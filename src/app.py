from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from auth import AccountManager
from services import InMemoryPlatformService
from scaffold import PlatformExtension


def render_extension_section(extension: PlatformExtension) -> str:
    entry_rows = "".join(
        f"<li><a href='{escape(str(entry.url))}'>{escape(entry.title)}</a><p>{escape(entry.summary)}</p></li>"
        for entry in extension.entries
    )
    return f"<section id='{escape(extension.slug)}'><h2>{escape(extension.label)}</h2><ul>{entry_rows}</ul></section>"


def render_login_form(message: str | None = None) -> str:
    notice = f"<p>{escape(message)}</p>" if message else ""
    return f"""<main><h1>Sign In</h1>{notice}
<form method='post' action='/login'>
<label for='email'>Email</label>
<input id='email' name='email' type='email' required>
<label for='password'>Password</label>
<input id='password' name='password' type='password' required>
<button type='submit'>Sign In</button>
</form></main>"""


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
        ul {{ padding-left: 1.2rem; }}
    </style>
</head>
<body>
{body}
<footer>© 2026 News Intelligence Platform</footer>
</body>
</html>"""


class PortalHandler(BaseHTTPRequestHandler):
    def __init__(
        self,
        service: InMemoryPlatformService,
        account_manager: AccountManager,
        *args: object,
        **kwargs: object,
    ) -> None:
        self.service = service
        self.account_manager = account_manager
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/home"}:
            self.show_home_page()
        elif path.startswith("/extensions/"):
            self.show_extension_page(path.removeprefix("/extensions/"))
        elif path.startswith("/category/"):
            self.show_category_page(path.removeprefix("/category/"))
        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif path == "/login":
            self.show_login_page()
        else:
            self.show_not_found()

    def do_POST(self) -> None:
        if urlparse(self.path).path == "/login":
            self.handle_login()
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

    def show_category_page(self, slug: str) -> None:
        try:
            category = self.service.get_category(slug)
        except KeyError:
            self.show_not_found()
            return
        articles = self.service.list_articles(category)
        article_rows = "".join(
            f"<li><strong>{escape(article.title)}</strong><p>{escape(article.summary)}</p></li>"
            for article in articles
        )
        html_content = render_html_page(
            str(category),
            f"<main><h1>{escape(str(category))}</h1><ul>{article_rows}</ul></main>",
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def show_not_found(self) -> None:
        path = urlparse(self.path).path
        html_content = render_html_page("Not Found", f"<main><h1>404</h1><p>{escape(path)} does not exist.</p></main>")
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def show_login_page(self, message: str | None = None, status: int = 200) -> None:
        html_content = render_html_page("Sign In", render_login_form(message))
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def handle_login(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        submitted = parse_qs(body.decode("utf-8"))
        email = submitted.get("email", [""])[0]
        password = submitted.get("password", [""])[0]
        if self.account_manager.authenticate(email, password) is None:
            self.show_login_page("Invalid credentials.", status=401)
            return
        html_content = render_html_page(
            "Signed In",
            "<main><h1>Welcome back</h1><p>You are signed in to the platform.</p></main>",
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, message: str, *args: object) -> None:
        pass
