"""
app.py - High Performance Local Web Server for Fund Flow Dashboard
Serves the responsive dashboard UI and provides APIs for live data refresh.
"""

import http.server
import socketserver
import os
import json
import threading
import webbrowser
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fetcher import get_fund_flow_data, fetch_live_market_data

PORT = 8088
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Global state for background fetch progress
fetch_status = {
    "is_fetching": False,
    "progress": 0,
    "total": 100,
    "message": "Ready",
    "last_updated": None
}


class FundFlowRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = get_fund_flow_data(force_refresh=False)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(fetch_status, ensure_ascii=False).encode("utf-8"))
            return

        # Fallback to static file server
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/refresh":
            global fetch_status
            if fetch_status["is_fetching"]:
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Fetch already in progress"}).encode("utf-8"))
                return

            def background_task():
                global fetch_status
                fetch_status["is_fetching"] = True
                fetch_status["progress"] = 0
                fetch_status["message"] = "市場データをダウンロード中..."
                try:
                    def on_progress(current, total, msg):
                        fetch_status["progress"] = current
                        fetch_status["total"] = total
                        fetch_status["message"] = msg

                    fetch_live_market_data(progress_callback=on_progress)
                    fetch_status["message"] = "更新完了"
                except Exception as e:
                    fetch_status["message"] = f"エラー: {str(e)}"
                finally:
                    fetch_status["is_fetching"] = False

            t = threading.Thread(target=background_task, daemon=True)
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Background fetch started"}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_server(port=PORT, auto_open=True):
    for p in range(port, port + 10):
        try:
            with ThreadedHTTPServer(("", p), FundFlowRequestHandler) as httpd:
                print("=" * 60)
                print(f"[*] US Stock Fund Flow Dashboard started successfully!")
                print(f"[*] Open in Browser: http://localhost:{p}")
                print("=" * 60)
                if auto_open:
                    threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{p}")).start()
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e) or getattr(e, 'errno', None) == 10048:
                continue
            else:
                raise e


if __name__ == "__main__":
    auto = "--no-browser" not in sys.argv
    run_server(auto_open=auto)

