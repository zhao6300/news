from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True, slots=True)
class AssistantAction:
    href: str
    label: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class AssistantAdvice:
    route: str
    title: str
    message: str
    actions: tuple[AssistantAction, ...]
    status: str = "已识别当前帮助场景"
    mode: str = "basic"
    commands: tuple[str, ...] = ("科技进展", "财经情报", "模型评测", "新增来源")

    @staticmethod
    def category_label(category: str) -> str:
        titles = {
            "ai": "AI",
            "news": "新闻",
            "tech": "技术",
            "finance": "财经",
            "models": "模型",
            "reviews": "评测",
        }
        return titles.get(category, category)

    @staticmethod
    def resolve_route_target(route: str) -> tuple[str, str]:
        parsed_path = urlparse(route).path.rstrip("/") or "/"
        matched = re.match(r"^/category/([^/]+)$", parsed_path)
        if matched:
            return parsed_path, AssistantAdvice.category_label(matched.group(1))
        matched_article = re.match(r"^/article/(\d+)$", parsed_path)
        if matched_article:
            return parsed_path, "当前文章"
        if parsed_path.startswith("/extensions/"):
            slug = parsed_path.split("/", 2)[-1]
            return parsed_path, f"来源 {slug}"
        titles = {
            "/": "平台工作台",
            "/home": "平台工作台",
            "/sources": "来源管理",
            "/search": "检索视图",
            "/account": "账户设置",
            "/login": "登录入口",
        }
        return parsed_path, titles.get(parsed_path, "未匹配路由")

    @staticmethod
    def resolve_route_context(raw_route: str) -> tuple[str, str]:
        parsed = urlparse(raw_route)
        query = parse_qs(parsed.query)
        route = parsed.path or "/"
        context = (
            (query.get("q", [None])[0] or query.get("category", [None])[0] or query.get("source", [None])[0] or "").strip()
        )
        return route, context

    @staticmethod
    def action(href: str, label: str, description: str = "") -> AssistantAction:
        return AssistantAction(href=href, label=label, description=description)

    @staticmethod
    def route_actions(authenticated: bool) -> tuple[AssistantAction, ...]:
        if not authenticated:
            return (
                AssistantAdvice.action("/login", "先登录平台", "解锁聚合和 AI 高级任务"),
                AssistantAdvice.action("/", "回到首页", "查看平台基础入口"),
            )
        return (
            AssistantAdvice.action("/", "回到首页", "重新聚合最新内容"),
            AssistantAdvice.action("/search", "开始检索", "收敛目标信息"),
        )

    @classmethod
    def suggest(
        cls, route: str, context: str | None = None, *, auth: bool = False
    ) -> "AssistantAdvice":
        route, scene = cls.resolve_route_target(route)
        route_or_signin = cls.route_actions(auth)
        if route == "/":
            return cls(
                route=route,
                title="首页助手",
                message="我会结合当前筛选条件推荐检索路径，必要时帮你切换高级分析模式。",
                actions=route_or_signin,
                status=scene if auth else "访客模式",
                mode="advanced" if auth else "basic",
            )
        if route.startswith("/category/"):
            category = route.removeprefix("/category/").split("/", 1)[0] or "content"
            category_text = cls.category_label(category)
            return cls(
                route=route,
                title="分类助手",
                message=f"已经定位 {category_text} 分类，可以继续筛选、检索或补充来源。",
                actions=(
                    cls.action(route, f"刷新{category_text}", "恢复当前筛选路径"),
                    cls.action("/search", "全局检索", "跨分类查找同一主题"),
                    cls.action("/sources", "补充来源", "检查分类支持"),
                ),
                status=scene,
            )
        if route.startswith("/article/"):
            article_id = route.removeprefix("/article/").split("/", 1)[0]
            return cls(
                route=route,
                title="文章助手",
                message="我可以帮你找同类来源，或回到分类继续收集资料。",
                actions=(
                    cls.action("/articles", "整理已有内容", "回到全部内容列表"),
                    cls.action("/sources", "查看信息源", "识别来源可靠性"),
                ),
                status=f"当前文章 {article_id}",
            )
        if route.startswith("/extensions/"):
            return cls(
                route=route,
                title="信息源助手",
                message="可以从当前来源切回来源总览，保持采集目标一致。",
                actions=(cls.action("/sources", "返回信息源", "查看全部来源状态"),),
                status=scene,
            )
        if route == "/sources":
            return cls(
                route=route,
                title="来源接入助手",
                message="我会检查目标分类，并建议新增科技、财经或 AI 类来源。",
                actions=(
                    cls.action("/sources", "继续配置来源", "进入来源管理表单"),
                    cls.action("/", "查看聚合结果", "回看当前采集效果"),
                ),
                status=scene,
                mode="advanced" if auth else "basic",
            )
        if route == "/search":
            query = (context or "").strip()
            suffix = f"：（{query[:60]}）" if query else ""
            return cls(
                route=route,
                title="检索助手",
                message=f"可以继续收窄当前检索{suffix}，或按分类重设结果。",
                actions=route_or_signin,
                status=scene,
            )
        if route == "/account":
            return cls(
                route=route,
                title="账号助手",
                message="可快速回到工作台，或管理与账号关联的信息源。",
                actions=(cls.action("/sources", "管理信息源", "查看来源健康状态"),),
                status=scene,
            )
        if route == "/login":
            return cls(
                route=route,
                title="登录助手",
                message="登录后 AI 助手可以接管聚合、筛选与后续分析任务。",
                actions=(cls.action("/", "了解平台入口", "查看平台基础能力"),),
                status=scene,
            )
        return cls(
            route=route,
            title="AI 助手",
            message="不清楚当前页面时，我可以先带你回到可用的信息入口。",
            actions=route_or_signin,
            status=scene,
        )

    @classmethod
    def plan_command(cls, route: str, text: str, *, auth: bool = False) -> "AssistantAdvice":
        cleaned = (text or "").strip()
        if not cleaned:
            return cls.suggest(route, auth=auth)
        lowered = cleaned.casefold()
        keyword_routes = {
            "科技": "/category/tech",
            "技术": "/category/tech",
            "tech": "/category/tech",
            "财经": "/category/finance",
            "金融": "/category/finance",
            "finance": "/category/finance",
            "模型": "/category/models",
            "models": "/category/models",
            "评测": "/category/reviews",
            "review": "/category/reviews",
            "新闻": "/category/news",
            "news": "/category/news",
            "AI": "/category/ai",
            "ai": "/category/ai",
        }
        matched_route = next(
            (target for keyword, target in keyword_routes.items() if keyword in lowered),
            None,
        )
        source_keywords = ("信息源", "来源", "新增来源", "source", "feed")
        target_route = (
            "/sources" if any(keyword in lowered for keyword in source_keywords) else matched_route
        )
        if target_route is None:
            return cls(
                route=route,
                title="检索反馈",
                message="暂时不能从这句话确定任务，可以先用关键词检索并保持当前页面上下文。",
                actions=(
                    cls.action(f"/search?q={cleaned[:160]}", "执行关键词检索", "把这句话压缩为搜索条件"),
                    cls.action("/", "回到首页", "从头确认信息目标"),
                ),
                status="已降级为关键词检索",
            )
        scene = cls.category_label(target_route.removeprefix("/category/")) if target_route.startswith("/category/") else "信息源管理"
        task = {
            "/category/tech": "收集技术进展",
            "/category/finance": "整理财经情报",
            "/category/models": "收集模型评测",
            "/category/reviews": "寻找评测线索",
            "/category/news": "聚合新闻",
            "/category/ai": "追踪 AI 进展",
            "/sources": "接入或检查信息源",
        }[target_route]
        return cls(
            route=route,
            title="AI 任务规划",
            message=f"已为你制定「{task}」任务，可直接进入对应视图并继续补充条件。",
            actions=(
                cls.action(target_route, "打开任务主视图", "进入统一筛选与聚合入口"),
                cls.action("/sources", "检查来源支持", "确认任务来源是否稳定"),
            ),
            status=f"已识别目标：{scene}",
            mode="advanced" if auth else "basic",
        )

    @property
    def payload(self) -> dict[str, object]:
        return {
            "status": self.status,
            "mode": self.mode,
            "title": self.title,
            "message": self.message,
            "commands": list(self.commands),
            "actions": [asdict(action) for action in self.actions],
        }
