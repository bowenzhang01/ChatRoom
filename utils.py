# -*- coding: utf-8 -*-
"""
Dorm Life - 纯工具函数（无状态）
  load_json / save_json / hex_to_rgba / extract_json / make_popup_label
"""

import json
import re as _re
from pathlib import Path

from kivy.metrics import dp
from kivy.uix.label import Label
import config


def load_json(path):
    """接受 Path 对象或字符串，返回解析后的 JSON"""
    p = Path(path) if not isinstance(path, Path) else path
    if not p.exists():
        return {} if "config" in str(p) else []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    """安全写入 JSON（自动创建父目录）"""
    p = Path(path) if not isinstance(path, Path) else path
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存失败: {p} - {e}")
        return False


def hex_to_rgba(h, a=1.0):
    """hex 颜色字符串 → (r, g, b, a) 浮点元组"""
    h = h.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
        return (r, g, b, a)
    return (1, 1, 1, 1)


def extract_json(text: str):
    """从 AI 返回文本中提取 JSON，处理 markdown 代码块和常见格式错误。
    返回 (dict|None, error_msg|None)"""
    if not text or not text.strip():
        return None, "AI返回为空"
    # Step 0: 移除 DeepSeek R1 等模型的 <think>...</think> 思考标签
    text = _re.sub(r'<think>[\s\S]*?</think>', '', text)
    text = text.strip()
    if not text:
        return None, "AI返回为空（仅含思考标签）"
    # Step 1: 提取 markdown 代码块
    m = _re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, _re.DOTALL)
    if m:
        text = m.group(1).strip()
    # Step 2: 找最外层 { ... } 或 [ ... ]
    m = _re.search(r'\{[\s\S]*\}', text)
    if m:
        text = m.group(0)
    else:
        m = _re.search(r'\[[\s\S]*\]', text)
        if m:
            text = m.group(0)
    # Step 3: 尝试直接解析
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result, None
    except json.JSONDecodeError:
        pass
    # Step 4: 修复常见错误后重试
    try:
        fixed = _re.sub(r',\s*([}\]])', r'\1', text)  # 去除尾部多余逗号
        return json.loads(fixed), None
    except json.JSONDecodeError:
        pass
    # Step 5: 尝试用 json5 宽松解析（如果可用）
    try:
        import json5
        result = json5.loads(text)
        if isinstance(result, dict):
            return result, None
    except Exception:
        pass
    return None, "JSON解析失败"


def make_popup_label(text, **kwargs):
    """创建带 text_size 绑定的 Label，确保多行文字正确换行。
    适用于弹窗中的消息 Label（替代普通 Label）。"""
    lbl = Label(
        text=text,
        font_name=config.FONT_DEFAULT,
        **kwargs,
    )
    lbl.bind(width=lambda inst, val: setattr(inst, 'text_size', (max(0, val - dp(16)), None)))
    return lbl
