from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from services import InMemoryPlatformService
from scaffold import PlatformExtension


def render_extension_section(extension: PlatformExtension) -> str:
    entry_rows = "".join(
        f"<li><a href='{escape(str(entry.url))}'>{escape(entry.title)}</a><p>{escape(entry.summary)}</p></li>"
        for entry in extension.entries
    )
    return f"<section id='{escape(extension.slug)}'><h2>{escape(extension.label)}</h2><ul>{entry_rows}</ul></section>"


def render_html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>{escape(title)} | News Intelligence Platform</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 2rem; }}
        h2 {{ margin-top: 2rem; }}
        a {{ color: black; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        ul {{ padding-left: 1.2rem; }}
        section {{ margin-bottom: 3rem; }}
        footer {{ font-size: 0.85rem; margin-top: 3rem; opacity: 0.7; }}
    </style>
</head>
<body>
{body}
<footer>© 2026 News Intelligence Platform</footer>
</body>
</html>"""


class PortalHandler(BaseHTTPRequestHandler):
    def __init__(self, service: InMemoryPlatformService, *args: object, **kwargs: object) -> None:
        self.service = service
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/home"}:
            self.show_home_page()
        elif path.startswith("/extensions/"):
            self.show_extension_page(path.removeprefix("/extensions/"))
        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.show_not_found()

    def show_home_page(self) -> None:
        sections = "".join(render_extension_section(extension) for extension in self.service.extensions)
        navigation = "".join(
            f"<li><a href='/extensions/{escape(extension.slug)}'>{escape(extension.label)}</a></li>"
            for extension in self.service.extensions
        )
        body = f"""
<header><h1>News Intelligence Platform</h1></header>
<nav><ul>{navigation}</ul></nav>
{sections}
"""
        html_content = render_html_page("Home", body)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def show_extension_page(self, slug: str) -> None:
        try:
            extension = self.service.get_extension(slug)
        except KeyError:
            self.show_not_found()
            return
        html_content = render_html_page(extension.label, render_extension_section(extension))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def show_not_found(self) -> None:
        html_content = render_html_page("Not Found", f"<main><h1>404</h1><p>The page '{urlparse(self.path).path}' does not exist.</p></main>")
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, message: str, *args: object) -> None:
        pass
