import argparse
import webbrowser

import uvicorn

from core.config import settings


def run_web(open_browser: bool = True, host: str | None = None, port: int | None = None) -> None:
    host = host or settings.host
    port = port or settings.port
    url = f"http://{host}:{port}"
    if open_browser:
        webbrowser.open(url)
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,
    )


def run_desktop() -> None:
    from app.desktop import main

    main()


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube MP3 Downloader")
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Launch the PySide6 desktop app instead of the web UI",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the browser automatically (web mode only)",
    )
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    args = parser.parse_args()

    if args.desktop:
        run_desktop()
    else:
        run_web(open_browser=not args.no_browser, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
