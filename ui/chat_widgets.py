# -*- coding: utf-8 -*-
"""
Dorm Life - 聊天流 UI 控件 (v2.0 增强版)
  parse_markdown_to_kivy_markup / BubbleLabel (含尾巴) / ChatMessageRow (入场动画) / ChatView
"""

import re

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import hex_to_rgba
from ui.theme import theme


def parse_markdown_to_kivy_markup(text):
    if not text:
        return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'[b]\1[/b]', text)
    text = re.sub(r'\*(.*?)\*', r'[color=#8a8a8a]\1[/color]', text)
    return text


class BubbleLabel(Label):
    """自适应圆角聊天气泡标签 — v2.0"""

    def __init__(self, text, is_right, **kwargs):
        super().__init__(**kwargs)
        self.markup = True
        self.text = parse_markdown_to_kivy_markup(text)
        self._is_right = is_right

        self.font_name = config.FONT_DEFAULT
        self.font_size = theme.font_sub
        self.size_hint = (None, None)
        self.halign = 'left'
        self.valign = 'middle'

        self.color = hex_color(theme.bubble_right_text) if is_right else hex_color(theme.bubble_left_text)
        bg_rgba = hex_color(theme.bubble_right_bg) if is_right else hex_color(theme.bubble_left_bg)

        if is_right:
            self.text = self.text.replace("[color=#8a8a8a]", "[color=#bbdefb]")

        self.max_bubble_width = Window.width * 0.65
        self.text_size = (self.max_bubble_width, None)

        def _on_window_resize(win, width, height):
            self.max_bubble_width = width * 0.65
            self.text_size = (self.max_bubble_width, None)
        Window.bind(on_resize=_on_window_resize)
        self._win_resize_cb = _on_window_resize
        self.bind(parent=self._on_bubble_parent)

        self.bind(texture_size=self._on_texture_size)

        with self.canvas.before:
            Color(*bg_rgba)
            self.rect = RoundedRectangle(radius=[theme.radius_lg] * 4)

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _on_texture_size(self, instance, size):
        self.width = size[0] + dp(26)
        self.height = size[1] + dp(16)

    def _on_bubble_parent(self, widget, parent):
        if parent is None:
            Window.unbind(on_resize=self._win_resize_cb)

    def _update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ChatMessageRow(BoxLayout):
    """聊天气泡行 — v2.0: 新消息入场动画"""
    def __init__(self, name, dname, text, t, msg_type="normal", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.padding = [theme.spacing_lg, theme.spacing_sm]
        self.spacing = theme.spacing_md
        self._export_dname = "导演" if msg_type == "director" else dname
        self._export_text = text
        self._export_time = t

        is_right = (name == "You" and msg_type != "director") or msg_type == "director"

        bubble = BubbleLabel(text=text, is_right=is_right)

        if msg_type == "director":
            name_text = f"[b]导演[/b]  {t}"
            name_color = hex_color(theme.bubble_director_label)
        else:
            name_text = f"[b]{dname}[/b]  {t}"
            _app = App.get_running_app()
            st = _app.char_styles.get(name, {}) if _app else {}
            name_color = hex_color(st.get("color", "#888"))

        name_lbl = Label(
            text=name_text,
            font_name=config.FONT_DEFAULT,
            markup=True,
            font_size=theme.font_sm,
            color=name_color,
            size_hint=(None, None),
            height=dp(16),
        )

        v_box = BoxLayout(orientation='vertical', size_hint=(None, None), spacing=dp(3))
        name_lbl.bind(width=lambda inst, val: setattr(name_lbl, 'text_size', (val, None)))
        v_box.add_widget(name_lbl)
        v_box.add_widget(bubble)

        def update_vbox_size(*args):
            v_box.width = bubble.width
            v_box.height = name_lbl.height + v_box.spacing + bubble.height
            name_lbl.width = bubble.width
        bubble.bind(size=update_vbox_size)

        if is_right:
            name_lbl.halign = 'right'
            self.add_widget(Widget(size_hint_x=1))
            self.add_widget(v_box)
        else:
            name_lbl.halign = 'left'
            self.add_widget(v_box)
            self.add_widget(Widget(size_hint_x=1))

        v_box.bind(height=lambda inst, val: setattr(self, 'height', val + dp(8)))

        self.opacity = 0
        self._anim_scheduled = False
        self.bind(parent=self._schedule_entrance)

    def _schedule_entrance(self, *args):
        if self.parent and not self._anim_scheduled:
            self._anim_scheduled = True
            Clock.schedule_once(self._do_entrance, 0.03)

    def _do_entrance(self, dt):
        from ui.animations import fade_in
        fade_in(self, duration=0.22)


class ChatView(ScrollView):
    """聊天滚动视图 — v2.0: 美化的滚动条"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(0),
            padding=(0, dp(8), 0, dp(24)),
        )
        self.container.bind(minimum_height=self.container.setter("height"))
        self.add_widget(self.container)
        self.bar_width = dp(4)
        self.bar_color = hex_to_rgba(theme.primary)
        self.bar_inactive_color = hex_to_rgba(theme.GRAY_200)
        self.scroll_type = ['bars', 'content']
        self.effect_cls = 'ScrollEffect'
        self._spacer = Widget(size_hint_y=None, height=0)
        self.container.add_widget(self._spacer)
        self.bind(size=self._update_spacer)
        self.container.bind(height=self._update_spacer)

    def _update_spacer(self, *args):
        real = self.container.height - self._spacer.height
        target = max(0, self.height - real)
        was_not_full = self._spacer.height > 0
        if abs(self._spacer.height - target) > 0.5:
            self._spacer.height = target
        if was_not_full and target == 0:
            self._scroll_to_bottom()

    def add_message(self, name, dname, text, t, color, msg_type="normal"):
        should_track = (self.scroll_y <= 0.1 or self._spacer.height > 0)
        row = ChatMessageRow(
            name=name, dname=dname, text=text, t=t,
            msg_type=msg_type,
        )
        self.container.add_widget(row)
        if len(self.container.children) > 301:
            oldest = self.container.children[-2]
            if oldest is not self._spacer and hasattr(oldest, '_export_text'):
                self.container.remove_widget(oldest)
        if should_track:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        def do_scroll(dt):
            self.scroll_y = 0
        Clock.schedule_once(do_scroll, 0.02)

    def clear(self):
        self.container.clear_widgets()
        self.container.add_widget(self._spacer)
        self._spacer.height = 0

    def get_all_text(self):
        lines = []
        for msg in self.container.children[-1::-1]:
            if hasattr(msg, "_export_text"):
                lines.append(f"{msg._export_dname}  {msg._export_time}\n{msg._export_text}")
        return "\n\n".join(lines)
