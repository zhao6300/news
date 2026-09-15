from __future__ import annotations

from frontend.core.service import get_article_by_id


def handler(request):
    if request.path == "/":
        return "首页：<a href=\"/article/1\">示例文章</a>"
    if request.path == "/article/1":
        return str(get_article_by_id(1))
    raise ValueError("未匹配的路径。")
