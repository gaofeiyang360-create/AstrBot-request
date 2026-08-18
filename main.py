import json
import httpx
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger

@register("astrbot_plugin_http_tool", "YourName", "HTTP请求工具插件（AI可调用）", "1.0.0")
class HttpToolPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("HTTP Tool 插件已加载")

    @filter.llm_tool(name="http_request")
    async def http_request(self, event: AstrMessageEvent, method: str, url: str, headers: str = "{}", body: str = "{}"):
        """
        向指定的URL发起HTTP请求，支持GET、POST、PUT、PATCH、DELETE方法。
        
        AI调用示例：
            GET请求：method="GET", url="https://api.github.com"
            POST请求：method="POST", url="https://httpbin.org/post", headers='{"Content-Type":"application/json"}', body='{"name":"test"}'
        
        参数说明（这些信息会自动传递给AI，AI会根据用户意图自动生成）：
            - method (string, 必填): HTTP方法，可选值: GET, POST, PUT, PATCH, DELETE
            - url (string, 必填): 完整的请求URL
            - headers (string, 可选): JSON格式的请求头，例如 {"Authorization": "Bearer token"}
            - body (string, 可选): JSON格式的请求体，仅在 POST/PUT/PATCH 时有效
        """
        try:
            # 解析headers和body
            headers_dict = json.loads(headers) if headers else {}
            body_dict = json.loads(body) if body and body != "{}" else None

            async with httpx.AsyncClient(timeout=30.0) as client:
                method_upper = method.upper()

                if method_upper == "GET":
                    resp = await client.get(url, headers=headers_dict)
                elif method_upper == "POST":
                    resp = await client.post(url, json=body_dict, headers=headers_dict)
                elif method_upper == "PUT":
                    resp = await client.put(url, json=body_dict, headers=headers_dict)
                elif method_upper == "PATCH":
                    resp = await client.patch(url, json=body_dict, headers=headers_dict)
                elif method_upper == "DELETE":
                    resp = await client.delete(url, headers=headers_dict)
                else:
                    return f"❌ 不支持的HTTP方法: {method}"

                resp.raise_for_status()

                # 尝试解析JSON响应
                try:
                    data = resp.json()
                    response_text = json.dumps(data, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    response_text = resp.text

                # 截断过长内容（避免消息爆炸）
                if len(response_text) > 2000:
                    response_text = response_text[:2000] + "\n... (响应过长，已截断)"

                return f"✅ 请求成功\n状态码: {resp.status_code}\n响应内容:\n{response_text}"

        except httpx.TimeoutException:
            return "❌ 请求超时，请检查网络或目标服务器"
        except httpx.HTTPStatusError as e:
            return f"❌ HTTP错误 {e.response.status_code}\n{e.response.text[:500]}"
        except json.JSONDecodeError as e:
            return f"❌ 参数JSON解析失败: {str(e)}"
        except Exception as e:
            logger.error(f"HTTP Tool 异常: {e}")
            return f"❌ 请求失败: {str(e)}"

    async def terminate(self):
        logger.info("HTTP Tool 插件已卸载")
