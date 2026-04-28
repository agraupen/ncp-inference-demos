#!/usr/bin/env bash
# ============================================================================
# NCP Inference RA - Preflight Validation
# ============================================================================
# Checks that all NVIDIA software components are properly installed and
# configured before running any demo. Call with the demo number to validate
# only the components needed for that specific demo.
#
# Usage:
#   bash shared/preflight-check.sh          # Check everything
#   bash shared/preflight-check.sh 1        # Check only Demo 1 requirements
#   bash shared/preflight-check.sh --fix    # Check + attempt to fix issues
# ============================================================================

set -euo pipefail

DEMO="${1:-all}"
FIX_MODE=false
if [ "${DEMO}" = "--fix" ] || [ "${2:-}" = "--fix" ]; then
    FIX_MODE=true
    if [ "${DEMO}" = "--fix" ]; then DEMO="all"; fi
fi

PASS=0
FAIL=0
WARN=0
FIXES=0

# ---------- Helpers ----------
check_pass() { echo "  [PASS] $1"; ((PASS++)); }
check_fail() { echo "  [FAIL] $1"; ((FAIL++)); }
check_warn() { echo "  [WARN] $1"; ((WARN++)); }
check_fix()  { echo "  [FIX]  $1"; ((FIXES++)); }

try_fix() {
    local description="$1"
    local fix_cmd="$2"
    if [ "${FIX_MODE}" = true ]; then
        echo "  [FIX]  Attempting: ${description}..."
        if eval "${fix_cmd}" &>/dev/null; then
            check_fix "${description} - fixed!"
            return 0
        else
            check_fail "${description} - auto-fix failed. Manual intervention needed."
            return 1
        fi
    else
        echo "         Fix: ${fix_cmd}"
        return 1
    fi
}

# ============================================================================
# LAYER 1: GPU Hardware & Drivers
# ============================================================================
check_gpu_drivers() {
    echo ""
    echo "=== GPU Hardware & Drivers ==="

    # nvidia-smi
    if command -v nvidia-smi &>/dev/null; then
        check_pass "nvidia-smi found"
    else
        check_fail "nvidia-smi not found - NVIDIA drivers not installed"
        try_fix "Install NVIDIA drivers" "sudo apt-get update && sudo apt-get install -y nvidia-driver-550"
        return
    fi

    # Driver version
    local driver_ver
    driver_ver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1 | tr -d ' ')
    if [ -n "${driver_ver}" ]; then
        # Check minimum driver version (550+ recommended for latest features)
        local major
        major=$(echo "${driver_ver}" | cut -d. -f1)
        if [ "${major}" -ge 535 ]; then
            check_pass "NVIDIA driver version: ${driver_ver} (>= 535)"
        else
            check_warn "NVIDIA driver version: ${driver_ver} (recommend >= 535 for full TensorRT-LLM support)"
        fi
    else
        check_fail "Could not query NVIDIA driver version"
    fi

    # GPU detected
    local gpu_count
    gpu_count=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1 | tr -d ' ')
    if [ "${gpu_count}" -ge 1 ]; then
        check_pass "GPU(s) detected: ${gpu_count}"
        nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader | while read -r line; do
            echo "         GPU: ${line}"
        done
    else
        check_fail "No GPUs detected"
    fi

    # GPU memory check
    local vram_mb
    vram_mb=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | tr -d ' ')
    if [ "${vram_mb}" -ge 40000 ]; then
        check_pass "GPU VRAM: ${vram_mb} MB (sufficient for all demos)"
    elif [ "${vram_mb}" -ge 20000 ]; then
        check_warn "GPU VRAM: ${vram_mb} MB (OK for Demos 1-3, 5; may be tight for 4, 6)"
    elif [ "${vram_mb}" -ge 14000 ]; then
        check_warn "GPU VRAM: ${vram_mb} MB (OK for Demos 1, 5; use small models for 3)"
    else
        check_warn "GPU VRAM: ${vram_mb} MB (limited — Demo 1 and 5 only)"
    fi
}

# ============================================================================
# LAYER 2: CUDA Toolkit
# ============================================================================
check_cuda() {
    echo ""
    echo "=== CUDA Toolkit ==="

    # nvcc
    if command -v nvcc &>/dev/null; then
        local cuda_ver
        cuda_ver=$(nvcc --version 2>/dev/null | grep "release" | sed 's/.*release //' | sed 's/,.*//')
        check_pass "CUDA toolkit: ${cuda_ver}"

        # Check minimum CUDA version
        local cuda_major
        cuda_major=$(echo "${cuda_ver}" | cut -d. -f1)
        if [ "${cuda_major}" -ge 12 ]; then
            check_pass "CUDA version >= 12 (required for TensorRT-LLM)"
        else
            check_warn "CUDA ${cuda_ver} detected. CUDA 12+ recommended for TensorRT-LLM / Dynamo."
        fi
    else
        check_warn "nvcc not found in PATH (may be inside containers only, which is OK for Docker-based demos)"
    fi

    # CUDA libraries
    if ldconfig -p 2>/dev/null | grep -q libcuda.so; then
        check_pass "libcuda.so found in library path"
    else
        check_warn "libcuda.so not found via ldconfig (may still work if drivers are loaded)"
    fi
}

# ============================================================================
# LAYER 3: Docker & NVIDIA Container Toolkit
# ============================================================================
check_docker() {
    echo ""
    echo "=== Docker & NVIDIA Container Toolkit ==="

    # Docker installed
    if command -v docker &>/dev/null; then
        local docker_ver
        docker_ver=$(docker --version 2>/dev/null | sed 's/Docker version //' | cut -d, -f1)
        check_pass "Docker installed: ${docker_ver}"
    else
        check_fail "Docker not installed"
        try_fix "Install Docker" "curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker \$(whoami)"
        return
    fi

    # Docker daemon running
    if docker info &>/dev/null; then
        check_pass "Docker daemon is running"
    else
        check_fail "Docker daemon is not running or permission denied"
        try_fix "Start Docker daemon" "sudo systemctl start docker"
        # Check if it's a permission issue
        if ! groups | grep -q docker; then
            echo "         You may need: sudo usermod -aG docker \$(whoami) && newgrp docker"
        fi
        return
    fi

    # NVIDIA Container Toolkit
    if docker info 2>/dev/null | grep -qi "nvidia"; then
        check_pass "NVIDIA Container Toolkit detected in Docker runtime"
    elif [ -f /etc/nvidia-container-runtime/config.toml ] || [ -f /usr/bin/nvidia-container-runtime ]; then
        check_pass "NVIDIA Container Runtime files found"
    else
        check_fail "NVIDIA Container Toolkit not detected"
        try_fix "Install NVIDIA Container Toolkit" \
            "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list && sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit && sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker"
    fi

    # GPU passthrough test
    echo "  [TEST] Testing Docker GPU passthrough..."
    if docker run --rm --gpus all nvidia/cuda:12.6.3-base-ubuntu24.04 nvidia-smi &>/dev/null; then
        check_pass "Docker GPU passthrough working (--gpus all)"
    else
        check_fail "Docker GPU passthrough FAILED"
        echo "         This means containers cannot access the GPU."
        echo "         Common fixes:"
        echo "           1. sudo nvidia-ctk runtime configure --runtime=docker"
        echo "           2. sudo systemctl restart docker"
        echo "           3. Reinstall nvidia-container-toolkit"
    fi
}

# ============================================================================
# LAYER 4: NGC Authentication
# ============================================================================
check_ngc() {
    echo ""
    echo "=== NGC Container Registry ==="

    # NGC_API_KEY set
    if [ -n "${NGC_API_KEY:-}" ]; then
        check_pass "NGC_API_KEY environment variable is set"

        # Test NGC login
        if echo "${NGC_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin &>/dev/null; then
            check_pass "NGC authentication successful (nvcr.io)"
        else
            check_fail "NGC authentication failed - key may be invalid or expired"
            echo "         Get a new key at: https://org.ngc.nvidia.com/setup/api-key"
        fi
    else
        check_warn "NGC_API_KEY not set - required for Demos 2, 3, 4, 6"
        echo "         Set with: export NGC_API_KEY=<your-key>"
        echo "         Get a key at: https://org.ngc.nvidia.com/setup/api-key"
    fi

    # NGC CLI (optional but useful)
    if command -v ngc &>/dev/null; then
        check_pass "NGC CLI installed"
    else
        check_warn "NGC CLI not installed (optional, only needed for Demo 2 Riva download)"
        echo "         Install: pip install ngc-cli"
    fi
}

# ============================================================================
# LAYER 5: HuggingFace Token
# ============================================================================
check_huggingface() {
    echo ""
    echo "=== HuggingFace Access ==="

    if [ -n "${HF_TOKEN:-}" ]; then
        check_pass "HF_TOKEN environment variable is set"

        # Validate token
        local hf_status
        hf_status=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer ${HF_TOKEN}" \
            https://huggingface.co/api/whoami-v2 2>/dev/null || echo "000")
        if [ "${hf_status}" = "200" ]; then
            check_pass "HuggingFace token is valid"
        elif [ "${hf_status}" = "401" ]; then
            check_fail "HuggingFace token is invalid or expired"
            echo "         Get a new token at: https://huggingface.co/settings/tokens"
        else
            check_warn "Could not validate HuggingFace token (HTTP ${hf_status})"
        fi
    else
        check_warn "HF_TOKEN not set - required for gated models (Llama 3, etc.)"
        echo "         Set with: export HF_TOKEN=<your-token>"
    fi
}

# ============================================================================
# LAYER 6: Python & Key Packages
# ============================================================================
check_python() {
    echo ""
    echo "=== Python Environment ==="

    # Python 3
    if command -v python3 &>/dev/null; then
        local py_ver
        py_ver=$(python3 --version 2>/dev/null | sed 's/Python //')
        check_pass "Python 3 installed: ${py_ver}"

        local py_major py_minor
        py_major=$(echo "${py_ver}" | cut -d. -f1)
        py_minor=$(echo "${py_ver}" | cut -d. -f2)
        if [ "${py_minor}" -ge 10 ]; then
            check_pass "Python version >= 3.10 (required for Dynamo/AIPerf)"
        else
            check_warn "Python ${py_ver} - recommend 3.10+ for full compatibility"
        fi
    else
        check_fail "Python 3 not installed"
        try_fix "Install Python 3" "sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
        return
    fi

    # pip
    if command -v pip3 &>/dev/null || python3 -m pip --version &>/dev/null; then
        check_pass "pip installed"
    else
        check_fail "pip not installed"
        try_fix "Install pip" "sudo apt-get install -y python3-pip"
    fi

    # Key packages
    for pkg in requests numpy; do
        if python3 -c "import ${pkg}" &>/dev/null; then
            check_pass "Python package '${pkg}' available"
        else
            check_warn "Python package '${pkg}' not installed"
            if [ "${FIX_MODE}" = true ]; then
                try_fix "Install ${pkg}" "pip3 install -q ${pkg}"
            fi
        fi
    done

    # AIPerf
    if command -v aiperf &>/dev/null || python3 -c "import aiperf" &>/dev/null; then
        check_pass "AIPerf installed"
    else
        check_warn "AIPerf not installed (needed for Demos 3, 4, 6)"
        echo "         Install: pip install aiperf"
    fi

    # AIConfigurator
    if command -v aiconfigurator &>/dev/null || python3 -c "import aiconfigurator" &>/dev/null; then
        check_pass "AIConfigurator installed"
    else
        check_warn "AIConfigurator not installed (needed for Demos 4, 6)"
        echo "         Install: pip install aiconfigurator"
    fi
}

# ============================================================================
# LAYER 7: Container Images (check if already pulled)
# ============================================================================
check_container_images() {
    echo ""
    echo "=== Container Images ==="

    local images_needed=()

    case "${DEMO}" in
        1) images_needed=("nvcr.io/nvidia/tritonserver:25.03-py3") ;;
        2) images_needed=("nvcr.io/nvidia/riva/riva-speech:2.19.0") ;;
        3) images_needed=("nvcr.io/nvidia/ai-dynamo/sglang-runtime:1.0.1") ;;
        4) images_needed=("nvcr.io/nvidia/ai-dynamo/sglang-runtime:1.0.1") ;;
        5) images_needed=("nvcr.io/nvidia/tritonserver:25.03-py3") ;;
        6) images_needed=("nvcr.io/nvidia/ai-dynamo/sglang-runtime:1.0.1" "nvcr.io/nvidia/tritonserver:25.03-py3") ;;
        all) images_needed=(
                "nvcr.io/nvidia/tritonserver:25.03-py3"
                "nvcr.io/nvidia/ai-dynamo/sglang-runtime:1.0.1"
                "nvcr.io/nvidia/riva/riva-speech:2.19.0"
             ) ;;
    esac

    for img in "${images_needed[@]}"; do
        if docker image inspect "${img}" &>/dev/null; then
            check_pass "Image cached: ${img}"
        else
            check_warn "Image not cached: ${img}"
            echo "         Will be pulled on first run (can be large: 5-20 GB)"
            echo "         Pre-pull: docker pull ${img}"
        fi
    done
}

# ============================================================================
# LAYER 8: Disk Space
# ============================================================================
check_disk() {
    echo ""
    echo "=== Disk Space ==="

    local avail_gb
    avail_gb=$(df -BG / 2>/dev/null | awk 'NR==2{print $4}' | tr -d 'G')

    if [ -n "${avail_gb}" ]; then
        if [ "${avail_gb}" -ge 100 ]; then
            check_pass "Disk space: ${avail_gb} GB available (sufficient for all demos)"
        elif [ "${avail_gb}" -ge 50 ]; then
            check_warn "Disk space: ${avail_gb} GB available (tight for multiple large containers)"
            echo "         Recommend 100+ GB for running all demos"
        else
            check_fail "Disk space: ${avail_gb} GB available (insufficient)"
            echo "         Need at least 50 GB. Container images are 5-20 GB each."
            echo "         Clean up: docker system prune -a"
        fi
    fi
}

# ============================================================================
# LAYER 9: Network Connectivity
# ============================================================================
check_network() {
    echo ""
    echo "=== Network Connectivity ==="

    # NGC registry
    if curl -s --max-time 5 https://nvcr.io/v2/ &>/dev/null; then
        check_pass "Can reach NGC container registry (nvcr.io)"
    else
        check_fail "Cannot reach NGC container registry"
        echo "         Check firewall/proxy settings"
    fi

    # HuggingFace
    if curl -s --max-time 5 https://huggingface.co &>/dev/null; then
        check_pass "Can reach HuggingFace (huggingface.co)"
    else
        check_warn "Cannot reach HuggingFace - gated model downloads will fail"
    fi

    # PyPI
    if curl -s --max-time 5 https://pypi.org &>/dev/null; then
        check_pass "Can reach PyPI (pypi.org)"
    else
        check_warn "Cannot reach PyPI - pip installs will fail"
    fi
}

# ============================================================================
# LAYER 10: Kubernetes (Demos 5, 6 only)
# ============================================================================
check_kubernetes() {
    echo ""
    echo "=== Kubernetes (Demos 5, 6) ==="

    if command -v kubectl &>/dev/null; then
        check_pass "kubectl installed"
        if kubectl cluster-info &>/dev/null 2>&1; then
            check_pass "Kubernetes cluster is accessible"

            # GPU resources
            local gpu_count
            gpu_count=$(kubectl get nodes -o json 2>/dev/null | \
                python3 -c "import sys,json; n=json.load(sys.stdin); print(sum(int(node.get('status',{}).get('capacity',{}).get('nvidia.com/gpu','0')) for node in n.get('items',[])))" 2>/dev/null || echo "0")
            if [ "${gpu_count}" -gt 0 ]; then
                check_pass "GPUs visible in Kubernetes: ${gpu_count}"
            else
                check_warn "No GPUs visible in Kubernetes (GPU Operator may not be installed)"
            fi
        else
            check_warn "No Kubernetes cluster running (Demo 5 will install K3s)"
        fi
    else
        check_warn "kubectl not installed (Demo 5 will install K3s + kubectl)"
    fi

    if command -v helm &>/dev/null; then
        check_pass "Helm installed: $(helm version --short 2>/dev/null)"
    else
        check_warn "Helm not installed (Demo 5 will install it)"
    fi
}

# ============================================================================
# Run checks based on demo selection
# ============================================================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   NCP Inference RA - Preflight Validation            ║"
echo "║   Checking: Demo ${DEMO}  |  Fix mode: ${FIX_MODE}            ║"
echo "╚══════════════════════════════════════════════════════╝"

# Always check these
check_gpu_drivers
check_cuda
check_docker
check_disk
check_network

# Demo-specific checks
case "${DEMO}" in
    1)
        check_python
        check_container_images
        ;;
    2)
        check_ngc
        check_python
        check_container_images
        ;;
    3)
        check_ngc
        check_huggingface
        check_python
        check_container_images
        ;;
    4)
        check_ngc
        check_huggingface
        check_python
        check_container_images
        ;;
    5)
        check_python
        check_kubernetes
        check_container_images
        ;;
    6)
        check_ngc
        check_huggingface
        check_python
        check_kubernetes
        check_container_images
        ;;
    all)
        check_ngc
        check_huggingface
        check_python
        check_kubernetes
        check_container_images
        ;;
esac

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "============================================"
echo " Preflight Summary"
echo "============================================"
echo "  PASS: ${PASS}"
echo "  WARN: ${WARN}"
echo "  FAIL: ${FAIL}"
if [ "${FIX_MODE}" = true ]; then
    echo "  FIXED: ${FIXES}"
fi
echo ""

if [ "${FAIL}" -gt 0 ]; then
    echo "  RESULT: SOME CHECKS FAILED"
    echo "  Run with --fix to attempt auto-repair:"
    echo "    bash shared/preflight-check.sh ${DEMO} --fix"
    echo ""
    exit 1
elif [ "${WARN}" -gt 0 ]; then
    echo "  RESULT: READY (with warnings)"
    echo "  Demos should work, but review warnings above."
    echo ""
    exit 0
else
    echo "  RESULT: ALL CHECKS PASSED"
    echo "  Ready to run Demo ${DEMO}!"
    echo ""
    exit 0
fi
