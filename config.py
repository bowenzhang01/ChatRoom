# -*- coding: utf-8 -*-
"""
Dorm Life - 全局配置与环境变量
  所有模块通过 `import config` 访问配置，使用 `config.API_KEY = xxx` 修改。
"""

import os
from pathlib import Path

from kivy.core.text import LabelBase

from utils import load_json

# ═══ 路径常量 ═══
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = BASE_DIR / "profiles"

# ═══ 字体注册 ═══
FONT_DEFAULT = 'Roboto'
FONT_SC = BASE_DIR / "NotoSansSC-Regular.ttf"

if FONT_SC.exists():
    LabelBase.register(name="Roboto", fn_regular=str(FONT_SC))

# ═══ 全局 JSON 配置（跨剧本共享的 API / App 设置）═══
app_config = load_json(BASE_DIR / "config.json")


def resolve_key():
    k = app_config.get("model", {}).get("api_key", "")
    if k:
        return k
    k = os.environ.get("DEEPSEEK_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    if k:
        return k
    return ""


# ═══ 模块级导出（方便跨文件访问，修改时直接赋值 config.XXX = ...）═══
API_KEY = resolve_key()
MC = app_config.get("model", {})
API_BASE = MC.get("api_base", "https://api.deepseek.com")
MODEL = MC.get("model", "deepseek-chat")
MODELS_LIST = MC.get("models", [])
TEMPERATURE = MC.get("temperature", 0.85)
MAX_TOKENS = MC.get("max_tokens", 300)
ACTIVE_PROFILE = app_config.get("active_profile", "dorm_girls")
