import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def _message(detail):
    if detail is None:
        return "请求失败"
    if isinstance(detail, dict):
        if "detail" in detail:
            return str(detail["detail"])
        parts = []
        for key, value in detail.items():
            text = value[0] if isinstance(value, list) and value else value
            parts.append(str(text))
        return "；".join(parts) or "请求失败"
    if isinstance(detail, list):
        return str(detail[0]) if detail else "请求失败"
    return str(detail)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("未处理异常")
        return Response({"code": 1, "message": "服务器错误", "data": None}, status=500)
    response.data = {"code": 1, "message": _message(response.data), "data": None}
    return response
