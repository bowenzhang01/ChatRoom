# -*- coding: utf-8 -*-
"""
Dorm Life - 设置弹窗 (v2.0 主题增强版)
  SettingsPopup: 剧本/场景/角色/API/应用 五大配置 Tab
  Tab 逻辑已拆分至 ui/settings_tabs/ 下的 mixin 类
  增强: 主题令牌 + 圆角关闭按钮 + Tab 激活指示器 + 卡片间距
"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import hex_to_rgba
from ui.base_widgets import RoundedButton
from ui.theme import theme

# ── Tab Mixins ──
from ui.settings_tabs._world import WorldTabMixin
from ui.settings_tabs._scenes import ScenesTabMixin
from ui.settings_tabs._chars import CharsTabMixin
from ui.settings_tabs._ai import AIMixin
from ui.settings_tabs._api import APITabMixin
from ui.settings_tabs._app import AppTabMixin


class SettingsPopup(
    WorldTabMixin,
    ScenesTabMixin,
    CharsTabMixin,
    AIMixin,
    APITabMixin,
    AppTabMixin,
    Popup,
):
    """设置弹窗 — 框架代码，Tab 逻辑来自 mixin 类"""

    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.app = app_instance
        self.title = "配置"
        self.size_hint = (0.95, 0.9)
        self.background_color = hex_to_rgba(theme.window_bg)
        self.auto_dismiss = False

        self.main_layout = BoxLayout(
            orientation="vertical",
            padding=theme.spacing_md,
            spacing=theme.spacing_md,
        )

        # ── Tab 按钮栏 ──
        tabs = BoxLayout(
            size_hint_y=None, height=theme.tabbar_h,
            spacing=theme.spacing_xs,
        )
        self.tab_btns = {}
        self._tab_names = [
            ("world", "剧本"),
            ("scenes", "场景"),
            ("chars", "角色"),
            ("api", "API"),
            ("app", "设置"),
        ]
        for tab_name, label_text in self._tab_names:
            btn = RoundedButton(
                btn_color=theme.primary,
                text=label_text,
                size_hint_y=1,
                size_hint_x=1,
                color=(1, 1, 1, 1),
                bold=True,
                font_size=theme.font_sm,
                radius=theme.radius_sm,
            )
            btn.bind(on_release=lambda _, t=tab_name: self._switch_tab(t))
            tabs.add_widget(btn)
            self.tab_btns[tab_name] = btn
        self.main_layout.add_widget(tabs)

        # Tab 激活指示器（底部彩色细条）
        self.tab_indicator = Widget(
            size_hint_y=None, height=dp(3),
        )
        with self.tab_indicator.canvas:
            from kivy.graphics import Color, RoundedRectangle
            self._ind_color = Color(*hex_to_rgba(theme.primary_dark))
            self._ind_rect = RoundedRectangle(
                radius=[dp(2), dp(2), dp(2), dp(2)],
            )
        self.tab_indicator.bind(
            pos=self._update_indicator,
            size=self._update_indicator,
        )
        self.main_layout.add_widget(self.tab_indicator)

        # ── Tab 内容区域 ──
        self.content_area = BoxLayout(orientation="vertical")
        self.main_layout.add_widget(self.content_area)

        # ── 关闭按钮 ──
        close_btn = RoundedButton(
            btn_color=theme.GRAY_600,
            text="关闭",
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1),
            radius=theme.radius_md,
        )
        close_btn.bind(on_release=self._on_close)
        self.main_layout.add_widget(close_btn)

        self.content = self.main_layout
        self.bind(on_open=self._apply_settings_font)
        self._switch_tab("world")

    def _on_close(self, *args):
        """关闭时自动恢复对话（v0.5.1 / v0.8.7: 直接恢复，不再走队列）"""
        self.dismiss()
        if hasattr(self, '_was_running') and self._was_running:
            effective_order = self.app._get_effective_order()
            current_char = effective_order[self.app.turn_idx % len(effective_order)] if effective_order else None
            if current_char == "You":
                self.app.btn_start_pause.text = "继续"
                self.app.btn_start_pause.btn_color = theme.accent
                self.app.btn_start_pause.set_btn_color(theme.accent)
                self.app._set_status("轮到你了～", theme.info)
                self.app._show_input_bar("user")
            else:
                self.app.paused = False
                self.app.btn_start_pause.text = "暂停"
                self.app.btn_start_pause.btn_color = theme.warning
                self.app.btn_start_pause.set_btn_color(theme.warning)
                self.app._set_status("运行中", theme.accent)
                self.app._hide_input_frame()
                self.app._toggle_save_btn(False)

    def _apply_settings_font(self, *args):
        def set_font(w):
            for c in w.children:
                if isinstance(c, (Label, Button, TextInput)) and c.font_name == 'Roboto':
                    c.font_name = config.FONT_DEFAULT
                set_font(c)
        set_font(self.main_layout)

    def _switch_tab(self, tab_name):
        self._current_tab = tab_name
        for name, btn in self.tab_btns.items():
            if name == tab_name:
                btn.set_bg_color(theme.primary_dark)
            else:
                btn.set_bg_color(theme.primary)

        # 更新指示器位置和宽度
        btn = self.tab_btns[tab_name]
        self.tab_indicator.width = btn.width
        self.tab_indicator.x = btn.x
        self.tab_indicator.y = btn.y - dp(3)
        # 绑定指示器跟随按钮
        def _follow(*a):
            self.tab_indicator.width = btn.width
            self.tab_indicator.x = btn.x
        btn.bind(pos=_follow, size=_follow)

        self.content_area.clear_widgets()
        if tab_name == "world":
            self._build_world_tab()
        elif tab_name == "scenes":
            self._build_scenes_tab()
        elif tab_name == "chars":
            self._build_chars_tab()
        elif tab_name == "api":
            self._build_api_tab()
        elif tab_name == "app":
            self._build_app_tab()
        Clock.schedule_once(lambda dt: self._apply_settings_font(), 0.05)

    def _update_indicator(self, instance, value):
        self._ind_rect.pos = instance.pos
        self._ind_rect.size = instance.size
