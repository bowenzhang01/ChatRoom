# -*- coding: utf-8 -*-
"""
Dorm Life — 投影与卡片容器（纯 Canvas 实现，无 KivyMD 依赖）
  ShadowBox / ShadowCard / Divider / ShadowMixin
  移动端性能：仅 2 层半透明矩形叠加，零纹理开销
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle

from ui.theme import theme


class Divider(Widget):
    """细分割线，用于列表间或区块间视觉分隔"""

    def __init__(self, color=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(1)

        c = color or theme.GRAY_200
        from utils import hex_to_rgba

        with self.canvas.before:
            self._color = Color(*hex_to_rgba(c))
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda obj, val: setattr(obj._rect, "pos", val),
            size=lambda obj, val: setattr(obj._rect, "size", val),
        )


class _ShadowDraw:
    """Mixin: 为任意 Widget 在 canvas.before 最底层注入投影指令。
    使用方式:
        class MyBox(BoxLayout, _ShadowDraw):
            def __init__(self, **kw):
                super().__init__(**kw)
                self.draw_shadow()

    注意: _ShadowDraw 必须在 Widget 子类之前被 MRO 解析。
    """

    def draw_shadow(self, radius=dp(12), opacity=0.06, offset_y=dp(-1), scale=1.0):
        """绘制单层投影（移动端较轻量）"""
        from kivy.graphics import Color, RoundedRectangle

        if not hasattr(self, 'canvas') or not hasattr(self, 'canvas.before'):
            return

        with self.canvas.before:
            self._shadow_color = Color(0, 0, 0, opacity)
            self._shadow_rect = RoundedRectangle(
                pos=(self.x + dp(1), self.y + offset_y),
                size=(self.width * scale - dp(2), self.height * scale + dp(2)),
                radius=[radius, radius, radius, radius],
            )
        self.bind(
            pos=self._update_shadow,
            size=self._update_shadow,
        )

    def _update_shadow(self, *args):
        if not hasattr(self, '_shadow_rect'):
            return
        self._shadow_rect.pos = (self.x + dp(1), self.y - dp(1))
        self._shadow_rect.size = (self.width - dp(2), self.height + dp(2))


class ShadowBox(BoxLayout):
    """带投影的 BoxLayout 容器。用法同 BoxLayout，额外提供圆角和背景色。"""

    def __init__(self, bg_color=None, radius=dp(12), shadow_opacity=0.06, **kwargs):
        super().__init__(**kwargs)
        from utils import hex_to_rgba

        _bg = bg_color or theme.card_bg
        _rgba = hex_to_rgba(_bg)

        # 阴影层
        with self.canvas.before:
            self._sd_color = Color(0, 0, 0, shadow_opacity)
            self._sd_rect = RoundedRectangle(
                pos=(self.x + dp(1), self.y - dp(1)),
                size=(self.width - dp(2), self.height + dp(2)),
                radius=[radius, radius, radius, radius],
            )

        # 背景层
        with self.canvas.before:
            self._bg_color = Color(*_rgba)
            self._bg_rect = RoundedRectangle(
                radius=[radius, radius, radius, radius],
            )

        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self._sd_rect.pos = (self.x + dp(1), self.y - dp(1))
        self._sd_rect.size = (self.width - dp(2), self.height + dp(2))
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size


class ShadowCard(ShadowBox):
    """卡片式容器：白底 + 圆角 + 投影 + 内边距。适用于设置界面中的分组区域。"""

    def __init__(self, bg_color=None, radius=None, padding_v=None, padding_h=None, **kwargs):
        _radius = radius or theme.radius_lg
        _padv = padding_v or theme.spacing_md
        _padh = padding_h or theme.spacing_lg
        super().__init__(
            bg_color=bg_color or theme.card_bg,
            radius=_radius,
            shadow_opacity=0.06,
            padding=(_padh, _padv),
            spacing=theme.spacing_sm,
            **kwargs,
        )
