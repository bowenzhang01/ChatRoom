# -*- coding: utf-8 -*-
"""
Dorm Life - 基础 UI 控件 (v2.0 主题增强版)
  StatusDot / RoundedButton / ColoredButton / FitSpinner / ScrollDropdown
  增强: 主题令牌引用 + 阴影 + 按钮缩放动画 + 呼吸灯
"""

from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.spinner import Spinner
from kivy.uix.dropdown import DropDown
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import hex_to_rgba
from ui.theme import theme, draw_shadow

# ═══════════════════════════════════════════════
#  Custom Widgets
# ═══════════════════════════════════════════════

class StatusDot(Widget):
    """圆形状态指示灯 (v2.0: 支持呼吸动画)"""
    def __init__(self, color=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(13), dp(13))
        self._breathe_cancel = None

        c = color or hex_to_rgba(theme.accent)
        with self.canvas:
            self._color = Color(*c)
            self._ellipse = Ellipse(pos=(self.x + dp(3), self.y + dp(3)),
                                     size=(dp(7), dp(7)))

    def set_color(self, color):
        if isinstance(color, str):
            color = hex_to_rgba(color)
        self._color.rgba = color

    def on_pos(self, *args):
        self._ellipse.pos = (self.x + dp(3), self.y + dp(3))

    def start_breathe(self):
        from ui.animations import breathe
        if self._breathe_cancel:
            self._breathe_cancel()
        self._breathe_cancel = breathe(self)

    def stop_breathe(self):
        if self._breathe_cancel:
            self._breathe_cancel()
            self._breathe_cancel = None
        self.opacity = 1.0


class RoundedButton(Button):
    """圆角按钮基类 — v2.0: 主题令牌 + 可选投影 + 按压变色"""
    def __init__(self, btn_color=None, radius=None, shadow=False, **kwargs):
        super().__init__(**kwargs)
        self._btn_color = btn_color or theme.GRAY_500
        self._radius = radius or theme.radius_md
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.font_name = config.FONT_DEFAULT
        self.bold = True

        self._normal_rgba = hex_to_rgba(self._btn_color)

        if shadow:
            self._sd_color, self._sd_rect = draw_shadow(self, radius=self._radius)

        with self.canvas.before:
            from kivy.graphics import Color as GColor, RoundedRectangle
            self._bg_color = GColor(*self._normal_rgba)
            self._bg_rect = RoundedRectangle(
                radius=[self._radius, self._radius, self._radius, self._radius]
            )
        self.bind(pos=self._update_bg, size=self._update_bg, state=self._on_press_state)

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def set_bg_color(self, color):
        if isinstance(color, str):
            color = hex_to_rgba(color)
        self._btn_color = color
        self._normal_rgba = color
        self._bg_color.rgba = color

    def get_bg_color(self):
        return self._btn_color

    @staticmethod
    def _darken(hex_color_val, factor):
        h = hex_color_val.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r, g, b = int(r * factor), int(g * factor), int(b * factor)
            return f"#{r:02x}{g:02x}{b:02x}"
        return hex_color_val

    def _on_press_state(self, instance, state):
        if state == "down":
            r, g, b, a = self._normal_rgba
            self._bg_color.rgba = (r * 0.78, g * 0.78, b * 0.78, a)
        else:
            self._bg_color.rgba = self._normal_rgba


class ColoredButton(RoundedButton):
    """v2.0: 圆角按钮 + 颜色变暗按压动画 + 投影"""
    def __init__(self, btn_color=None, shadow=True, **kwargs):
        _color = btn_color or theme.accent
        super().__init__(btn_color=_color, radius=theme.radius_md, shadow=shadow, **kwargs)
        self._normal_color = _color
        self._pressed_color = self._darken(_color, 0.78)
        self.color = (1, 1, 1, 1)
        self.font_size = dp(12)
        self.size_hint_y = None
        self.height = dp(40)
        self.bind(size=self._update_padding)

    def _update_padding(self, *args):
        self.padding = (dp(8), dp(6))

    def _on_press_state(self, instance, state):
        if state == "down":
            self._bg_color.rgba = hex_to_rgba(self._pressed_color)
        else:
            self._bg_color.rgba = hex_to_rgba(self._normal_color)

    def set_btn_color(self, color):
        self._normal_color = color if isinstance(color, str) else color
        self._pressed_color = self._darken(self._normal_color, 0.78)
        self._normal_rgba = hex_to_rgba(self._normal_color)
        if hasattr(self, '_bg_color'):
            self._bg_color.rgba = self._normal_rgba


class FitSpinnerOption(Button):
    """下拉选项：文本过长时自动换行，自适应高度"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.halign = 'left'
        self.valign = 'middle'
        self.font_size = dp(11)
        self.padding = [dp(10), dp(8)]
        self.size_hint_y = None
        self.bind(parent=self._on_parent)

    def _on_parent(self, widget, parent):
        if parent is not None:
            parent.bind(width=self._update_text_size)

    def _update_text_size(self, dropdown, width):
        self.text_size = (max(0, width - dp(20)), None)
        self.height = self.texture_size[1] + dp(16)


class ScrollDropdown(DropDown):
    """带最大高度的下拉框"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_height = dp(400)


class FitSpinner(Spinner):
    """自适应 Spinner — v2.0: 增加圆角 + 主题色"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shorten = True
        self.shorten_from = 'right'
        self.halign = 'center'
        self.valign = 'middle'

        if not self.background_normal:
            self.background_normal = ""
        if self.background_color in (None, (1, 1, 1, 1)):
            self.background_color = hex_to_rgba(theme.surface)

        self.bind(size=self._on_spinner_size)

    def _on_spinner_size(self, *args):
        self.text_size = (max(0, self.width - dp(24)), None)
