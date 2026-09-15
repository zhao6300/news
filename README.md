# News Intelligence Platform

面向新闻、技术、模型、评测等内容的轻量级信息收集平台。当前版本使用 Python 标准库完成 Web、服务层、存储层、RSS 连接器和诊断接口，避免平台核心依赖第三方包。

## 架构

平台使用前后端分离结构：

- `frontend/index.html` 是唯一页面壳。
- `frontend/static/app.js` 负责页面路由、中文界面和数据渲染。
- `frontend/static/styles.css` 负责样式。
- Python 后端通过 `/api/bootstrap`、`/api/articles`、`/api/extensions/{slug}`、`/api/search`、`/api/login`、`/api/logout` 提供数据。
- 后端仍然是 Python 标准库，前端仍然是浏览器原生 `fetch`，没有 React/Vue/Vite/Node/npm 依赖。
- 平台登录门禁在浏览器侧显示，受保护的分类、文章、搜索和来源数据仍然通过服务层与仓储层获取。

## 项目结构

- `src/app.py` — Web 路由、页面渲染和登录会话处理。
- `frontend/core/` — 独立前端核心：页面壳、静态资源和本地路由。
- `frontend/` — 浏览器壳、静态资源和页面路由逻辑。
- `src/auth.py` — 账号模型、密码校验和账号访问控制。
- `src/services.py` — 分类、来源、文章查询和分页服务。
- `src/storage.py` — 可替换仓储接口与内存实现。
- `src/sqlite_store.py` — SQLite 持久化实现。
- `src/connectors.py` — 统一来源协议与 RSS 连接器。
- `src/extensions/builtin.py` — 启动时的内置示例数据。
- `tests/` — 单元测试与 HTTP 集成测试。

## 环境要求

- Python 3.11 或更高版本
- Make

不需要安装 `npm`、Node.js、Django、Flask 或第三方依赖。

## 界面设计

当前界面参考主流新闻网站的信息层级，保持清晰、安静、可扫读：

1. 顶部使用紧凑导航条，品牌、搜索和账户操作分布在同一层。
2. 分类导航横向滚动，新闻、技术、模型、评测和来源状态按同一规则展示。
3. 文章优先：卡片突出标题、摘要、日期、来源和分类；标签作为辅助信息。
4. 使用浅色为主的稳重配色与深色模式自动适配。
5. 移动端保持独立单列，不牺牲可读性。
6. 全站使用较大的连续圆角，分类导航保持主导航形态，不使用标签胶囊。

## 响应式布局

页面按内容宽度自动调节栏目数量：

1. 1240px 以上保持宽屏版面，但不超过 1460px，避免过度拉伸。
2. 1120px 以下压缩主标题并预留给顶部操作折行空间。
3. 880px 以下文章和来源采用单列，分类导航保持水平滚动。
4. 420px 和 360px 移动宽度下正文、表单和页脚使用紧凑内边距。
5. 卡片内元信息与阅读入口独立布局，不会继承站点页脚的居中和外边距样式。

## 快速启动

```bash
PLATFORM_ACCOUNT_EMAIL=owner@example.com \
PLATFORM_ACCOUNT_PASSWORD=owner-password \
make run
```

默认入口是 `frontend/core/main.py`，能够独立启动前后端进程。

默认地址为 `http://127.0.0.1:8000`。如果缺少账号环境变量，应用会启动失败，而不是使用不安全的默认账号。
未设置 `PLATFORM_PORT` 时，应用会从默认端口开始，最多自动尝试后续 19 个端口。

修改监听地址和端口：

```bash
PLATFORM_HOST=0.0.0.0 \
PLATFORM_PORT=8080 \
PLATFORM_ACCOUNT_EMAIL=owner@example.com \
PLATFORM_ACCOUNT_PASSWORD=owner-password \
make run
```

本地演示账号用户名是 `member@example.com`，密码是 `demo-password`。生产环境必须通过环境变量替换为真实账号。

## 持久化

```bash
PLATFORM_DB=./platform.sqlite3 \
PLATFORM_ACCOUNT_EMAIL=owner@example.com \
PLATFORM_ACCOUNT_PASSWORD=owner-password \
make run
```

设置 `PLATFORM_DB` 后，文章会保存到 SQLite 文件。未设置时使用内存数据，进程退出后重置。

## 登录行为

- 登录页路径：`/login`。
- 表单字段使用中文提示：邮箱、密码。
- 登录失败继续返回 401，并显示“登录失败，请检查邮箱和密码。”。
- 已登录访问 `/login` 会跳转到 `/`，不会重新替换当前会话。
- 退出登录：`/logout`。
- 账户页：`/account`。

登录成功后，服务端会写入 `portal_session` Cookie。该 Cookie 设置为 `HttpOnly` 和 `SameSite=Lax`。浏览器端所有 JSON 请求都会透传 Cookie，服务端会话在 `make run` 进程生命周期内保持。

## 新闻源接入

平台内置统一的来源连接器协议。启动时会直接抓取真实 RSS/Atom 来源；默认不再加载“内置示例数据”。
默认来源会并行读取并在读取完成后按统一顺序落库，以缩短启动等待时间。
运行过程中也可以登录后在 `/sources` 页面添加 RSS 或 Atom 信息源，或通过 `PLATFORM_FEEDS` 配置固定来源替换全部默认来源。

默认真实来源包括：

1. 科技：Hacker News、Ars Technica、The Verge、TechCrunch、Wired、IEEE Spectrum、Engadget。
2. 财经：MarketWatch、CNBC、Yahoo Finance、Investing.com、CBC Business。

登录后的手动添加只使用中文表单，字段如下：

1. `来源名称`：1 到 60 个字符。
2. `信息分类`：`ai`、`news`、`tech`、`finance`、`models` 或 `reviews`。
3. `信息源地址`：HTTP 或 HTTPS 的 RSS 或 Atom 地址。
4. `每次拉取条数`：1 到 100。

例如：

```json
{
  "label": "科技研究源",
  "category": "tech",
  "feed_url": "https://example.com/rss.xml",
  "limit": 20
}
```

免费预置源分为科技和财经两类：

1. 科技：Hacker News、Ars Technica、The Verge、TechCrunch、Wired、IEEE Spectrum、Engadget。
2. 财经：MarketWatch、CNBC、Yahoo Finance、Investing.com、CBC Business。

启动前配置的 RSS 或 Atom 来源通过 `PLATFORM_FEEDS` 设置：

```bash
PLATFORM_FEEDS='[
  {
    "slug": "local-news",
    "source": "Local News",
    "category": "news",
    "url": "https://example.com/rss.xml",
    "limit": 20,
    "timeout": 10
  },
  {
    "slug": "tech-rss",
    "source": "Technology Feed",
    "category": "technology",
    "url": "https://example.com/technology.xml",
    "limit": 30,
    "timeout": 15
  }
]' \
PLATFORM_ACCOUNT_EMAIL=owner@example.com \
PLATFORM_ACCOUNT_PASSWORD=owner-password \
make run
```

`PLATFORM_FEEDS` 必须是 JSON 数组。每条记录的必填字段：

- `slug`：来源的唯一英文标识。
- `source`：页面上显示的来源名称。
- `category`：内容分类，必须是 `ai`、`news`、`tech`、`finance`、`models` 或 `reviews`。
- `url`：RSS 或 Atom 文档地址。

可选字段：

- `limit`：文章条数上限，范围是 1 到任意正整数。
- `timeout`：拉取超时时间，单位秒。

RSS 连接器会根据文章 URL 生成稳定 ID。来源不可访问、格式错误或缺失必要字段时，该来源会在诊断接口中报告失败，不会让整个服务崩溃。

运行时手动添加的来源默认仍保存在当前进程内存中；如果需要长期保存，请使用 `PLATFORM_FEEDS` 配置或等待后续持久化阶段。

## 来源诊断

登录后访问：

```text
/api/sources
```

返回所有已注册来源：

```json
{
  "status": "ok",
  "sources": [
    {
      "slug": "builtin",
      "label": "Builtin",
      "url": "/extensions/builtin",
      "article_count": 6,
      "categories": [],
      "ingestion": {
        "status": "ok",
        "item_count": 6,
        "error": null
      }
    }
  ]
}
```

`ingestion.error` 不是 `null` 时表示来源启动失败；`ingestion.status` 为 `failed` 表示连接器或数据格式存在问题。

启动级诊断也可通过：

```text
/api/ingestion
```

## 页面和接口

- `GET /`：前端应用壳。
- `GET /static/{styles.css|app.js}`：前端静态资源。
- `GET /api/bootstrap`：全局分类、来源、登录状态。
- `GET /api/articles`：内容和分页。
- `GET /api/articles/{id}`：文章详情。
- `GET /api/extensions/{slug}`：指定来源内容。

- `GET /`：首页和全部来源聚合。
- `GET /extensions/{slug}`：指定来源的文章列表。
- `GET /category/{slug}`：分类目录，支持分页。
- `GET /article/{id}`：文章详情。
- `GET /search?q=`：关键词搜索页面。
- `GET /api/search?q=`：关键词搜索 API。
- `GET /api/sources`：来源和拉取状态。
- `GET /api/ingestion`：启动归集任务状态。
- `GET /login` 和 `POST /login`：登录页和登录提交。
- `GET /logout`：退出登录。
- `GET /health`：服务健康检查。

分类分页支持 `?page=` 和 `?page_size=1..50`。搜索支持 `category` 和 `source` 过滤。

## 测试

```bash
make test
```

分层验证：

```bash
make unit
make integration
```

## 已知限制

1. 外部 RSS 已兼容 RSS/Atom 基础条目；复杂命名空间媒体字段仍不解析。
2. 运行时手动添加的来源重启后会丢失；`PLATFORM_FEEDS` 或默认来源重启后会重新抓取。
3. 登录会话保存在进程内存中，重启需要重新登录。
4. 默认端口被占用时，启动会显示中文错误，需要结束占用进程或设置 `PLATFORM_PORT`。
5. 内置示例数据用于验证平台结构，不是正式新闻数据。

## 下一步

1. 增加来源级别手动刷新接口。
2. 增加 Atom 兼容解析器。
3. 增加来源启停开关和失败退避策略。
4. 把登录会话迁移到 SQLite 或其他持久化存储。
