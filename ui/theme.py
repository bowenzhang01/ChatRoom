# -*- coding: utf-8 -*-
"""
Dorm Life — 统一主题系统
  移动端优先（Android），所有颜色/间距/字号/圆角在此集中管理。
  使用方式: from ui.theme import theme
"""

from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Rectangle

__all__ = ["theme", "draw_shadow"]


class Theme:
    """移动端优先的主题令牌集合"""

    # ═══ 基础色板 ═══
    WHITE           = "#ffffff"
    PINK_400        = "#ff9a9e"
    PINK_500        = "#e91e63"
    PINK_50         = "#fce4ec"
    GREEN_400       = "#66bb6a"
    GREEN_700       = "#388e3c"
    ORANGE_400      = "#ffa726"
    RED_400         = "#ef5350"
    RED_800         = "#c62828"
    BLUE_400        = "#42a5f5"
    BLUE_600        = "#1e88e5"
    TEAL_800        = "#00695c"
    PURPLE_400      = "#ab47bc"
    PURPLE_300      = "#ce93d8"
    GRAY_50         = "#fafafa"
    GRAY_100        = "#f5f5f5"
    GRAY_200        = "#eeeeee"
    GRAY_300        = "#e0e0e0"
    GRAY_400        = "#bdbdbd"
    GRAY_500        = "#9e9e9e"
    GRAY_600        = "#757575"
    GRAY_700        = "#616161"
    GRAY_800        = "#424242"
    GRAY_900        = "#212121"

    # ═══ 语义色 ═══
    @property
    def primary(self):       return self.PINK_400
    @property
    def primary_dark(self):  return self.PINK_500
    @property
    def primary_light(self): return self.PINK_50

    @property
    def accent(self):        return self.GREEN_400
    @property
    def accent_dark(self):   return self.GREEN_700

    @property
    def warning(self):       return self.ORANGE_400
    @property
    def danger(self):        return self.RED_400
    @property
    def info(self):          return self.BLUE_400
    @property
    def purple(self):        return self.PURPLE_400

    # ═══ 背景/表面 ═══
    @property
    def window_bg(self):     return "#fff8f5"
    @property
    def surface(self):       return self.WHITE
    @property
    def surface_alt(self):   return "#f5eeeb"
    @property
    def scene_bg(self):      return "#fff3e0"
    @property
    def input_bg(self):      return "#e8f5e9"
    @property
    def card_bg(self):       return self.WHITE

    # ═══ 文字色 ═══
    @property
    def text_primary(self):   return self.GRAY_900
    @property
    def text_secondary(self): return self.GRAY_700
    @property
    def text_hint(self):      return "#5c4a46"
    @property
    def text_on_primary(self): return self.WHITE
    @property
    def text_on_accent(self):  return self.WHITE
    @property
    def text_muted(self):      return self.GRAY_500

    # ═══ 聊天气泡 ═══
    @property
    def bubble_left_bg(self):   return self.GRAY_300
    @property
    def bubble_left_text(self): return self.GRAY_900
    @property
    def bubble_right_bg(self):  return self.BLUE_600
    @property
    def bubble_right_text(self): return self.WHITE
    @property
    def bubble_director_label(self): return self.TEAL_800

    # ═══ 阴影 ═══
    @property
    def shadow_color(self): return (0, 0, 0, 0.08)

    # ═══ 间距 (dp) ═══
    @property
    def spacing_xs(self):  return dp(2)
    @property
    def spacing_sm(self):  return dp(4)
    @property
    def spacing_md(self):  return dp(8)
    @property
    def spacing_lg(self):  return dp(12)
    @property
    def spacing_xl(self):  return dp(16)
    @property
    def spacing_xxl(self): return dp(24)

    # ═══ 圆角 (dp) ═══
    @property
    def radius_sm(self): return dp(4)
    @property
    def radius_md(self): return dp(8)
    @property
    def radius_lg(self): return dp(12)
    @property
    def radius_xl(self): return dp(16)
    @property
    def radius_full(self): return dp(999)

    # ═══ 字号 (dp → sp) ═══
    @property
    def font_xs(self):    return dp(9)
    @property
    def font_sm(self):    return dp(10)
    @property
    def font_body(self):  return dp(12)
    @property
    def font_sub(self):   return dp(14)
    @property
    def font_title(self): return dp(16)
    @property
    def font_h1(self):    return dp(20)

    # ═══ 触摸目标 ═══
    @property
    def touch_min(self): return dp(44)

    # ═══ 布局尺寸 ═══
    @property
    def toolbar_h(self):    return dp(48)
    @property
    def modebar_h(self):    return dp(34)
    @property
    def controls_h(self):   return dp(48)
    @property
    def statusbar_h(self):  return dp(28)
    @property
    def tabbar_h(self):     return dp(36)
    @property
    def btn_h(self):        return dp(36)
    @property
    def btn_h_lg(self):     return dp(44)


theme = Theme()


def draw_shadow(widget, radius=dp(8), opacity=0.08, offset_y=dp(-2)):
    """在 widget 的 canvas.before 绘制一层投影。
    用法: draw_shadow(some_widget, radius=dp(12))
    返回 (shadow_color, shadow_rect) 元组，供后续 bind 更新用。"""
    from kivy.graphics import Color, RoundedRectangle

    with widget.canvas.before:
        c = Color(0, 0, 0, opacity)
        r = RoundedRectangle(
            pos=(widget.x + dp(1), widget.y + offset_y),
            size=(widget.size[0] - dp(2), widget.size[1] + dp(2)),
            radius=[radius, radius, radius, radius],
        )

    widget.bind(
        pos=lambda obj, val: setattr(r, "pos", (val[0] + dp(1), val[1] + offset_y)),
        size=lambda obj, val: setattr(r, "size", (val[0] - dp(2), val[1] + dp(2))),
    )

    return c, r
