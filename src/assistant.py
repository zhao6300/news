from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class AssistantAction:
    href: str
    label: str


@dataclass(frozen=True, slots=True)
class AssistantAdvice:
    route: str
    title: str
    message: str
    actions: tuple[AssistantAction, ...]
    mode: str = "basic"

    @classmethod
    def suggest(
        cls, route: str, context: str | None = None, *, auth: bool = False
    ) -> "AssistantAdvice":
        route_or_signin = (
            (
                AssistantAction("/login", "先登录平台"),
                AssistantAction("/", "回到首页"),
            )
            if not auth
            else (
                AssistantAction("/", "回到首页"),
                AssistantAction("/search", "开始检索"),
            )
        )
        if route == "/":
            return cls(
                route=route,
                title="首页 AI 助手",
                message="我会结合当前筛选条件推荐检索路径，必要时帮你切换高级分析模式。",
                actions=route_or_signin,
                mode="advanced" if auth else "basic",
            )
        if route.startswith("/category/"):
            category = route.removeprefix("/category/").split("/", 1)[0] or "content"
            return cls(
                route=route,
                title="分类阅读助手",
                message=f"可以继续筛选 {category} 相关内容，或切换到全局检索。",
                actions=(
                    AssistantAction(f"/category/{category}", "刷新当前分类"),
                    AssistantAction("/search", "全局检索"),
                ),
            )
        if route.startswith("/article/"):
            return cls(
                route=route,
                title="阅读助手",
                message="我可以帮你找同类来源，或回到分类继续收集资料。",
                actions=(
                    AssistantAction("/articles", "整理已有内容"),
                    AssistantAction("/sources", "查看信息源"),
                ),
            )
        if route.startswith("/extensions/"):
            return cls(
                route=route,
                title="信息源助手",
                message="可以从当前来源切回来源总览，保持采集目标一致。",
                actions=(AssistantAction("/sources", "返回信息源"),),
            )
        if route == "/sources":
            return cls(
                route=route,
                title="来源接入助手",
                message="我会检查目标分类，并建议新增科技、财经或 AI 类来源。",
                actions=(
                    AssistantAction("/sources", "继续配置来源"),
                    AssistantAction("/", "查看聚合结果"),
                ),
                mode="advanced" if auth else "basic",
            )
        if route == "/search":
            query = (context or "").strip()
            suffix = f"：“{query[:60]}”" if query else ""
            return cls(
                route=route,
                title="检索助手",
                message=f"可以继续收窄当前检索{suffix}，或按分类重设结果。",
                actions=route_or_signin,
            )
        if route == "/account":
            return cls(
                route=route,
                title="账号助手",
                message="可快速回到工作台，或管理与账号关联的信息源。",
                actions=(AssistantAction("/sources", "管理信息源"),),
            )
        if route == "/login":
            return cls(
                route=route,
                title="登录助手",
                message="登录后 AI 助手可以接管聚合、筛选与后续分析任务。",
                actions=(AssistantAction("/", "了解平台入口"),),
            )
        return cls(
            route=route,
            title="AI 助手",
            message="不清楚当前页面时，我可以先带你回到可用的信息入口。",
            actions=route_or_signin,
        )

    @property
    def payload(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "title": self.title,
            "message": self.message,
            "actions": [asdict(action) for action in self.actions],
        }
