"""Serve the last captured NCP RD DC dashboard when its live app is unavailable."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "_dashboard_5175.html"


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/health", "/healthz"}:
            body = b'{"status":"snapshot","source":"_dashboard_5175.html"}'
            content_type = "application/json; charset=utf-8"
            status = 200
        elif self.path == "/" and SNAPSHOT.exists():
            body = SNAPSHOT.read_bytes()
            content_type = "text/html; charset=utf-8"
            status = 200
        else:
            body = b"Not found"
            content_type = "text/plain; charset=utf-8"
            status = 404

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    if not SNAPSHOT.exists():
        raise SystemExit(f"Dashboard snapshot not found: {SNAPSHOT}")
    ThreadingHTTPServer(("127.0.0.1", 5175), DashboardHandler).serve_forever()
