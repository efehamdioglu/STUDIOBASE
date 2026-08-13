"""STUDIOBASE masaüstü uygulaması başlatıcısı.

Streamlit sunucusunu arka planda başlatır ve arayüzü tarayıcı sekmesi/adres
çubuğu olmadan, gerçek bir masaüstü penceresi gibi (pywebview ile) açar.
Pencere kapatıldığında Streamlit sunucusu da otomatik olarak sonlandırılır.
"""

import socket
import subprocess
import sys
import time
from pathlib import Path

import webview

APP_DIR = Path(__file__).parent
PORT = 8501
URL = f"http://localhost:{PORT}"


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("localhost", port)) == 0


def _start_streamlit() -> subprocess.Popen:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_DIR / "app.py"),
            "--server.headless",
            "true",
            "--server.port",
            str(PORT),
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd=str(APP_DIR),
    )


def main() -> None:
    process = _start_streamlit()
    try:
        for _ in range(100):  # ~20 saniyeye kadar bekle
            if _port_open(PORT):
                break
            time.sleep(0.2)

        webview.create_window(
            "STUDIOBASE — Multi-Agent Music Engine",
            URL,
            width=460,
            height=880,
            resizable=True,
            background_color="#0d0d0e",
        )
        webview.start()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()
