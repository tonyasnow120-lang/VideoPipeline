"""Desktop launcher for FacelessAI.

Starts the FastAPI server in-process on a background thread and opens the
dashboard in a native desktop window via pywebview. Double-click the bundled
``FacelessAI.bat`` (Windows) to run it.
"""
import socket
import threading
import time

import uvicorn

from main import app

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def _wait_for_server(timeout: float = 30.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if _port_open(HOST, PORT):
            return True
        time.sleep(0.25)
    return False


class _ServerThread:
    """Runs uvicorn in a daemon thread so closing the window exits cleanly."""

    def __init__(self):
        config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def start(self):
        self.thread.start()


def main():
    import webview  # imported lazily so the rest is testable without a display

    # If a server is already listening (e.g. launched separately), reuse it.
    if not _port_open(HOST, PORT):
        _ServerThread().start()
        if not _wait_for_server():
            raise RuntimeError(f"FacelessAI server did not start at {URL}")

    webview.create_window(
        "FacelessAI",
        URL,
        width=1200,
        height=820,
        min_size=(900, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
