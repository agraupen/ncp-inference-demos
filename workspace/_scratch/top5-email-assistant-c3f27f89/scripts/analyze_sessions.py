#!/usr/bin/env python3
"""Analyze Claude Code session JSONL files and extract structured data.

Reads session logs from ~/.claude/projects/<project-dir>/<session-id>.jsonl
and produces structured summaries with tool usage, file changes, git commits,
and conversation segments split by time gaps, branch changes, or cwd changes.

Usage:
    python3 analyze_sessions.py [OPTIONS]

    --project TEXT       Filter project dirs by substring
    --since INT          Hours to look back (default: 72)
    --session TEXT       Specific session ID
    --base PATH          Base projects dir (default: ~/.claude/projects)
    --gap-minutes INT    Topic split threshold (default: 10)
    --compact            Truncate messages to 500 chars
    --verbose            Print progress to stderr

Output: JSON array of session extractions to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

GAP_MINUTES_DEFAULT = 10
MAX_RESULT_PREVIEW = 500

GIT_COMMIT_RE = re.compile(r"\[(\S+)\s+([a-f0-9]{7,})\]\s+(.+)")

SKIP_TYPES = frozenset({"file-history-snapshot", "queue-operation", "last-prompt"})


@dataclass
class Message:
    role: str
    timestamp: str | None = None
    text: str | None = None
    tool: str | None = None
    input_summary: str | None = None
    result_preview: str | None = None
    file_path: str | None = None
    branch: str | None = None
    cwd: str | None = None

    def to_dict(self) -> dict:
        d: dict = {"role": self.role, "timestamp": self.timestamp}
        if self.text is not None:
            d["text"] = self.text
        if self.tool is not None:
            d["tool"] = self.tool
        if self.input_summary is not None:
            d["input_summary"] = self.input_summary
        if self.result_preview is not None:
            d["result_preview"] = self.result_preview
        return d


@dataclass
class Segment:
    segment_index: int
    time_range: list[str | None]
    git_branch: str | None
    files_touched: list[str]
    commands_run: list[str]
    tools_used: dict[str, int]
    messages: list[Message]

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def to_dict(self, compact: bool = False) -> dict:
        d = {
            "segment_index": self.segment_index,
            "time_range": self.time_range,
            "git_branch": self.git_branch,
            "files_touched": sorted(set(self.files_touched)),
            "commands_run": self.commands_run,
            "tools_used": dict(sorted(self.tools_used.items(), key=lambda x: -x[1])),
            "message_count": self.message_count,
        }
        if not compact:
            d["messages"] = [m.to_dict() for m in self.messages]
        return d


@dataclass
class SessionExtraction:
    session_id: str | None = None
    project_dir: str = ""
    cwd: str | None = None
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    duration_minutes: float | None = None
    git_branches: list[str] = field(default_factory=list)
    git_commits: list[dict] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    tools_summary: dict[str, int] = field(default_factory=dict)
    tool_call_total: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    segments: list[Segment] = field(default_factory=list)
    error: str | None = None

    def to_dict(self, compact: bool = False) -> dict:
        return {
            "session_id": self.session_id,
            "project_dir": self.project_dir,
            "cwd": self.cwd,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "duration_minutes": self.duration_minutes,
            "git_branches": self.git_branches,
            "git_commits": self.git_commits,
            "files_changed": self.files_changed,
            "tools_summary": dict(sorted(self.tools_summary.items(), key=lambda x: -x[1])),
            "tool_call_total": self.tool_call_total,
            "user_message_count": self.user_message_count,
            "assistant_message_count": self.assistant_message_count,
            "segments": [s.to_dict(compact=compact) for s in self.segments],
            "error": self.error,
        }


def _extract_text_from_content(content) -> str:
    """Extract text from a message content field (string or list of blocks)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return " ".join(parts).strip()
    return ""


def _make_tool_input_summary(tool_name: str, input_dict: dict) -> str:
    """Build a human-readable one-line summary of a tool invocation."""
    if tool_name in ("Edit", "Write", "Read"):
        fp = input_dict.get("file_path", "")
        return f"{tool_name} {fp}"
    if tool_name == "Bash":
        cmd = input_dict.get("command", "")
        if len(cmd) > 120:
            cmd = cmd[:117] + "..."
        return f"Bash: {cmd}"
    if tool_name in ("Grep", "Glob"):
        pattern = input_dict.get("pattern", "")
        path = input_dict.get("path", "")
        if path:
            return f"{tool_name} {pattern!r} in {path}"
        return f"{tool_name} {pattern!r}"
    if tool_name == "WebFetch":
        return f"WebFetch {input_dict.get('url', '')}"
    if tool_name == "WebSearch":
        return f"WebSearch {input_dict.get('query', '')}"
    if tool_name == "Skill":
        return f"Skill {input_dict.get('skill', '')}"
    # Generic fallback
    keys = list(input_dict.keys())[:3]
    return f"{tool_name}({', '.join(keys)})" if keys else tool_name


def _parse_timestamp(ts_str: str | None) -> datetime | None:
    """Parse an ISO8601 timestamp string to datetime."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class SessionExtractor:
    """Single-pass extractor for a Claude Code session JSONL file."""

    def __init__(self, session_path: Path, gap_minutes: int = GAP_MINUTES_DEFAULT, compact: bool = False):
        self.session_path = session_path
        self.gap_minutes = gap_minutes
        self.compact = compact

        # Accumulated state
        self._messages: list[Message] = []
        self._tools_summary: dict[str, int] = {}
        self._files_changed: set[str] = set()
        self._git_branches: set[str] = set()
        self._git_commits: list[dict] = []
        self._git_commit_hashes: set[str] = set()
        self._tool_use_id_map: dict[str, str] = {}  # tool_use_id -> tool_name
        self._first_ts: str | None = None
        self._last_ts: str | None = None
        self._session_id: str | None = None
        self._cwd: str | None = None
        self._current_branch: str | None = None
        self._current_cwd: str | None = None
        self._user_count = 0
        self._assistant_count = 0

    def extract(self) -> dict:
        """Parse the JSONL file and return the structured extraction dict."""
        try:
            with open(self.session_path) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self._parse_line(raw)
        except Exception as e:
            return SessionExtraction(
                session_id=self._session_id or self.session_path.stem,
                project_dir=self.session_path.parent.name,
                error=str(e),
            ).to_dict()

        segments = self._segment_messages()

        duration = None
        if self._first_ts and self._last_ts:
            t0 = _parse_timestamp(self._first_ts)
            t1 = _parse_timestamp(self._last_ts)
            if t0 and t1:
                duration = round((t1 - t0).total_seconds() / 60, 1)

        result = SessionExtraction(
            session_id=self._session_id or self.session_path.stem,
            project_dir=self.session_path.parent.name,
            cwd=self._cwd,
            first_timestamp=self._first_ts,
            last_timestamp=self._last_ts,
            duration_minutes=duration,
            git_branches=sorted(self._git_branches),
            git_commits=self._git_commits,
            files_changed=sorted(self._files_changed),
            tools_summary=self._tools_summary,
            tool_call_total=sum(self._tools_summary.values()),
            user_message_count=self._user_count,
            assistant_message_count=self._assistant_count,
            segments=segments,
        )
        return result.to_dict(compact=self.compact)

    def _parse_line(self, raw: dict) -> None:
        """Process a single JSONL record."""
        # Skip sidechain messages
        if raw.get("isSidechain"):
            return

        msg_type = raw.get("type")

        # Skip non-content types
        if msg_type in SKIP_TYPES:
            return

        # Track timestamps
        ts = raw.get("timestamp")
        if ts:
            if self._first_ts is None:
                self._first_ts = ts
            self._last_ts = ts

        # Track session ID
        if not self._session_id and raw.get("sessionId"):
            self._session_id = raw["sessionId"]

        # Track git branch
        branch = raw.get("gitBranch")
        if branch:
            self._git_branches.add(branch)
            self._current_branch = branch

        # Track cwd
        raw_cwd = raw.get("cwd")
        if raw_cwd:
            if self._cwd is None:
                self._cwd = raw_cwd
            self._current_cwd = raw_cwd

        message = raw.get("message")
        if not isinstance(message, dict):
            message = {}

        role = message.get("role")
        content = message.get("content")

        # User messages
        if msg_type == "user" and role == "user":
            self._user_count += 1
            # Extract text from user content
            user_text = self._extract_user_content(content, ts)
            if user_text is not None:
                text = user_text if not self.compact else user_text[:MAX_RESULT_PREVIEW]
                self._add_message(Message(role="user", timestamp=ts, text=text))

        # Assistant messages (type can be "assistant" or None with role "assistant")
        elif msg_type == "assistant" or (msg_type is None and role == "assistant"):
            self._assistant_count += 1
            self._process_assistant_content(content, ts)

        # Progress events
        elif msg_type == "progress":
            data = raw.get("data", {})
            if isinstance(data, dict) and data.get("type") == "bash_progress":
                full_output = data.get("fullOutput", "")
                if full_output:
                    self._scan_for_git_commits(full_output)

        # System events (turn_duration etc) — no extraction needed
        elif msg_type == "system":
            pass

    def _extract_user_content(self, content, ts: str | None) -> str | None:
        """Extract text from user message content, also processing tool_result blocks."""
        if isinstance(content, str):
            return content.strip() or None

        if not isinstance(content, list):
            return None

        text_parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")

            if block_type == "text":
                t = block.get("text", "").strip()
                if t:
                    text_parts.append(t)

            elif block_type == "tool_result":
                tool_use_id = block.get("tool_use_id", "")
                tool_name = self._tool_use_id_map.get(tool_use_id)
                is_error = block.get("is_error", False)

                # Extract result text
                result_content = block.get("content", "")
                if isinstance(result_content, str):
                    result_text = result_content
                elif isinstance(result_content, list):
                    rparts = []
                    for sub in result_content:
                        if isinstance(sub, dict):
                            if sub.get("type") == "text":
                                rparts.append(sub.get("text", ""))
                            elif sub.get("type") == "tool_reference":
                                rparts.append(f"[tool_ref: {sub.get('tool_name', '')}]")
                    result_text = " ".join(rparts)
                else:
                    result_text = ""

                # Save bash output for git commit scanning
                if tool_name == "Bash" and result_text:
                    self._scan_for_git_commits(result_text)

                preview = result_text[:MAX_RESULT_PREVIEW] if result_text else ""
                if is_error and preview:
                    preview = f"[ERROR] {preview}"

                self._add_message(Message(
                    role="tool_result",
                    timestamp=ts,
                    tool=tool_name,
                    result_preview=preview,
                ))

        return " ".join(text_parts).strip() or None

    def _process_assistant_content(self, content, ts: str | None) -> None:
        """Process assistant message content blocks for text and tool_use."""
        if not isinstance(content, list):
            text = _extract_text_from_content(content)
            if text:
                text = text if not self.compact else text[:MAX_RESULT_PREVIEW]
                self._add_message(Message(role="assistant", timestamp=ts, text=text))
            return

        # Collect text blocks separately from tool_use blocks
        text_parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")

            if block_type == "text":
                t = block.get("text", "").strip()
                if t:
                    text_parts.append(t)

            elif block_type == "tool_use":
                tool_name = block.get("name", "unknown")
                tool_use_id = block.get("id", "")
                inp = block.get("input", {})

                # Map tool_use_id -> tool_name for later result linking
                if tool_use_id:
                    self._tool_use_id_map[tool_use_id] = tool_name

                # Track tool usage
                self._tools_summary[tool_name] = self._tools_summary.get(tool_name, 0) + 1

                # Track files changed
                fp = None
                if tool_name in ("Edit", "Write") and isinstance(inp, dict):
                    fp = inp.get("file_path")
                    if fp:
                        self._files_changed.add(fp)

                # Build input summary
                summary = _make_tool_input_summary(tool_name, inp if isinstance(inp, dict) else {})

                self._add_message(Message(
                    role="tool_use",
                    timestamp=ts,
                    tool=tool_name,
                    input_summary=summary,
                    file_path=fp,
                ))

        # Add assistant text message if any
        if text_parts:
            combined = " ".join(text_parts)
            if self.compact:
                combined = combined[:MAX_RESULT_PREVIEW]
            self._add_message(Message(role="assistant", timestamp=ts, text=combined))

    def _add_message(self, msg: Message) -> None:
        """Append a message with its associated branch/cwd for segmenting."""
        msg.branch = self._current_branch
        msg.cwd = self._current_cwd
        self._messages.append(msg)

    def _segment_messages(self) -> list[Segment]:
        """Split messages into segments based on time gaps, branch changes, or cwd changes."""
        if not self._messages:
            return []

        # Pre-parse timestamps to avoid double-parsing during gap checks
        parsed_ts = [_parse_timestamp(m.timestamp) for m in self._messages]

        segments: list[Segment] = []
        current_start = 0

        for i in range(1, len(self._messages)):
            split = False
            prev_msg = self._messages[i - 1]
            curr_msg = self._messages[i]

            # Check time gap
            if parsed_ts[i - 1] and parsed_ts[i]:
                gap = (parsed_ts[i] - parsed_ts[i - 1]).total_seconds() / 60
                if gap > self.gap_minutes:
                    split = True

            # Check branch change
            if curr_msg.branch != prev_msg.branch:
                if curr_msg.branch is not None and prev_msg.branch is not None:
                    split = True

            # Check cwd change
            if curr_msg.cwd != prev_msg.cwd:
                if curr_msg.cwd is not None and prev_msg.cwd is not None:
                    split = True

            if split:
                segments.append(self._build_segment(len(segments), current_start, i))
                current_start = i

        # Final segment
        segments.append(self._build_segment(len(segments), current_start, len(self._messages)))
        return segments

    def _build_segment(self, index: int, start: int, end: int) -> Segment:
        """Build a Segment from a slice of messages."""
        msgs = self._messages[start:end]

        # Time range
        valid_ts = [m.timestamp for m in msgs if m.timestamp is not None]
        time_range = [valid_ts[0] if valid_ts else None, valid_ts[-1] if valid_ts else None]

        # Primary branch (most common non-None)
        branch_counts: dict[str, int] = {}
        for m in msgs:
            if m.branch is not None:
                branch_counts[m.branch] = branch_counts.get(m.branch, 0) + 1
        primary_branch = max(branch_counts, key=branch_counts.get) if branch_counts else None

        # Files touched, commands run, tools used
        files_touched: list[str] = []
        commands_run: list[str] = []
        tools_used: dict[str, int] = {}

        for m in msgs:
            if m.role == "tool_use" and m.tool:
                tools_used[m.tool] = tools_used.get(m.tool, 0) + 1
                if m.tool in ("Edit", "Write") and m.file_path:
                    files_touched.append(m.file_path)
                elif m.tool == "Bash" and m.input_summary:
                    if m.input_summary.startswith("Bash: "):
                        commands_run.append(m.input_summary[6:])

        return Segment(
            segment_index=index,
            time_range=time_range,
            git_branch=primary_branch,
            files_touched=files_touched,
            commands_run=commands_run,
            tools_used=tools_used,
            messages=msgs,
        )

    def _scan_for_git_commits(self, text: str) -> None:
        """Eagerly scan text for git commit patterns and deduplicate."""
        for match in GIT_COMMIT_RE.finditer(text):
            hash_val = match.group(2)
            if hash_val not in self._git_commit_hashes:
                self._git_commit_hashes.add(hash_val)
                self._git_commits.append({
                    "hash": hash_val,
                    "message": match.group(3).strip(),
                    "branch": match.group(1),
                })


def find_project_dirs(base: Path, project_filter: str | None = None) -> list[Path]:
    """Find Claude project directories, optionally filtering by substring."""
    dirs = []
    try:
        entries = list(base.iterdir())
    except PermissionError:
        return dirs
    for entry in entries:
        if not entry.is_dir():
            continue
        # Skip dotfile directories
        if entry.name.startswith("."):
            continue
        if project_filter and project_filter.lower() not in entry.name.lower():
            continue
        dirs.append(entry)
    return sorted(dirs)


def find_sessions(
    project_dir: Path,
    since: datetime | None = None,
    session_id: str | None = None,
) -> list[Path]:
    """Find session JSONL files, optionally filtered by time or ID."""
    sessions = []
    try:
        entries = list(project_dir.iterdir())
    except PermissionError:
        return sessions
    for f in entries:
        if not f.is_file() or f.suffix != ".jsonl":
            continue
        if session_id and session_id not in f.stem:
            continue
        mtime = f.stat().st_mtime
        if since:
            mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            if mtime_dt < since:
                continue
        sessions.append((mtime, f))
    return [f for _, f in sorted(sessions, key=lambda x: -x[0])]


def main():
    parser = argparse.ArgumentParser(description="Analyze Claude Code session JSONL files")
    parser.add_argument("--project", help="Filter project dirs by substring")
    parser.add_argument("--since", type=int, default=72, help="Hours to look back (default: 72)")
    parser.add_argument("--session", help="Specific session ID")
    parser.add_argument(
        "--base",
        default=str(Path("~/.claude/projects").expanduser()),
        help="Base projects dir (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--gap-minutes",
        type=int,
        default=GAP_MINUTES_DEFAULT,
        help=f"Topic split threshold in minutes (default: {GAP_MINUTES_DEFAULT})",
    )
    parser.add_argument("--compact", action="store_true", help="Truncate messages to 500 chars")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    base = Path(args.base)
    if not base.exists():
        print(json.dumps({"error": f"Base dir not found: {base}"}))
        sys.exit(1)

    since = datetime.now(timezone.utc) - timedelta(hours=args.since)

    project_dirs = find_project_dirs(base, args.project)
    if not project_dirs:
        print(json.dumps({"error": "No matching project directories found"}))
        sys.exit(1)

    if args.verbose:
        print(f"Found {len(project_dirs)} project dir(s)", file=sys.stderr)

    results = []
    for pd in project_dirs:
        sessions = find_sessions(pd, since=since, session_id=args.session)
        if args.verbose and sessions:
            print(f"  {pd.name}: {len(sessions)} session(s)", file=sys.stderr)

        for sp in sessions:
            if args.verbose:
                print(f"    Processing {sp.name}...", file=sys.stderr)
            try:
                extractor = SessionExtractor(sp, gap_minutes=args.gap_minutes, compact=args.compact)
                result = extractor.extract()
                results.append(result)
                if args.verbose:
                    msg_count = result.get("user_message_count", 0) + result.get("assistant_message_count", 0)
                    seg_count = len(result.get("segments", []))
                    print(
                        f"      -> {msg_count} messages, {seg_count} segment(s), "
                        f"{result.get('tool_call_total', 0)} tool calls",
                        file=sys.stderr,
                    )
            except Exception as e:
                results.append({
                    "session_id": sp.stem,
                    "project_dir": pd.name,
                    "error": str(e),
                })

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
