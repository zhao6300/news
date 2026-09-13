from __future__ import annotations

from html import escape
from collections.abc import Sequence
from json import dumps
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlencode, urlparse

from auth import AccountManager
from connectors import IngestionReport
from services import InMemoryPlatformService
from sessions import SessionManager
from searchers import SearchEngine
from scaffold import PlatformExtension
from scaffold import Article
from scaffold import CategoryGroup
from storage import Page


def render_extension_section(extension: PlatformExtension) -> str:
    entry_rows = "".join(
        f"""
        <article class='article-card'>
            <a href='/article/{entry.id}'><strong>{escape(entry.title)}</strong></a>
            <p>{escape(entry.summary)}</p>
            <span class='meta'>{escape(entry.source)} · {escape(category_label(entry.category_id))}</span>
        </article>
        """
        for entry in extension.entries
    )
    return f"""
    <section id='{escape(extension.slug)}'>
        <h2>{escape(extension.label)}</h2>
        <div class='article-list'>{entry_rows}</div>
    </section>
    """


def category_label(category: CategoryGroup) -> str:
    return category.name.replace("_", " ").title()


def render_article_items(articles: Sequence[Article]) -> str:
    return "".join(
        f"""
        <article class='article-card'>
            <a href='/article/{article.id}'><strong>{escape(article.title)}</strong></a>
            <p>{escape(article.summary)}</p>
            <span class='meta'>{escape(article.source)} · {escape(category_label(article.category_id))}</span>
        </article>
        """
        for article in articles
    )


def render_login_form(message: str | None = None) -> str:
    notice = f"<p>{escape(message)}</p>" if message else ""
    return f"""<div class='login-panel'><h1>Sign In</h1>{notice}
<form method='post' action='/login'>
<label for='email'>Email</label>
<input id='email' name='email' type='email' required>
<label for='password'>Password</label>
<input id='password' name='password' type='password' required>
<button type='submit'>Sign In</button>
</form></div>"""


def render_navigation() -> str:
    links = [f"<a href='/'>Home</a>"]
    links.extend(f"<a href='/category/{category.value}'>{category_label(category)}</a>" for category in CategoryGroup)
    return f"<div class='category-nav'>{''.join(links)}</div>"


def render_search_form(query: str = "") -> str:
    return f"""
    <form class='search-form' method='get' action='/search'>
        <label for='q'>Search</label>
        <input id='q' name='q' type='search' value='{escape(query)}' placeholder='News, technology, models, reviews...' required>
        <button type='submit'>Search</button>
    </form>
    """


def render_search_filters(query: str, selected_category: CategoryGroup | None = None) -> str:
    links = [
        f"<a href='{escape(_search_url(query))}'"
        + (f" aria-current='page'" if selected_category is None else "")
        + ">All</a>"
    ]
    links.extend(
        f"<a href='{escape(_search_url(query, category))}'"
        + (f" aria-current='page'" if selected_category == category else "")
        + f">{category_label(category)}</a>"
        for category in CategoryGroup
    )
    return f"<div class='filter-list'>{''.join(links)}</div>"


def _search_url(query: str, category: CategoryGroup | None = None) -> str:
    parameters = {"q": query}
    if category is not None:
        parameters["category"] = category.value
    return f"/search?{urlencode(parameters)}"


def render_html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang='en'>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{escape(title)} | News Intelligence Platform</title>
    <style>
        :root {{ --surface: white; --edge: #dfdfd9; --muted: #64696a; --accent: #0b5f4e; }}
        * {{ box-sizing: border-box; }}
        body {{ background: #f6f6f3; color: #211f1e; font-family: Inter, system-ui, sans-serif; line-height: 1.6; margin: 0; padding: 0; }}
        .layout {{ max-width: 1060px; margin: 0 auto; padding: 0 1.1rem; }}
        header.site-header {{ background: #211f1e; color: #fff; padding: 1.1rem 0; }}
        .site-header a {{ color: #fff; text-decoration: none; }}
        .site-title {{ font-size: 1.4rem; font-weight: 700; text-decoration: none; }}
        .search-form {{ display: grid; gap: .45rem; margin: 1.2rem 0; }}
        .search-form label {{ position: absolute; clip: rect(0 0 0 0); clip-path: inset(50%); width: 1px; height: 1px; overflow: hidden; }}
        .search-form input {{ border: 1px solid var(--edge); border-radius: .35rem; font: inherit; padding: .6rem .8rem; }}
        .search-form button {{ background: var(--accent); border: 0; border-radius: .35rem; color: #fff; cursor: pointer; font: inherit; padding: .6rem 1rem; }}
        main.page {{ padding: 1.8rem 0 2.4rem; }}
        h1 {{ font-size: 1.7rem; line-height: 1.2; margin: .2rem 0 .3rem; }}
        h2 {{ margin: 1.5rem 0 .8rem; }}
        .page-meta {{ color: var(--muted); font-size: .95rem; margin: 0; }}
        .category-nav {{ display: grid; gap: .65rem; grid-template-columns: repeat(auto-fill, minmax(8rem, 1fr)); margin-top: 1.2rem; }}
        .category-nav a {{ background: rgba(255,255,255,.12); border-radius: 99rem; color: #fff; font-size: .92rem; padding: .35rem .8rem; text-align: center; }}
        .filter-list {{ display: flex; flex-wrap: wrap; gap: .45rem; margin: 1rem 0; }}
        .filter-list a {{ background: var(--surface); border: 1px solid var(--edge); border-radius: 99rem; color: #211f1e; font-size: .86rem; padding: .3rem .7rem; text-decoration: none; }}
        .article-list {{ display: grid; gap: .9rem; margin-top: 1rem; }}
        .article-card {{ background: var(--surface); border: 1px solid var(--edge); border-radius: .65rem; padding: 1rem 1.1rem; }}
        .article-card a {{ color: var(--accent); text-decoration: none; }}
        .article-card a:hover {{ text-decoration: underline; }}
        .article-card p {{ margin: .45rem 0; }}
        .meta {{ color: var(--muted); font-size: .86rem; }}
        .actions {{ margin-top: 1.3rem; }}
        .pagination {{ color: var(--muted); font-size: .94rem; margin-top: 1.3rem; }}
        footer {{ border-top: 1px solid var(--edge); color: var(--muted); font-size: .88rem; padding: 1.2rem 1.1rem 2rem; }}
        .login-panel {{ background: var(--surface); border: 1px solid var(--edge); border-radius: .8rem; max-width: 22rem; padding: 1.4rem; }}
        form:not(.search-form) label {{ display: block; font-weight: 600; margin: .8rem 0 .2rem; }}
        form:not(.search-form) input {{ border: 1px solid var(--edge); border-radius: .4rem; padding: .6rem .7rem; width: 100%; }}
        form:not(.search-form) button {{ background: var(--accent); border: 0; border-radius: .4rem; color: #fff; cursor: pointer; display: block; font: inherit; margin-top: 1.1rem; padding: .6rem .9rem; }}
    </style>
</head>
<body>
<header class='site-header'>
    <div class='layout'>
        <a class='site-title' href='/'>News Intelligence</a>
        {render_search_form()}
        {render_navigation()}
    </div>
</header>
<main class='page layout'>{body}</main>
<footer>© 2026 News Intelligence Platform</footer>
</body>
</html>"""


def render_search_page(title: str, body: str) -> str:
    return render_html_page(title, body)


def render_search_results(query: str, result: Page, selected_category: CategoryGroup | None = None) -> str:
    if not query:
        heading = "Search"
    elif result.total:
        heading = f"Search: {query}"
    else:
        heading = "No matching content"
    body = f"""
<h1>{escape(heading)}</h1>
<p>{result.total} matching page{'s' if result.total != 1 else ''}</p>
{render_search_filters(query, selected_category)}
<div class='article-list'>{render_article_items(result.items)}</div>
    """
    return render_html_page("Search", body)


class PortalHandler(BaseHTTPRequestHandler):
    def __init__(
        self,
        service: InMemoryPlatformService,
        account_manager: AccountManager,
        session_manager: SessionManager,
        search_engine: SearchEngine,
        *args: object,
        ingestion_reports: Sequence[IngestionReport] = (),
        **kwargs: object,
    ) -> None:
        self.service = service
        self.account_manager = account_manager
        self.session_manager = session_manager
        self.search_engine = search_engine
        self.ingestion_reports = list(ingestion_reports)
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/logout":
            self.handle_logout()
            return
        if not self.is_authenticated(path):
            self.show_login_page()
            return
        if path in {"/", "/home"}:
            self.show_home_page()
        elif path.startswith("/extensions/"):
            self.show_extension_page(path.removeprefix("/extensions/"))
        elif path.startswith("/category/"):
            self.show_category_page(path.removeprefix("/category/"))
        elif path.startswith("/article/"):
            self.show_article_page(path.removeprefix("/article/"))
        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif path == "/api/ingestion":
            self.handle_ingestion_api()
        elif path == "/api/search":
            self.handle_search_api()
        elif path == "/search":
            self.handle_search_page()
        elif path == "/login":
            self.show_login_page()
        else:
            self.show_not_found()

    def do_POST(self) -> None:
        if urlparse(self.path).path == "/login":
            self.handle_login()
        else:
            self.show_not_found()

    def session_token(self) -> str | None:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get("portal_session")
        return morsel.value if morsel else None

    def search_category(self, query: dict[str, list[str]]) -> CategoryGroup | None:
        text = query.get("category", [""])[0]
        if not text:
            return None
        try:
            return CategoryGroup(text)
        except ValueError:
            raise KeyError(text) from None

    def is_authenticated(self, path: str) -> bool:
        return path in {"/login", "/health", "/api/ingestion"} or self.current_session() is not None

    def current_session(self):
        return self.session_manager.resolve(self.session_token())

    def show_home_page(self) -> None:
        sections = "".join(render_extension_section(extension) for extension in self.service.extensions)
        navigation = "".join(
            f"<li><a href='/category/{escape(category.value)}'>{escape(category_label(category))}</a></li>"
            for category in CategoryGroup
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
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        page = max(1, int(query.get("page", ["1"])[0]))
        page_size = min(50, max(1, int(query.get("page_size", ["10"])[0])))
        result = self.service.list_articles(category, page=page, page_size=page_size)
        article_rows = render_article_items(result.items)
        pagination = self.render_pagination(page, page_size, result.total)
        html_content = render_html_page(
            category_label(category),
            f"<h1>{escape(category_label(category))}</h1><p class='page-meta'>{result.total} articles · page {page}</p><div class='article-list'>{article_rows}</div><nav class='pagination'>{pagination}</nav>",
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def show_article_page(self, article_id: str) -> None:
        try:
            article = self.service.get_article(int(article_id))
        except (KeyError, ValueError):
            self.show_not_found()
            return
        html_content = render_html_page(
            article.title,
            f"""<article><h1>{escape(article.title)}</h1>
<p class='page-meta'>{escape(article.source)} · {escape(category_label(article.category_id))}</p>
<p>{escape(article.summary)}</p>
<p class='actions'><a href='{escape(article.url)}'>Read source</a></p>
</article>""",
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def show_not_found(self) -> None:
        path = urlparse(self.path).path
        html_content = render_html_page("Not Found", f"<h1>404</h1><p>{escape(path)} does not exist.</p>")
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
        if not email or not password:
            self.show_login_page("Email and password are required.", status=400)
            return
        if self.account_manager.authenticate(email, password) is None:
            self.show_login_page("Invalid credentials.", status=401)
            return
        session = self.session_manager.create(self.account_manager.authenticate(email, password))
        html_content = render_html_page(
            "Signed In",
            "<h1>Welcome back</h1><p>You are signed in to the platform.</p>",
        )
        self.send_response(303)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header(
            "Set-Cookie",
            f"portal_session={session.token}; Path=/; HttpOnly; SameSite=Lax",
        )
        self.send_header("Location", "/")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def handle_logout(self) -> None:
        self.session_manager.revoke(self.session_token())
        self.send_response(303)
        self.send_header(
            "Set-Cookie",
            "portal_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0",
        )
        self.send_header("Location", "/login")
        self.end_headers()

    def handle_search_api(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        text = query.get("q", [""])[0]
        try:
            category = self.search_category(query)
        except KeyError:
            self.show_not_found()
            return
        page = max(1, int(query.get("page", ["1"])[0]))
        page_size = min(100, max(1, int(query.get("page_size", ["10"])[0])))
        result = self.search_engine.search(
            text,
            category=category,
            page=page,
            page_size=page_size,
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            dumps(
                {
                    "query": text,
                    "page": result.page,
                    "page_size": result.page_size,
                    "total": result.total,
                    "items": [
                        {
                            "id": article.id,
                            "title": article.title,
                            "summary": article.summary,
                            "category": article.category_id.value,
                        }
                        for article in result.items
                    ],
                },
                ensure_ascii=False,
            ).encode("utf-8"),
    )

    def handle_ingestion_api(self) -> None:
        status = "ok" if all(report.succeeded for report in self.ingestion_reports) else "degraded"
        payload = {
            "status": status,
            "jobs": [
                {
                    "slug": report.slug,
                    "label": report.label,
                    "item_count": report.item_count,
                    "error": report.error,
                }
                for report in self.ingestion_reports
            ],
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(dumps(payload, ensure_ascii=False).encode("utf-8"))

    def handle_search_page(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        text = query.get("q", [""])[0]
        try:
            category = self.search_category(query)
        except KeyError:
            self.show_not_found()
            return
        page_size = min(50, max(1, int(query.get("page_size", ["10"])[0])))
        result = self.search_engine.search(
            text,
            category=category,
            page_size=page_size,
        )
        html_content = render_search_results(text, result, category)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def log_message(self, message: str, *args: object) -> None:
        pass

    def render_pagination(self, page: int, page_size: int, total_count: int) -> str:
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        previous_page = max(1, page - 1)
        next_page = min(total_pages, page + 1)
        links = [f"<a href='?page=1'>First</a>", f"<a href='?page={previous_page}'>Prev</a>"]
        links.append(f"<a href='?page={next_page}'>Next</a>")
        links.append(f"<a href='?page={total_pages}'>Last</a>")
        return f"Page {page} of {total_pages} " + " ".join(links)
