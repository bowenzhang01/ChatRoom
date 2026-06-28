# -*- coding: utf-8 -*-
"""SettingsPopup — 剧本/世界管理 Tab"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import hex_to_rgba
from ui.base_widgets import RoundedButton
from ui.theme import theme


class WorldTabMixin:
    """剧本/世界管理 Tab — 标题、欢迎文字、世界观、发言顺序"""

    def _build_world_tab(self):
        box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box_scroll = ScrollView(size_hint=(1, 1))
        box_scroll.add_widget(box)

        box.add_widget(Label(
            text="应用标题：", size_hint_y=None, height=dp(20),
            halign="left", color=(0.75, 0.70, 0.65, 1), bold=True, font_size=dp(11),
        ))
        self._app_title_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(36),
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12), padding=[dp(10), dp(10), dp(10), dp(10)],
        )
        box.add_widget(self._app_title_input)

        box.add_widget(Label(
            text="欢迎标题：", size_hint_y=None, height=dp(20),
            halign="left", color=(0.75, 0.70, 0.65, 1), bold=True, font_size=dp(11),
        ))
        self._app_welcome_title = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(36),
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12), padding=[dp(10), dp(10), dp(10), dp(10)],
        )
        box.add_widget(self._app_welcome_title)

        box.add_widget(Label(
            text="欢迎文字：", size_hint_y=None, height=dp(20),
            halign="left", color=(0.75, 0.70, 0.65, 1), bold=True, font_size=dp(11),
        ))
        self._app_welcome_text = TextInput(
            text="", multiline=True, size_hint_y=None, height=dp(80),
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12), padding=[dp(10), dp(10), dp(10), dp(10)],
        )
        box.add_widget(self._app_welcome_text)

        # ── 世界观 ──
        world_header = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(6))
        world_header.add_widget(Label(
            text="世界观/大背景：", size_hint_x=0.75,
            halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1), bold=True, font_size=dp(11),
        ))
        world_infer_btn = RoundedButton(
            btn_color=theme.purple,
            text="AI推断", size_hint_x=0.25,
            color=(1, 1, 1, 1), font_size=dp(9), bold=True,
        )
        world_infer_btn.bind(on_release=self._ai_infer_world)
        world_header.add_widget(world_infer_btn)
        box.add_widget(world_header)

        self._world_input = TextInput(
            text="", multiline=True, size_hint_y=None, height=dp(100),
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12), padding=[dp(10), dp(10), dp(10), dp(10)],
            hint_text="描述这个世界的背景设定…",
        )
        box.add_widget(self._world_input)

        # 发言顺序摘要（只读，编辑请切换到"发言"标签）
        self._app_order_label = Label(
            text="", size_hint_y=None, height=dp(28),
            halign="left", valign="middle",
            color=(0.55, 0.48, 0.42, 1), font_size=dp(11),
            text_size=(None, None),
        )
        row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(4))
        row.add_widget(Label(
            text="发言顺序：", size_hint_x=None, width=dp(64),
            halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1), bold=True, font_size=dp(11),
        ))
        row.add_widget(self._app_order_label)
        box.add_widget(row)

        box.add_widget(Widget(size_hint_y=None, height=dp(6)))

        # AI 按钮行
        ai_btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        for txt, bg, cmd in [
            ("AI补全设置", theme.purple, self._ai_fill_app_settings),
            ("AI生成设置", "#7e57c2", self._ai_gen_app_settings),
        ]:
            btn = RoundedButton(
                btn_color=bg,
                text=txt,
                color=(1, 1, 1, 1), font_size=dp(11), bold=True,
            )
            btn.bind(on_release=lambda _, c=cmd: c())
            ai_btns.add_widget(btn)
        box.add_widget(ai_btns)

        box.add_widget(Widget(size_hint_y=None, height=dp(6)))

        # 保存按钮
        save_btn = RoundedButton(
            btn_color=theme.accent,
            text="保存", size_hint_y=None, height=dp(44),
            color=(1, 1, 1, 1), font_size=dp(13), bold=True,
        )
        save_btn.bind(on_release=self._save_app_settings)
        box.add_widget(save_btn)

        self.content_area.add_widget(box_scroll)
        #  v0.5.3: 修复发言顺序输入框初始不显示文字的问题
        Clock.schedule_once(lambda dt: self._refresh_app_inputs(), 0.1)
