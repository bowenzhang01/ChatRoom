# -*- coding: utf-8 -*-
"""
Dorm Life - API 服务层
  封装所有 LLM HTTP 请求：chat completion / model list fetch
  支持同步和异步（后台线程）两种调用方式
"""

import threading
from typing import Callable, Optional

import httpx
from kivy.clock import Clock, mainthread

import config
from utils import extract_json


# ── 通用错误类 ──

class APIError(Exception):
    """API 调用错误，携带人类可读消息"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _parse_error(e: Exception) -> str:
    """解析 HTTP/网络异常，返回人类可读消息"""
    msg = str(e)
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401:
            return "API Key 无效，请检查设置"
        elif code == 403:
            return "API 访问被拒绝，请检查 Key 权限"
        elif code == 429:
            return "API 请求太频繁，请稍后重试"
        elif code >= 500:
            return f"API 服务器错误 (HTTP {code})"
        else:
            return f"API 请求失败 (HTTP {code})"
    if "timed out" in msg.lower() or "timeout" in msg.lower():
        return "连接 API 超时，请检查网络"
    if "connection" in msg.lower() or "refused" in msg.lower():
        return "无法连接 API 服务器，请检查网络和地址"
    if "name resolution" in msg.lower() or "getaddrinfo" in msg.lower():
        return "无法解析 API 服务器地址"
    return msg[:120]


# ── 核心 API 函数 ──

def call_chat_completion(
    messages: list,
    model: str = None,
    api_key: str = None,
    api_base: str = None,
    temperature: float = None,
    max_tokens: int = None,
    timeout: float = 30.0,
) -> str:
    """同步调用 LLM chat completion，返回响应文本。
    
    Args:
        messages: [{"role":"system","content":...}, {"role":"user","content":...}]
        model: 模型名，默认用 config.MODEL
        api_key: API Key，默认用 config.API_KEY
        api_base: API 地址，默认用 config.API_BASE
        temperature: 温度参数
        max_tokens: 最大 token 数
        timeout: 超时秒数
    
    Returns:
        LLM 返回的纯文本
    
    Raises:
        APIError: HTTP 或网络错误
    """
    if model is None:
        model = config.MODEL
    if api_key is None:
        api_key = config.API_KEY
    if api_base is None:
        api_base = config.API_BASE
    if temperature is None:
        temperature = config.TEMPERATURE
    if max_tokens is None:
        max_tokens = config.MAX_TOKENS

    if not api_key:
        raise APIError("未配置 API Key")

    try:
        with httpx.Client(timeout=timeout, verify=False, trust_env=False) as client:
            r = client.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        raise APIError(_parse_error(e), e.response.status_code)
    except Exception as e:
        raise APIError(_parse_error(e))


def call_chat_completion_async(
    messages: list,
    on_result: Callable[[str], None],
    on_error: Callable[[str], None] = None,
    model: str = None,
    api_key: str = None,
    api_base: str = None,
    temperature: float = 0.7,
    max_tokens: int = 800,
    timeout: float = 30.0,
):
    """后台线程异步调用 LLM，通过主线程回调返回结果。
    
    Args:
        messages: 同 call_chat_completion
        on_result: 成功回调 on_result(response_text)，在主线程执行
        on_error: 失败回调 on_error(error_message)，在主线程执行
        其他参数: 同 call_chat_completion
    """
    if api_key is None:
        api_key = config.API_KEY

    def _run():
        try:
            result = call_chat_completion(
                messages=messages,
                model=model,
                api_key=api_key,
                api_base=api_base,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            if on_result:
                Clock.schedule_once(lambda dt: on_result(result), 0)
        except APIError as e:
            if on_error:
                Clock.schedule_once(lambda dt: on_error(str(e)), 0)
        except Exception as e:
            if on_error:
                Clock.schedule_once(lambda dt: on_error(_parse_error(e)), 0)

    threading.Thread(target=_run, daemon=True).start()


def fetch_models(
    api_key: str = None,
    api_base: str = None,
    timeout: float = 15.0,
) -> list:
    """获取可用模型列表。
    
    Returns:
        模型 ID 列表（如 ["deepseek-chat", "deepseek-reasoner"]）
    
    Raises:
        APIError: 请求失败
    """
    if api_key is None:
        api_key = config.API_KEY
    if api_base is None:
        api_base = config.API_BASE

    try:
        with httpx.Client(timeout=timeout, verify=False, trust_env=False) as client:
            r = client.get(
                f"{api_base}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            return [m.get("id", "") for m in r.json().get("data", [])]
    except httpx.HTTPStatusError as e:
        raise APIError(_parse_error(e), e.response.status_code)
    except Exception as e:
        raise APIError(_parse_error(e))
