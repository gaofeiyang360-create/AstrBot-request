import json
import httpx
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.tool import register_llm_tool


@register("astrbot_plugin_http_tool", "YourName", "为AI提供HTTP请求能力的工具插件", "1.0.0")
class HttpToolPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("HTTP Tool 插件已加载")

    @register_llm_tool(
        name="http_request",
        description="向指定的URL发起HTTP请求，支持GET、POST、PUT、PATCH、DELETE方法。可以携带自定义请求头和JSON请求体。",
        parameters=[
            {
                "name": "method",
                "type": "string",
                "description": "HTTP方法，可选值：GET, POST, PUT, PATCH, DELETE",
                "required": True
            },
            {
                "name": "url",
                "type": "string",
                "description": "目标URL（完整地址）",
                "required": True
            },
            {
                "name": "headers",
                "type": "string",
                "description": "请求头，JSON格式字符串，例如 {\"Authorization\": \"Bearer token\"}",
                "required": False
            },
            {
                "name": "body",
                "type": "string",
                "description": "请求体，JSON格式字符串，例如 {\"key\": \"value\"}。仅在POST/PUT/PATCH时有效",
                "required": False
            }
        ]
    )
    async def http_request(self, method: str, url: str, headers: str = "{}", body: str = "{}") -> str:
        """
        AI调用的HTTP请求工具
        """
        try:
            headers_dict = json.loads(headers)
            body_dict = json.loads(body) if body else None

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

                # 截断过长内容
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
