from langchain_community.chat_models import ChatTongyi
from langchain_openai import ChatOpenAI
import os


def get_llm(provider="tongyi", model="qwen-turbo", **kwargs):
    """
    Returns an instance of the specified chat model provider with tool support.
    """
    # print(f"创建 LLM: provider={provider}, model={model}")

    if provider == "tongyi":
        api_key = kwargs.get("api_key") or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 未设置")

        # 通义千问模型支持工具调用
        llm = ChatTongyi(
            model_name=model,
            dashscope_api_key=api_key,
            temperature=kwargs.get("temperature", 0.3),
            streaming=kwargs.get("streaming", False),
        )

        # 验证模型是否支持工具调用
        # if hasattr(llm, 'bind_tools'):
        #     print(f"✅ {model} 支持工具调用")
        # else:
        #     print(f"⚠️ {model} 可能不支持工具调用，将使用基础模式")

        return llm

    elif provider == "openai" or provider == "deepseek":
        # 支持 OpenAI 或兼容 OpenAI 接口的模型（如 DeepSeek）
        api_key = kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        base_url = kwargs.get("base_url") or os.environ.get("OPENAI_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL")

        # 过滤出 ChatOpenAI 支持的参数
        openai_params = {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
            "temperature": kwargs.get("temperature", 0.3),
            "streaming": kwargs.get("streaming", False),
        }

        # 可选：添加其他 ChatOpenAI 支持的参数（如果需要）
        if "max_tokens" in kwargs:
            openai_params["max_tokens"] = kwargs["max_tokens"]
        if "timeout" in kwargs:
            openai_params["timeout"] = kwargs["timeout"]
        if "max_retries" in kwargs:
            openai_params["max_retries"] = kwargs["max_retries"]
        # 注意：proxies 参数不会被传递，因为它不在支持的参数列表中

        return ChatOpenAI(**openai_params)

    else:
        # 默认返回通义千问
        return ChatTongyi(
            model_name="qwen-turbo",
            dashscope_api_key=kwargs.get("api_key"),
            temperature=kwargs.get("temperature", 0.3),
        )