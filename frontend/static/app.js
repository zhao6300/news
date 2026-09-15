const view = document.querySelector("#view");
const categoryNav = document.querySelector("#category-nav");
const accountStatus = document.querySelector("#account-status");
const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#search-input");
const assistantLauncher = document.querySelector("#assistant-launcher");
const assistantHost = document.querySelector("#assistant-host");
const assistantTitle = document.querySelector("#assistant-title");
const assistantStatus = document.querySelector("#assistant-status");
const assistantCommand = document.querySelector("#assistant-command");
const assistantActions = document.querySelector("#assistant-actions");

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.message || `请求失败（${response.status}）`);
    error.status = response.status;
    error.payload = payload;
    throw error;
  }
  return payload;
}

function categoryLabel(slug) {
  const labels = {
    ai: "人工智能",
    news: "新闻",
    tech: "技术",
    finance: "财经",
    models: "模型",
    reviews: "评测",
  };
  return labels[slug] || slug;
}

function articleCard(article) {
  const tags = article.tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
  return `
    <article class="news-card">
      <a href="/article/${article.id}">
        <h3>${escapeHtml(article.title)}</h3>
      </a>
      <p>${escapeHtml(article.summary)}</p>
      <div class="tag-list">${tags}</div>
      <footer>
        <span class="card-meta">
          <span class="date">${escapeHtml(article.published_at.split("T", 1)[0])}</span>
          <strong>${escapeHtml(article.source)}</strong>
          <span>${escapeHtml(categoryLabel(article.category))}</span>
        </span>
        <a class="read-more" href="/article/${article.id}">阅读全文</a>
      </footer>
    </article>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[character]));
}

function renderLoading() {
  view.innerHTML = `<p class="loading">正在加载平台内容…</p>`;
}

function renderError(error) {
  if (error.status === 401) {
    history.replaceState({}, "", "/login");
  }
  view.innerHTML = `<p class="empty">${escapeHtml(error.message)}</p>`;
}

function hideAssistant() {
  if (!assistantHost || assistantHost.hidden) return;
  assistantHost.hidden = true;
  hideAssistant();
}

function renderAssistantPanel(advice) {
  if (!assistantHost) {
    return;
  }
  assistantHost.innerHTML = `
    <div class="assistant-panel">
<div class="assistant-panel__head">
        <strong id="assistant-title">${escapeHtml(advice.title)}</strong>
        <button type="button" id="assistant-close">×</button>
      </div>
      <p id="assistant-status" class="assistant-status">${escapeHtml(advice.status)}</p>
      <p>${escapeHtml(advice.message)}</p>
      <ul id="assistant-actions">
        ${advice.actions.map((action) => `
          <li>
            <a href="${escapeHtml(action.href)}">
              <strong>${escapeHtml(action.label)}</strong>
              ${action.description ? `<small>${escapeHtml(action.description)}</small>` : ""}
            </a>
          </li>
        `).join("")}
      </ul>
      <form id="assistant-question" class="assistant-question">
        <input id="assistant-command" name="text" type="text" autocomplete="off" placeholder="告诉我你要收集的内容">
        <button type="submit">规划</button>
      </form>
    </div>`;
  assistantHost.hidden = false;
  const close = assistantHost.querySelector("#assistant-close");
  if (close) {
    close.addEventListener("click", () => {
  hideAssistant();
      const launcher = document.querySelector("#assistant-launcher");
      if (launcher) launcher.focus();
    });
  }
  assistantHost.querySelector("#assistant-question").addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = new FormData(event.currentTarget).get("text").toString().trim();
    const advice = await api("/api/assistant", { method: "POST", body: JSON.stringify({ route: location.pathname + location.search, text }) });
    renderAssistantPanel(advice);
  });
  close.focus();
  return;
}

async function showAssistant(path) {
  try {
    const search = new URLSearchParams({ route: path });
    const query = new URLSearchParams(location.search).get("q");
    if (query) search.set("q", query);
    const advice = await api(`/api/assistant?${search.toString()}`);
    renderAssistantPanel(advice);
  } catch {
    // 助手不影响主内容。
  }
}

function renderFilterControls(categories, sources, current = {}) {
  const categoryOptions = categories
    .map((category) => `<option value="${escapeHtml(category.slug)}" ${current.category === category.slug ? "selected" : ""}>${escapeHtml(category.label)}</option>`)
    .join("");
  const sourceOptions = sources
    .map((source) => `<option value="${escapeHtml(source.label)}" ${current.source === source.label ? "selected" : ""}>${escapeHtml(source.label)}</option>`)
    .join("");
  return `
    <section class="filter-panel" aria-label="新闻筛选">
      <form id="news-filter-form">
        <label for="filter-query">搜索新闻</label>
        <input id="filter-query" name="q" type="search" value="${escapeHtml(current.query || "")}" placeholder="搜索标题、摘要、来源或标签">
        <label for="filter-category">分类</label>
        <select id="filter-category" name="category">
          <option value="">全部分类</option>${categoryOptions}
        </select>
        <label for="filter-source">来源</label>
        <select id="filter-source" name="source">
          <option value="">全部来源</option>${sourceOptions}
        </select>
        <button type="submit">应用筛选</button>
      </form>
    </section>`;
}

function filterUrl(item, current = {}) {
  const params = new URLSearchParams();
  if (current.query) params.set("q", current.query);
  if (current.category) params.set("category", current.category);
  if (current.source) params.set("source", current.source);
  if (item.page && item.page > 1) params.set("page", String(item.page));
  const suffix = params.toString();
  return `${item.path}${suffix ? `?${suffix}` : ""}`;
}

function renderPagination(current, result) {
  if (result.total_pages <= 1) return "";
  return `
    <nav class="pagination page-meta">
      <a href="${filterUrl({ path: current.path, ...current, page: Math.max(1, result.page - 1) }, current)}">上一页</a>
      <span>第 ${result.page} / ${result.total_pages} 页</span>
      <a href="${filterUrl({ path: current.path, ...current, page: Math.min(result.total_pages, result.page + 1) }, current)}">下一页</a>
    </nav>`;
}

function renderHome(bootstrap, sources, articles, current = {}) {
  const sourceCards = sources.map((source) => `
    <a class="card source-card" href="/extensions/${escapeHtml(source.slug)}">
      <strong><span>${escapeHtml(source.label)}</span><span>${source.article_count}</span></strong>
      <span>${(source.categories || []).map((category) => escapeHtml(category.label)).join(" · ") || "全部内容"}</span>
    </a>`).join("");
  const articleCards = articles.items.map(articleCard).join("");
  view.innerHTML = `
    <div class="page-heading">
      <h1>AI 信息平台</h1>
    <p class="page-meta">来自新闻、技术、模型和评测来源的最新内容。</p>
    </div>
    ${renderFilterControls(bootstrap.categories, sources, current)}
    <section><h2 class="section-title">内容来源</h2><div class="cards">${sourceCards}</div></section>
    <section>
      <h2 class="section-title">最新内容</h2>
      <div class="content-grid two">${articleCards || '<p class="empty">没有匹配的新闻。</p>'}</div>
      ${renderPagination(current, articles)}
    </section>`;
  document.querySelector("#news-filter-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const next = {
      query: String(form.get("q") || "").trim(),
      category: String(form.get("category") || ""),
      source: String(form.get("source") || ""),
    };
    history.pushState({}, "", filterUrl({ path: "/", ...next, page: 1 }));
    route();
  });
}

function renderCategory(category, result, page) {
  const cards = result.items.map(articleCard).join("");
  const previous = Math.max(1, page - 1);
  const next = Math.min(result.total_pages, page + 1);
  const pager = result.total_pages > 1 ? `
    <nav class="pagination page-meta">
      <a href="/category/${category.slug}?page=${previous}">上一页</a>
      <span>第 ${result.page} / ${result.total_pages} 页</span>
      <a href="/category/${category.slug}?page=${next}">下一页</a>
    </nav>` : "";
  view.innerHTML = `
    <h1 class="page-heading">${escapeHtml(categoryLabel(category.slug))}</h1>
    <p class="page-meta">${result.total} 条内容</p>
    <div class="content-grid two">${cards || '<p class="empty">该分类暂无内容</p>'}</div>${pager}`;
}

function renderArticle(article) {
  const tags = article.tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
  view.innerHTML = `
    <div class="page-heading"><a href="/">← 返回首页</a></div>
    <article class="detail-card">
      <h1 class="page-heading">${escapeHtml(article.title)}</h1>
      <div class="detail-meta">
        <span>${escapeHtml(article.published_at.split("T", 1)[0])}</span>
        <span>${escapeHtml(article.source)}</span>
        <span><a href="/category/${article.category}">${escapeHtml(categoryLabel(article.category))}</a></span>
      </div>
      <div class="tag-list">${tags}</div>
      <p>${escapeHtml(article.summary)}</p>
      <a class="link" href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer">查看原文</a>
    </article>`;
}

function renderSources(sources, categories = [], options = []) {
  const categoryOptions = categories
    .map((category) => `<option value="${escapeHtml(category.slug)}">${escapeHtml(category.label)}</option>`)
    .join("");
  const presetOptions = options
    .map((option) => `<option value="${escapeHtml(option.id)}">${escapeHtml(option.label)} · ${escapeHtml(categoryLabel(option.category))}</option>`)
    .join("");
  const form = `
    <section class="source-form-card">
      <h2 class="section-title">添加信息源</h2>
      <p class="page-meta">填写来源名称、分类和 RSS 或 Atom 地址，提交后会立即读取最近内容。</p>
      <form class="form source-form" id="source-form">
        <label for="source-preset">免费预置源</label>
        <select id="source-preset" name="source_preset">
          <option value="">手填来源</option>
          ${presetOptions}
        </select>
        <label for="source-label">来源名称</label>
        <input id="source-label" name="label" type="text" required maxlength="60" placeholder="例如：科技研究源">
        <label for="source-category">信息分类</label>
        <select id="source-category" name="category" required>${categoryOptions}</select>
        <label for="source-url">信息源地址</label>
        <input id="source-url" name="feed_url" type="url" required placeholder="https://example.com/rss.xml 或 atom.xml">
        <label for="source-limit">每次拉取条数</label>
        <input id="source-limit" name="limit" type="number" min="1" max="100" value="20" required>
        <p id="source-form-message" class="message" aria-live="polite"></p>
        <button type="submit">添加</button>
      </form>
    </section>`;
  const cards = sources.map((source) => `
    <a class="card source-card" href="/extensions/${escapeHtml(source.slug)}">
      <h3 class="card-title">${escapeHtml(source.label)}</h3>
      <div class="source-cat">
        <span>${(source.categories || []).map((item) => escapeHtml(item.label)).join(" · ") || "全部内容"}</span>
        <span>${escapeHtml(source.article_count)}</span>
      </div>
    </a>`).join("");
  view.innerHTML = `
    <h1 class="page-heading">内容来源</h1>
    <p class="page-meta">包含内置来源和已配置的 RSS 连接器。</p>
    ${form}
    <div class="content-grid two">${cards || '<p class="empty">暂无来源</p>'}</div>`;
  document.querySelector("#source-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const message = document.querySelector("#source-form-message");
    try {
      await api("/api/sources", {
        method: "POST",
        body: JSON.stringify({
          label: formData.get("label"),
          category: formData.get("category"),
          feed_url: formData.get("feed_url"),
          limit: Number(formData.get("limit")),
        }),
      });
      await route();
    } catch (error) {
      if (message) {
        message.textContent = error.message;
        message.className = "message error";
      }
    }
  });
  document.querySelector("#source-preset").addEventListener("change", (event) => {
    const preset = options.find((item) => item.id === event.currentTarget.value);
    if (!preset) return;
    document.querySelector("#source-label").value = preset.label;
    document.querySelector("#source-category").value = preset.category;
    document.querySelector("#source-url").value = preset.feed_url;
  });
}

function renderExtension(extension) {
  const cards = extension.items.map(articleCard).join("");
  view.innerHTML = `
    <a href="/sources" class="page-button">← 返回来源</a>
    <h1 class="page-heading">${escapeHtml(extension.label)}</h1>
    <p class="page-meta">${extension.article_count} 条内容</p>
    <div class="content-grid two">${cards || '<p class="empty">该来源暂无内容</p>'}</div>`;
}

function renderSearch(query, result, page) {
  const cards = result.items.map(articleCard).join("");
  const previous = Math.max(1, page - 1);
  const next = Math.min(result.total_pages, page + 1);
  const pager = result.total_pages > 1 ? `
    <nav class="pagination page-meta">
      <a href="/search?q=${encodeURIComponent(query)}&page=${previous}">上一页</a>
      <span>第 ${result.page} / ${result.total_pages} 页</span>
      <a href="/search?q=${encodeURIComponent(query)}&page=${next}">下一页</a>
    </nav>` : "";
  view.innerHTML = `
    <h1 class="page-heading">${query ? `搜索：${escapeHtml(query)}` : "搜索"}</h1>
    <p class="page-meta">${result.total} 条匹配内容</p>
    <aside class="assistant-notice">AI 已基于关键词和来源结构生成这批候选。筛选关键词、分类或来源可以让下一步更收敛。</aside>
    <div class="content-grid two">${cards || '<p class="empty">没有匹配的内容</p>'}</div>${pager}`;
}

function renderLogin(message = "", status = "") {
  view.innerHTML = `
    <div class="login-panel">
      <h1 class="page-heading">登录</h1>
      ${message ? `<p class="message ${status === "failed" ? "error" : ""}">${escapeHtml(message)}</p>` : ""}
      <p class="assistant-notice">登录后 AI 会继续处理来源、分类、摘要和长期任务。未登录时只提供公共入口。</p>
      <form class="form" id="login-form">
        <label for="email">邮箱</label>
        <input id="email" name="email" type="email" required>
        <label for="password">密码</label>
        <input id="password" name="password" type="password" required>
        <button type="submit">登录</button>
      </form>
    </div>`;
  document.querySelector("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await api("/api/login", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(form)),
      });
      history.replaceState({}, "", "/");
      await route();
    } catch (error) {
      renderLogin(error.message, "failed");
    }
  });
}

function renderAccount(bootstrap) {
  const account = bootstrap.account;
  view.innerHTML = `
    <div class="form-panel">
      <h1 class="page-heading">账户</h1>
      <p>已登录：${escapeHtml(account.email)}</p>
      <a href="/logout">退出登录</a>
    </div>`;
}

function updateNavigation(bootstrap) {
  const currentPath = location.pathname;
  if (assistantStatus && assistantTitle && assistantActions) {
    if (!bootstrap.account) {
      assistantStatus.textContent = "AI 未连接";
      assistantTitle.textContent = "AI 助手离线";
      assistantActions.hidden = true;
    } else {
      assistantStatus.textContent = "AI 助手已连接";
      assistantActions.hidden = false;
    }
  }
  categoryNav.innerHTML = bootstrap.categories.map((category) => {
    const active = currentPath === `/category/${category.slug}` ? " active" : "";
    return `<a class="${active}" href="/category/${category.slug}">${escapeHtml(categoryLabel(category.slug))}<span>${category.article_count}</span></a>`;
  }).join("");
  searchForm.dataset.next = location.pathname + location.search;
  if (bootstrap.account) {
    accountStatus.innerHTML = `<a href="/account">账户</a><a href="/logout">退出</a>`;
  } else {
    accountStatus.innerHTML = `<a href="/login">登录</a>`;
  }
  if (searchInput) searchInput.value = currentPath === "/search" ? new URL(location.href).searchParams.get("q") || "" : searchInput.value;
}

async function route() {
  renderLoading();
  document.title = "News Intelligence Platform";
  const [path, search] = [location.pathname, new URLSearchParams(location.search)];
  await showAssistant(path);
  try {
    if (path === "/login") {
      const bootstrap = await api("/api/bootstrap");
      updateNavigation(bootstrap);
      if (bootstrap.account) {
        history.replaceState({}, "", "/");
        return route();
      }
      renderLogin();
      return;
    }

    if (path === "/logout") {
      await api("/api/logout", { method: "POST" });
      history.replaceState({}, "", "/login");
      return route();
    }

    const bootstrap = await api("/api/bootstrap");
    updateNavigation(bootstrap);
    if (!bootstrap.account) {
      history.replaceState({}, "", "/login");
      renderLogin("请先登录。");
      return;
    }

    if (path === "/account") {
      renderAccount(bootstrap);
      return;
    }

    if (path === "/sources") {
      const sources = await api("/api/sources");
      renderSources(sources.sources || [], bootstrap.categories, sources.source_options || []);
      return;
    }

    const extensionMatch = path.match(/^\/extensions\/([a-z0-9-]+)/);
    if (extensionMatch) {
      renderExtension(await api(`/api/extensions/${extensionMatch[1]}`));
      return;
    }

    if (path === "/") {
      const current = {
        query: search.get("q") || "",
        category: search.get("category") || "",
        source: search.get("source") || "",
      };
      const sources = await api("/api/sources");
      const articles = await api(`/api/articles${location.search}`);
      renderHome(bootstrap, sources.sources, {
        ...articles,
        total_pages: Math.max(1, Math.ceil(articles.total / articles.page_size)),
      }, current);
      return;
    }

    const articleMatch = path.match(/^\/article\/(\d+)$/);
    if (articleMatch) {
      renderArticle(await api(`/api/articles/${articleMatch[1]}`));
      return;
    }

    const categoryMatch = path.match(/^\/category\/([a-z0-9-]+)/);
    if (categoryMatch) {
      const params = new URLSearchParams({ category: categoryMatch[1], page: search.get("page") || "1" });
      const result = await api(`/api/articles?${params}`);
      const category = bootstrap.categories.find((item) => item.slug === categoryMatch[1]);
      if (!category) throw new Error("分类不存在");
      renderCategory(category, result, Number(params.get("page")));
      return;
    }

    if (path === "/search") {
      const query = search.get("q") || "";
      const params = new URLSearchParams({ q: query, page: search.get("page") || "1" });
      renderSearch(query, await api(`/api/search?${params}`), Number(params.get("page")));
      return;
    }

    throw new Error("页面不存在");
  } catch (error) {
    document.title = "页面错误 | News Intelligence Platform";
    renderError(error);
  }
}

window.addEventListener("popstate", route);
window.addEventListener("click", (event) => {
  const link = event.target.closest("a");
  if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target === "_blank") return;
  const url = new URL(link.href, location.href);
  if (url.origin !== location.origin) return;
  event.preventDefault();
  history.pushState({}, "", url.href);
  route();
});

if (assistantLauncher) {
  assistantLauncher.addEventListener("click", () => {
    if (!assistantHost.hidden) {
      hideAssistant();
      return;
    }
    showAssistant(location.pathname);
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && assistantHost && !assistantHost.hidden) {
    hideAssistant();
    const launcher = document.querySelector("#assistant-launcher");
    if (launcher) launcher.focus();
  }
});

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  history.pushState({}, "", `/search?q=${encodeURIComponent(searchInput.value.trim())}`);
  route();
});

route();
