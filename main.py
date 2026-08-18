import json
import httpx
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("astrbot_plugin_http_client", "YourName", "像Postman一样发起自定义HTTP请求", "1.0.0")
class HttpClientPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """插件初始化时可选的异步方法"""
        logger.info("HTTP Client 插件已加载")

    @filter.command("http")
    async def http_request(self, event: AstrMessageEvent):
        """
        发起自定义HTTP请求。
        用法：/http <METHOD> <URL> [headers_json] [body_json]
        示例：
          /http GET https://api.github.com
          /http POST https://httpbin.org/post {"Content-Type":"application/json"} {"key":"value"}
        """
        # 解析用户输入
        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result(
                "❌ 用法错误！\n"
                "格式：/http <METHOD> <URL> [headers_json] [body_json]\n"
                "示例：\n"
                "  /http GET https://api.github.com\n"
                "  /http POST https://httpbin.org/post {\"Content-Type\":\"application/json\"} {\"key\":\"value\"}"
            )
            return

        # 进一步解析参数
        args = parts[1].split(maxsplit=3)
        if len(args) < 2:
            yield event.plain_result("❌ 请提供 METHOD 和 URL")
            return

        method = args[0].upper()
        url = args[1]
        headers = {}
        body = None

        # 解析可选的 headers（第3个参数）
        if len(args) >= 3:
            try:
                headers = json.loads(args[2])
            except json.JSONDecodeError:
                yield event.plain_result(f"❌ headers 格式错误，请传入有效的 JSON：{args[2]}")
                return

        # 解析可选的 body（第4个参数）
        if len(args) >= 4:
            try:
                body = json.loads(args[3])
            except json.JSONDecodeError:
                yield event.plain_result(f"❌ body 格式错误，请传入有效的 JSON：{args[3]}")
                return

        # 发送请求
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=body, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=body, headers=headers)
                elif method == "PATCH":
                    response = await client.patch(url, json=body, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    yield event.plain_result(f"❌ 不支持的 HTTP 方法：{method}")
                    return

                response.raise_for_status()

                # 尝试解析响应为 JSON，否则返回纯文本
                try:
                    resp_data = response.json()
                    resp_text = json.dumps(resp_data, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    resp_text = response.text

                # 截断过长的响应
                if len(resp_text) > 1500:
                    resp_text = resp_text[:1500] + "\n... (截断)"

                result = (
                    f"✅ 请求成功！\n"
                    f"状态码: {response.status_code}\n"
                    f"响应内容:\n{resp_text}"
                )
                yield event.plain_result(result)

        except httpx.TimeoutException:
            yield event.plain_result("❌ 请求超时，请检查目标服务器是否可达")
        except httpx.HTTPStatusError as e:
            yield event.plain_result(f"❌ HTTP 错误: {e.response.status_code}\n{e.response.text[:500]}")
        except Exception as e:
            logger.error(f"HTTP请求异常: {e}")
            yield event.plain_result(f"❌ 请求失败: {str(e)}")

    async def terminate(self):
        """插件卸载/停用时调用"""
        logger.info("HTTP Client 插件已卸载")
