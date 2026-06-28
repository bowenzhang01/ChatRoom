# -*- coding: utf-8 -*-
"""
Dorm Life - Kivy Edition v0.9.0 (Android APK Ready)
 v0.6.5: 多剧本/多配置组支持 — profiles/ 目录隔离
 v0.7.0: AI 创建场景 / 角色 / 剧本
 v0.8.x: 对话存档 / 动态发言 / Spinner 升级 / UX 优化
 v0.9.0: 代码模块化拆分 (6→1 文件) + 4个 Bug 修复
 v0.8.0: 对话保存 / 读取 / 删除 + 自动存档恢复
 v0.8.6: AI 导演动态发言顺序 + 沉默追踪
女生寝室角色扮演聊天室 · 手机版
 v0.5.3: API 模型自动获取 + 下拉选择 + 自定义模型输入
"""

import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
import threading
from threading import Thread, Event
from typing import Optional

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hex_color
from kivy.graphics import Color

# ── 拆分后的模块导入 ──
import config
from utils import load_json, save_json, hex_to_rgba, extract_json, make_popup_label
from ui.theme import theme
from ui.base_widgets import (
    StatusDot, RoundedButton, ColoredButton,
    FitSpinner,
)
from ui.chat_widgets import ChatView
from ui.shadow_widgets import Divider
from ui.settings_popup import SettingsPopup
from ui.animations import fade_in, fade_out, slide_in_up, slide_out_down
from api_service import call_chat_completion, call_chat_completion_async, APIError
from core.chat_manager import ChatManager
from core.ai_engine import AIEngine
from core.data_manager import DataManager

# ═══════════════════════════════════════════════
#  Main App (v0.5.1: 全面升级)
# ═══════════════════════════════════════════════

class DormApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Dorm Life"
        self.running = False
        self.paused = False
        self.mode = "round"
        self.speed = 3
        self.turn_order = []
        self.turn_idx = 0
        self.turn_count = 0
        self.message_count = 0
        self.scene_idx = 0
        self._char_last_turn = {}  # v0.8.6: silence tracking for dynamic mode
        self._suggested_next = None  # v0.8.6: [NEXT] hint from last character
        # v0.6.5: 动态剧本数据
        self.profile_dir = None
        self.char_dir = None
        self.scenes = []
        self.characters = {}
        self.char_styles = {}
        self._profile_config = {}
        # v0.5.1: 新增模式
        self.director_mode = False
        self.user_mode = False
        self._input_mode = None  # "director" | "user"
        self._api_error_count = 0  # v0.5.2: API 连续失败计数器
        self.history: list = []
        self._task: Optional[Thread] = None
        self._queue = Queue()
        self._stop_event = Event()
        # v0.8.0: 对话存档 (v0.9.1: 拆分至 ChatManager)
        self.chat = ChatManager(self)
        # v0.9.1: AI 引擎拆分
        self.ai = AIEngine(self)
        # v0.9.1: 数据管理拆分
        self.data = DataManager(self)

    def _setup_workspace(self):
        """v0.6.5: 确定读写工作目录。Android/iOS 上使用 user_data_dir，PC 沿用 config.BASE_DIR"""
        is_mobile = hasattr(sys, 'platform') and sys.platform in ('android', 'ios')
        if is_mobile and hasattr(self, 'user_data_dir') and self.user_data_dir:
            # Android / iOS: 应用安装目录只读，user_data_dir 可写
            ud = Path(self.user_data_dir)
            # 首次启动：将内置剧本复制到可写目录
            bundled_profiles = config.BASE_DIR / "profiles"
            writable_profiles = ud / "profiles"
            if bundled_profiles.exists() and not writable_profiles.exists():
                import shutil
                shutil.copytree(str(bundled_profiles), str(writable_profiles))
            # 迁移内置 config（如果 user_data 中不存在）
            bundled_config = config.BASE_DIR / "config.json"
            writable_config = ud / "config.json"
            if bundled_config.exists() and not writable_config.exists():
                import shutil
                shutil.copy(str(bundled_config), str(writable_config))
            # 切换全局路径
            config.BASE_DIR = ud
            config.PROFILES_DIR = ud / "profiles"
            # 重新加载 config（从可写目录）
            config.app_config = load_json(config.BASE_DIR / "config.json")

    def build(self):
        # v0.6.5: 在 build() 中初始化工作区（此时 user_data_dir 已就绪）
        self._setup_workspace()
        self._migrate_if_needed()
        self.load_profile(config.ACTIVE_PROFILE)

        Window.clearcolor = hex_to_rgba(theme.window_bg)
        Window.minimum_width = dp(320)
        Window.minimum_height = dp(480)

        # Root layout
        root = BoxLayout(orientation="vertical")

        # ── 顶部工具栏 ──
        toolbar = BoxLayout(
            size_hint_y=None, height=theme.toolbar_h,
            spacing=theme.spacing_md, padding=(dp(6), dp(4)),
        )
        with toolbar.canvas.before:
            from kivy.graphics import Color as GColor, Rectangle
            toolbar.bg_color = GColor(*hex_to_rgba(theme.primary))
            toolbar.bg_rect = Rectangle(pos=toolbar.pos, size=toolbar.size)
        toolbar.bind(
            pos=lambda obj, val: setattr(toolbar.bg_rect, "pos", val),
            size=lambda obj, val: setattr(toolbar.bg_rect, "size", val),
        )

        self.title_label = Label(
            text=self.title,
            font_name=config.FONT_DEFAULT,
            size_hint_x=1,
            color=(1, 1, 1, 1),
            bold=True,
            font_size=theme.font_title,
            halign="left",
            valign="middle",
            shorten=True,
        )
        self.title_label.bind(size=lambda lbl, s: setattr(lbl, "text_size", (s[0] - dp(8), None)))
        toolbar.add_widget(self.title_label)

        # Speed spinner
        self.speed_spinner = FitSpinner(
            font_name=config.FONT_DEFAULT,
            text=str(self.speed),
            values=["1", "2", "3", "5", "8", "10"],
            size_hint=(None, None),
            size=(dp(54), dp(36)),
            background_normal="",
            background_color=(1, 1, 1, 0.3),
            color=(1, 1, 1, 1),
            font_size=theme.font_body,
        )
        self.speed_spinner.bind(text=self._on_speed_change)
        toolbar.add_widget(self.speed_spinner)

        # Mode toggle button
        self.btn_mode = ColoredButton(
            btn_color="#ff8a65", text="轮流",
            size_hint_x=None,
            size_hint_y=None,
            width=dp(66),
        )
        self.btn_mode.bind(on_release=self._toggle_mode)
        toolbar.add_widget(self.btn_mode)

        # Settings button
        settings_btn = RoundedButton(
            btn_color=theme.WHITE,
            text="设置",
            font_name=config.FONT_DEFAULT,
            size_hint=(None, None),
            size=(dp(66), dp(36)),
            color=(1, 1, 1, 1),
            font_size=theme.font_body,
            radius=theme.radius_sm,
        )
        settings_btn.set_bg_color((1, 1, 1, 0.3))
        settings_btn.bind(on_release=self._open_settings)
        toolbar.add_widget(settings_btn)

        root.add_widget(toolbar)

        # ═══ v0.5.1 新增：模式选择栏 ═══
        self.mode_bar = BoxLayout(
            size_hint_y=None, height=theme.modebar_h,
            spacing=theme.spacing_sm, padding=(dp(8), dp(4)),
        )
        with self.mode_bar.canvas.before:
            self.mode_bar.bg_color = GColor(*hex_to_rgba(theme.primary_light))
            self.mode_bar.bg_rect = Rectangle(pos=self.mode_bar.pos, size=self.mode_bar.size)
        self.mode_bar.bind(
            pos=lambda obj, val: setattr(obj.bg_rect, "pos", val),
            size=lambda obj, val: setattr(obj.bg_rect, "size", val),
        )

        mode_label = Label(
            text="模式：",
            font_name=config.FONT_DEFAULT,
            size_hint_x=None,
            width=dp(56),
            color=hex_to_rgba(theme.text_hint),
            font_size=theme.font_sm,
            halign="left",
            valign="middle",
        )
        self.mode_bar.add_widget(mode_label)

        # 导演模式开关
        self.dir_btn = RoundedButton(
            btn_color=theme.primary_light,
            text="导演模式",
            font_name=config.FONT_DEFAULT,
            size_hint_x=1,
            color=hex_to_rgba(theme.text_hint),
            font_size=theme.font_xs,
            bold=True,
            radius=theme.radius_sm,
        )
        self.dir_btn.bind(on_release=lambda _: self._toggle_director_mode())
        self.mode_bar.add_widget(self.dir_btn)

        # 用户模式开关
        self.user_btn = RoundedButton(
            btn_color=theme.primary_light,
            text="用户模式",
            font_name=config.FONT_DEFAULT,
            size_hint_x=1,
            color=hex_to_rgba(theme.text_hint),
            font_size=theme.font_xs,
            bold=True,
            radius=theme.radius_sm,
        )
        self.user_btn.bind(on_release=lambda _: self._toggle_user_mode())
        self.mode_bar.add_widget(self.user_btn)

        self._update_mode_buttons()
        root.add_widget(self.mode_bar)

        # ═══ v0.5.1 新增：通用输入栏 ═══
        self.input_frame = BoxLayout(
            size_hint_y=None, height=dp(0), opacity=0,
            spacing=theme.spacing_sm, padding=(dp(4), dp(4)),
        )
        with self.input_frame.canvas.before:
            self.input_frame.bg_color = GColor(*hex_to_rgba(theme.input_bg))
            self.input_frame.bg_rect = Rectangle(pos=self.input_frame.pos, size=self.input_frame.size)
        self.input_frame.bind(
            pos=lambda obj, val: setattr(obj.bg_rect, "pos", val),
            size=lambda obj, val: setattr(obj.bg_rect, "size", val),
        )

        self.input_label = Label(
            text="导演模式",
            font_name=config.FONT_DEFAULT,
            size_hint_x=None,
            width=dp(90),
            color=hex_to_rgba(theme.text_hint),
            font_size=theme.font_sm,
            bold=True,
            halign="left",
            valign="middle",
        )
        self.input_frame.add_widget(self.input_label)

        self.input_entry = TextInput(
            text="",
            multiline=False,
            size_hint_x=1,
            background_color=hex_to_rgba(theme.WHITE),
            foreground_color=hex_to_rgba(theme.text_hint),
            font_size=theme.font_body,
            padding=(dp(6), dp(8)),
            hint_text="输入你的发言...",
        )
        self.input_entry.bind(on_text_validate=lambda _: self._send_input())
        self.input_frame.add_widget(self.input_entry)

        self.input_btn = RoundedButton(
            btn_color=theme.accent,
            text="发送",
            font_name=config.FONT_DEFAULT,
            size_hint_x=None,
            width=dp(64),
            color=(1, 1, 1, 1),
            font_size=theme.font_xs,
            bold=True,
            radius=theme.radius_md,
        )
        self.input_btn.bind(on_release=lambda _: self._send_input())
        self.input_frame.add_widget(self.input_btn)

        self.skip_btn = RoundedButton(
            btn_color=theme.GRAY_300,
            text="跳过",
            font_name=config.FONT_DEFAULT,
            size_hint_x=None,
            width=dp(64),
            color=hex_to_rgba(theme.text_muted),
            font_size=theme.font_xs,
            radius=theme.radius_md,
        )
        self.skip_btn.bind(on_release=lambda _: self._skip_user_turn())

        root.add_widget(self.input_frame)

        # ── 场景横幅 ──
        self.scene_banner = BoxLayout(
            size_hint_y=None, padding=(dp(12), dp(6)),
        )
        self.scene_banner.bind(minimum_height=self.scene_banner.setter("height"))
        with self.scene_banner.canvas.before:
            self.scene_banner.bg_color = GColor(*hex_to_rgba(theme.scene_bg))
            self.scene_banner.bg_rect = Rectangle(
                pos=self.scene_banner.pos, size=self.scene_banner.size
            )
        self.scene_banner.bind(
            pos=lambda obj, val: setattr(obj.bg_rect, "pos", val),
            size=lambda obj, val: setattr(obj.bg_rect, "size", val),
        )

        self.scene_label = Label(
            font_name=config.FONT_DEFAULT,
            text="- 正在加载...",
            color=hex_to_rgba(theme.text_hint),
            font_size=theme.font_body,
            halign="left",
            valign="middle",
            size_hint_y=None,
        )
        self.scene_label.bind(
            texture_size=lambda lbl, s: setattr(lbl, "height", s[1] + dp(4)),
            size=lambda lbl, s: setattr(lbl, "text_size", (s[0] - dp(8), None))
        )
        self.scene_banner.add_widget(self.scene_label)
        root.add_widget(self.scene_banner)

        # 场景横幅与聊天区分割线
        root.add_widget(Divider(color=theme.GRAY_200))

        # ── 聊天区 ──
        self.chat_view = ChatView()
        root.add_widget(self.chat_view)

        # ── 底部控制栏 ──
        controls = BoxLayout(
            size_hint_y=None, height=theme.controls_h,
            spacing=theme.spacing_sm, padding=(dp(4), dp(4)),
        )
        with controls.canvas.before:
            controls.bg_color = GColor(*hex_to_rgba(theme.surface_alt))
            controls.bg_rect = Rectangle(pos=controls.pos, size=controls.size)
        controls.bind(
            pos=lambda obj, val: setattr(obj.bg_rect, "pos", val),
            size=lambda obj, val: setattr(obj.bg_rect, "size", val),
        )

        # Start/Pause button
        self.btn_start_pause = ColoredButton(
            btn_color=theme.accent, text="开始",
            size_hint_x=1,
        )
        self.btn_start_pause.bind(on_release=lambda _: self._toggle_start_pause())
        controls.add_widget(self.btn_start_pause)

        # Stop button (v0.5.1: 确认弹窗)
        self.btn_stop = ColoredButton(
            btn_color=theme.danger, text="停止",
            size_hint_x=1,
        )
        self.btn_stop.bind(on_release=lambda _: self._confirm_stop())
        controls.add_widget(self.btn_stop)

        # v0.8.7: 保存按钮（暂停时显示，点击手动保存含 AI 标题）
        self.btn_save = ColoredButton(
            btn_color=theme.purple, text="保存",
            size_hint_x=None,
            width=0,
            opacity=0,
        )
        self.btn_save.disabled = True
        self.btn_save.bind(on_release=lambda _: self.save_current_chat(show_popup=True))
        controls.add_widget(self.btn_save)

        # v0.5.2: 回底按钮（滚动上去时显示，始终在控制栏内）
        self.scroll_down_btn = RoundedButton(
            btn_color=theme.accent, text="▼",
            size_hint_x=None,
            size_hint_y=None,
            width=0,
            height=dp(36),
            color=(1, 1, 1, 1),
            font_size=theme.font_body,
            bold=True,
            opacity=0,
        )
        self.scroll_down_btn.bind(on_release=lambda _: self._scroll_chat_to_bottom())
        controls.add_widget(self.scroll_down_btn)

        root.add_widget(controls)

        # ── 底部状态栏 ──
        status_bar = BoxLayout(
            size_hint_y=None, height=theme.statusbar_h,
            spacing=theme.spacing_md, padding=(dp(8), dp(4)),
        )
        with status_bar.canvas.before:
            status_bar.bg_color = GColor(*hex_to_rgba(theme.surface_alt))
            status_bar.bg_rect = Rectangle(pos=status_bar.pos, size=status_bar.size)
        status_bar.bind(
            pos=lambda obj, val: setattr(obj.bg_rect, "pos", val),
            size=lambda obj, val: setattr(obj.bg_rect, "size", val),
        )

        self.status_dot = StatusDot(
            color=hex_to_rgba(theme.accent),
            size_hint_x=None,
            width=dp(12),
        )
        status_bar.add_widget(self.status_dot)

        self.status_label = Label(
            font_name=config.FONT_DEFAULT,
            color=hex_to_rgba(theme.text_hint),
            text="就绪",
            size_hint_x=1,
            font_size=theme.font_sm,
            halign="left",
            valign="middle",
        )
        self.status_label.bind(size=lambda lbl, s: setattr(lbl, "text_size", (s[0] - dp(4), None)))
        status_bar.add_widget(self.status_label)

        self.msg_label = Label(
            font_name=config.FONT_DEFAULT,
            color=hex_to_rgba(theme.text_hint),
            text=" 0条",
            size_hint_x=None,
            width=dp(60),
            font_size=theme.font_sm,
            halign="right",
            valign="middle",
        )
        status_bar.add_widget(self.msg_label)

        root.add_widget(status_bar)

        # 欢迎信息
        self._show_welcome()

        # 更新场景显示
        self._update_scene_label()

        # 定时轮询队列
        Clock.schedule_interval(self._poll_queue, 0.1)

        # 首次启动检查 API Key
        from kivy.clock import Clock as _Clock
        _Clock.schedule_once(lambda dt: self._check_api_setup(), 0.5)

        # v0.8.0: 启动后检查自动存档恢复
        _Clock.schedule_once(lambda dt: self.check_autosave_on_start(), 0.8)

        # v0.5.2: 监听滚动位置，控制回底按钮显隐
        self.chat_view.bind(scroll_y=self._on_chat_scroll)

        return root

    # ═══════════════════════════════════════════
    #  v0.5.1 模式管理
    # ═══════════════════════════════════════════

    def _get_effective_order(self):
        """v0.9.x: 获取当前模式下的有效发言顺序（含用户角色）"""
        if self.user_mode:
            return [n for n in self.turn_order if n in self.characters]
        return [n for n in self.turn_order if n in self.characters and n != "You"]

    def _update_mode_buttons(self):
        """刷新模式按钮样式"""
        for on, btn in [(self.director_mode, self.dir_btn),
                         (self.user_mode, self.user_btn)]:
            if on:
                btn.set_bg_color((1, 1, 1, 1))
                btn.color = hex_to_rgba(theme.text_hint)
            else:
                btn.set_bg_color(theme.primary_light)
                btn.color = hex_to_rgba(theme.text_hint)

    def _toggle_director_mode(self):
        """切换导演模式（v0.5.1：即开即关）"""
        self.director_mode = not self.director_mode
        self._update_mode_buttons()
        config.app_config.setdefault("app", {})["director_mode"] = self.director_mode
        self._save_config()

    def _toggle_user_mode(self):
        """切换用户模式（v0.5.1：即开即关）"""
        self.user_mode = not self.user_mode
        self._update_mode_buttons()
        config.app_config.setdefault("app", {})["user_mode"] = self.user_mode
        self._save_config()
        if self.user_mode and "You" in self.characters and "You" not in self.turn_order:
            self.turn_order.append("You")
            self._save_turn_order()

    # ═══════════════════════════════════════════
    #  v0.5.1 通用输入栏
    # ═══════════════════════════════════════════

    def _show_input_bar(self, mode):
        """显示输入栏（带动画）"""
        self._input_mode = mode
        if mode == "director":
            self.input_label.text = "导演模式"
            self.input_label.color = hex_to_rgba(theme.text_hint)
            self.input_frame.bg_color.rgba = hex_to_rgba(theme.input_bg)
            self.input_btn.set_bg_color(theme.accent)
            self.input_btn.text = "发送"
            if self.skip_btn.parent:
                self.skip_btn.parent.remove_widget(self.skip_btn)
        elif mode == "user":
            self.input_label.text = "轮到你了"
            self.input_label.color = hex_to_rgba(theme.info)
            self.input_frame.bg_color.rgba = hex_to_rgba("#e3f2fd")
            self.input_btn.set_bg_color(theme.info)
            self.input_btn.text = "发送"
            if not self.skip_btn.parent:
                self.input_frame.add_widget(self.skip_btn)
                self.input_frame.remove_widget(self.skip_btn)
                self.input_frame.add_widget(self.skip_btn, index=len(self.input_frame.children))
        self.input_frame.height = dp(44)
        self.input_entry.text = ""
        self.input_frame.opacity = 0
        fade_in(self.input_frame, duration=0.25)
        Clock.schedule_once(lambda dt: setattr(self.input_entry, 'focus', True), 0.1)

    def _hide_input_frame(self):
        """隐藏输入栏（带动画）"""
        self._input_mode = None
        if self.skip_btn.parent:
            self.skip_btn.parent.remove_widget(self.skip_btn)
        def _on_hide_done():
            if self._input_mode is None:
                self.input_frame.height = dp(0)
        fade_out(
            self.input_frame, duration=0.18,
            on_complete=_on_hide_done,
        )

    def _toggle_save_btn(self, visible):
        """v0.8.7: 切换保存按钮显示/隐藏"""
        if visible:
            self.btn_save.size_hint_x = 1
            self.btn_save.width = 0  # reset fixed width
            self.btn_save.opacity = 1
            self.btn_save.disabled = False
        else:
            self.btn_save.size_hint_x = None
            self.btn_save.width = 0
            self.btn_save.opacity = 0
            self.btn_save.disabled = True

    def _send_input(self):
        """根据当前模式分发输入"""
        if self._input_mode == "director":
            self._send_director_note()
        elif self._input_mode == "user":
            self._send_user_message(single=False)

    def _send_director_note(self):
        """发送导演提示"""
        text = self.input_entry.text.strip()
        if not text:
            return
        self.input_entry.text = ""
        entry = {
            "name": "__director__",
            "display_name": "导演",
            "text": text,
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "director",
        }
        self.history.append(entry)
        self._append_director_message(entry)

    @mainthread
    def _append_director_message(self, entry):
        t = entry.get("time", "")
        text = entry.get("text", "")
        self.chat_view.add_message(
            name="__director__", dname="导演",
            text=text, t=t, color=theme.bubble_director_label, msg_type="director",
        )

    def _send_user_message(self, single=False):
        """发送用户消息（v0.5.1: 作为角色参与对话）"""
        text = self.input_entry.text.strip()
        if not text:
            return
        self.input_entry.text = ""
        uc = self.characters.get("You", {})
        entry = {
            "name": "You",
            "display_name": uc.get("display_name", "你"),
            "text": text,
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        # v0.5.1: 线程安全 — 通过 queue 交给主线程
        self._queue.put(("user_msg", entry))
        self._hide_input_frame()
        if not single:
            self.paused = False
            self.btn_start_pause.text = "暂停"
            self.btn_start_pause.btn_color = theme.warning
            self.btn_start_pause.set_btn_color(theme.warning)
            self._set_status("运行中", theme.accent)

    def _skip_user_turn(self):
        """v0.5.1: 跳过用户回合"""
        self.turn_idx += 1
        self.turn_count += 1
        self._hide_input_frame()
        self.paused = False
        self.btn_start_pause.text = "暂停"
        self.btn_start_pause.btn_color = theme.warning
        self.btn_start_pause.set_btn_color(theme.warning)
        self._set_status("运行中", theme.accent)
        self._toggle_save_btn(False)

    # ═══════════════════════════════════════════
    #  v0.5.1 停止确认弹窗
    # ═══════════════════════════════════════════

    def _confirm_stop(self):
        """停止确认弹窗（v0.8.0: 支持保存提醒）"""
        has_unsaved = bool(self.history) and (time.time() - self.chat._last_save_time > 30)

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        if has_unsaved:
            msg_text = "当前对话尚未保存。\n\n停止将清空全部对话记录。\n要保存后再停止吗？"
        else:
            msg_text = "这将清空全部对话记录，回到初始画面。\n\n确定要停止吗？\n（选「否」将仅暂停对话）"

        msg = make_popup_label(
            msg_text,
            halign="center",
            valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        )
        content.add_widget(msg)

        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8), padding=(dp(16), 0))

        if has_unsaved:
            btn_save_stop = RoundedButton(
                btn_color=theme.accent,
                text="保存并停止",
                font_name=config.FONT_DEFAULT,
                color=(1, 1, 1, 1), font_size=dp(11), bold=True,
            )
            btn_stop = RoundedButton(
                btn_color=theme.danger,
                text="直接停止",
                font_name=config.FONT_DEFAULT,
                color=(1, 1, 1, 1), font_size=dp(11),
            )
            btn_cancel = RoundedButton(
                btn_color=theme.GRAY_600,
                text="取消",
                font_name=config.FONT_DEFAULT,
                color=(1, 1, 1, 1), font_size=dp(11),
            )
            btns.add_widget(btn_save_stop)
            btns.add_widget(btn_stop)
            btns.add_widget(btn_cancel)

            popup = Popup(
                title="停止对话",
                content=content,
                size_hint=(0.9, 0.4),
                background_color=hex_to_rgba(theme.window_bg),
                auto_dismiss=True,
            )

            def on_save_stop(*args):
                popup.dismiss()
                self.save_current_chat(show_popup=True)
                self._queue.put(("reset", None))

            def on_stop(*args):
                popup.dismiss()
                self._queue.put(("reset", None))

            btn_save_stop.bind(on_release=on_save_stop)
            btn_stop.bind(on_release=on_stop)
            btn_cancel.bind(on_release=popup.dismiss)
        else:
            btn_no = RoundedButton(
                btn_color=theme.GRAY_600,
                text="否 — 仅暂停",
                font_name=config.FONT_DEFAULT,
                color=(1, 1, 1, 1), font_size=dp(12),
            )
            btn_yes = RoundedButton(
                btn_color=theme.danger,
                text="是 — 停止并重置",
                font_name=config.FONT_DEFAULT,
                color=(1, 1, 1, 1), font_size=dp(12), bold=True,
            )
            btns.add_widget(btn_no)
            btns.add_widget(btn_yes)

            popup = Popup(
                title="停止对话",
                content=content,
                size_hint=(0.85, 0.35),
                background_color=hex_to_rgba(theme.window_bg),
                auto_dismiss=True,
            )

            def on_no(*args):
                popup.dismiss()
                if self.running and not self.paused:
                    self._queue.put(("pause", None))

            def on_yes(*args):
                popup.dismiss()
                self._queue.put(("reset", None))

            btn_no.bind(on_release=on_no)
            btn_yes.bind(on_release=on_yes)

        content.add_widget(btns)
        popup.open()

    # ═══════════════════════════════════════════
    #  API 首次检查
    # ═══════════════════════════════════════════

    def _check_api_setup(self):
        """检查 API Key 并更新状态栏。返回 True 表示已配置。"""
        config.API_KEY = config.resolve_key()
        if not config.API_KEY:
            self._set_status(" 未配置 API Key — 请在设置中填写", theme.danger)
            return False
        self._set_status("就绪", theme.accent)
        return True

    # ═══════════════════════════════════════════
    #  UI 操作
    # ═══════════════════════════════════════════

    @mainthread
    def _set_status(self, text, color):
        self.status_label.text = text
        self.status_dot.set_color(color)

    @mainthread
    def _append_message(self, entry):
        # v0.5.2: 不再删除欢迎标签，垫片方案让它自然滚出视口
        name = entry["name"]
        st = self.char_styles.get(name, {})
        color = st.get("color", "#888")
        dname = entry.get("display_name", st.get("name", name))
        t = entry.get("time", "")
        text = entry.get("text", "")
        msg_type = entry.get("type", "normal")
        self.chat_view.add_message(name, dname, text, t, color, msg_type)
        self.message_count += 1
        self.msg_label.text = f" {self.message_count}条"

    @mainthread
    def _update_scene_label(self):
        if self.scenes and self.scene_idx < len(self.scenes):
            s = self.scenes[self.scene_idx]
            self.scene_label.text = f"- {s.get('time','')} | {s.get('location','')} — {s.get('mood','')} ：{s.get('scene','')}"

    def _on_chat_scroll(self, instance, scroll_y):
        """v0.5.2: 用户滚上去时在控制栏显示回底按钮"""
        if scroll_y > 0.05:
            self.scroll_down_btn.width = dp(44)
            self.scroll_down_btn.opacity = 1
        else:
            self.scroll_down_btn.width = 0
            self.scroll_down_btn.opacity = 0

    def _scroll_chat_to_bottom(self):
        """v0.5.2: 一键回到底部"""
        self.chat_view._scroll_to_bottom()

    @mainthread
    def _show_welcome(self):
        # v0.5.1: 使用 effective_order 显示完整发言顺序
        ac = self._profile_config.get("app", {})
        welcome_title = ac.get("welcome_title", "Welcome")
        welcome_text = ac.get("welcome_text", "")
        self.chat_view.clear()
        effective = self._get_effective_order()
        display_names = []
        for name in effective:
            if name == "You":
                c = self.characters.get(name, {})
                display_names.append(c.get("display_name", "你"))
            else:
                st = self.char_styles.get(name, {})
                display_names.append(st.get("name", name))
        welcome_content = f"\n{welcome_title}\n\n{' · '.join(display_names)}\n\n{welcome_text}\n"
        self._welcome_label = Label(
            color=(0.55, 0.48, 0.42, 1),
            text=welcome_content,
            font_name=config.FONT_DEFAULT,
            size_hint_y=None,
            halign="center",
            font_size=dp(12),
        )
        # v0.5.2: 立即绑定 text_size，防止异步高度变化导致滚动跳动
        self._welcome_label.bind(
            width=lambda instance, value: setattr(instance, "text_size", (max(0, value - dp(16)), None))
        )
        self._welcome_label.bind(texture_size=lambda lbl, s: setattr(lbl, "height", s[1] + dp(16)))
        self.chat_view.container.add_widget(self._welcome_label)
        self.message_count = 0
        self.msg_label.text = " 0条"

    @mainthread
    def _refresh_scene_display(self):
        self._update_scene_label()

    @mainthread
    def _hide_scene_banner(self):
        """v0.5.1: 对话开始后隐藏场景横幅"""
        if self.scene_banner.parent:
            self.scene_banner.parent.remove_widget(self.scene_banner)

    @mainthread
    def _show_scene_banner(self):
        """v0.5.1: 停止后重新显示场景横幅"""
        if not self.scene_banner.parent:
            root = self.chat_view.parent
            if root:
                chat_idx = list(root.children).index(self.chat_view)
                root.add_widget(self.scene_banner, index=chat_idx + 2)

    def _toggle_start_pause(self):
        if not self.running:
            self._queue.put(("start", None))
        elif self.running and not self.paused:
            self._queue.put(("pause", None))
        else:
            self._queue.put(("resume", None))

    def _toggle_mode(self, *args):
        if self.mode == "round":
            new_mode = "random"
        elif self.mode == "random":
            new_mode = "dynamic"
        else:
            new_mode = "round"
        self._queue.put(("mode", new_mode))

    def _on_speed_change(self, spinner, text):
        try:
            self._queue.put(("speed", int(text)))
        except:
            pass

    def _open_settings(self, *args):
        # v0.5.1: 打开设置时自动暂停，关闭后自动恢复
        # v0.8.7: 直接设置 paused 状态 + 自动存档，不再走队列延迟
        if getattr(self, '_settings_open', False):
            return
        self._settings_open = True
        was_running = self.running and not self.paused
        if was_running:
            self.paused = True
            self.btn_start_pause.text = "继续"
            self.btn_start_pause.btn_color = theme.accent
            self.btn_start_pause.set_btn_color(theme.accent)
            self._set_status("已暂停", theme.warning)
            if self.director_mode:
                self._show_input_bar("director")
            self._auto_save()  # v0.8.7: 暂停时自动存档
            self._toggle_save_btn(True)  # v0.8.7: 暂停时显示保存按钮

        popup = SettingsPopup(self)
        popup._was_running = was_running  # 标记打开前状态
        popup.bind(on_dismiss=lambda _: setattr(self, '_settings_open', False))
        popup.open()

    # ═══════════════════════════════════════════
    #  v0.6.5 多剧本管理 (v0.9.1: 数据操作拆分至 core/data_manager.py)
    # ═══════════════════════════════════════════

    # 薄封装 — 转发到 DataManager
    def _migrate_if_needed(self):
        return self.data._migrate_if_needed()

    def load_profile(self, profile_name):
        return self.data.load_profile(profile_name)

    def get_profile_list(self):
        return self.data.get_profile_list()

    def get_profile_display_names(self):
        return self.data.get_profile_display_names()

    def profile_name_to_display(self, folder_name):
        return self.data.profile_name_to_display(folder_name)

    def profile_display_to_name(self, display_name):
        return self.data.profile_display_to_name(display_name)

    # switch_profile 保留 — 含 UI 编排逻辑
    def switch_profile(self, new_name):
        """v0.6.5: 切换到指定剧本，强制清空上下文"""
        if new_name == config.app_config.get("active_profile", ""):
            return
        self._do_stop()
        self.history.clear()
        self.data.load_profile(new_name)
        self.turn_idx = 0
        self.turn_count = 0
        self.message_count = 0
        self.scene_idx = 0
        self._char_last_turn.clear()
        self._suggested_next = None
        self.chat._loaded_chat_path = None
        self.chat_view.clear()
        self._show_welcome()
        self._update_scene_label()
        self._check_api_setup()
        config.app_config["active_profile"] = new_name
        config.ACTIVE_PROFILE = new_name
        self.data._save_config()
        if hasattr(self, 'title_label'):
            self.title_label.text = self.title
        if hasattr(self, 'speed_spinner'):
            self.speed_spinner.text = str(self.speed)
        self._update_mode_buttons()

    # ═══════════════════════════════════════════
    #  Data I/O (v0.9.1: 拆分至 core/data_manager.py)
    # ═══════════════════════════════════════════

    def _safe_write(self, path, data, desc=""):
        return self.data._safe_write(path, data, desc)

    def _save_scenes(self):
        return self.data._save_scenes()

    def _save_config(self):
        return self.data._save_config()

    def _save_turn_order(self):
        return self.data._save_turn_order()

    def _save_character(self, filename, data):
        return self.data._save_character(filename, data)

    def _delete_character(self, name):
        return self.data._delete_character(name)

    def _reload_data(self):
        return self.data._reload_data()

    def _save_log(self):
        text = self.chat_view.get_all_text()
        if not text.strip():
            return
        log_path = config.BASE_DIR / f"{self.title}_对话.txt"
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                header = f"{self.title}\n {self.message_count}条\n{'─' * 30}\n\n"
                f.write(header + text)
        except Exception as e:
            print(f"保存日志失败: {e}")

    def _copy_log(self):
        text = self.chat_view.get_all_text()
        if not text.strip():
            return
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(text)

    # ═══════════════════════════════════════════
    #  对话存档 (v0.9.1: 拆分至 core/chat_manager.py)
    # ═══════════════════════════════════════════

    # 薄封装 — 转发到 ChatManager，保持外部调用兼容
    @property
    def chats_dir(self):
        return self.chat.chats_dir

    def _list_chat_files(self):
        return self.chat._list_chat_files()

    def _read_chat_meta(self, filepath):
        return self.chat._read_chat_meta(filepath)

    def save_current_chat(self, show_popup=True):
        return self.chat.save_current_chat(show_popup)

    def load_chat(self, filepath):
        return self.chat.load_chat(filepath)

    def delete_chat(self, filepath):
        return self.chat.delete_chat(filepath)

    def _auto_save(self):
        return self.chat._auto_save()

    def _clear_autosave(self):
        return self.chat._clear_autosave()

    def check_autosave_on_start(self):
        return self.chat.check_autosave_on_start()

    def on_pause(self):
        """App 切到后台时自动保存对话"""
        self.chat._auto_save()
        return True

    def on_stop(self):
        """v0.8.7: App 关闭时自动存档（PC 端关窗也能触发恢复）"""
        self.chat._auto_save()

    # ═══════════════════════════════════════════
    #  LLM API (v0.9.1: 拆分至 core/ai_engine.py)
    # ═══════════════════════════════════════════

    # 薄封装 — 转发到 AIEngine
    def _get_scene_text(self) -> str:
        return self.ai._get_scene_text()

    def _build_prompt(self, name: str) -> str:
        return self.ai._build_prompt(name)

    def _build_next_hint(self, current_speaker: str) -> str:
        return self.ai._build_next_hint(current_speaker)

    def _call_llm(self, name: str) -> str:
        return self.ai._call_llm(name)

    # ═══════════════════════════════════════════
    #  Dynamic Speaker Selection (v0.9.1: 拆分至 core/ai_engine.py)
    # ═══════════════════════════════════════════

    def _pick_next_speaker_rules(self):
        return self.ai._pick_next_speaker_rules()

    # ═══════════════════════════════════════════
    #  Background Loop (v0.5.1: 线程安全 + 用户回合)
    # ═══════════════════════════════════════════

    def _run_loop(self):
        # v0.5.1+: 记录当前线程身份，防止僵尸线程推送幽灵消息
        current_thread = threading.current_thread()
        while not self._stop_event.is_set():
            try:
                if self.paused:
                    time.sleep(0.3)
                    continue

                # v0.5.1: 使用 effective_order（含用户角色）
                effective_order = self._get_effective_order()

                # v0.5.1: 空顺序保护
                if not effective_order:
                    time.sleep(1)
                    continue

                if self.mode == "random":
                    name = random.choice(effective_order)
                elif self.mode == "dynamic":
                    name = self._pick_next_speaker_rules()
                    if not name:
                        name = random.choice(effective_order)
                else:
                    name = effective_order[self.turn_idx % len(effective_order)]

                # v0.5.1: 用户回合 — 暂停等待输入
                if name == "You":
                    self._queue.put(("user_turn", None))
                    self.paused = True
                    continue

                st = self.char_styles.get(name, {})
                dname = st.get("name", name)

                # API调用
                reply = self._call_llm(name)

                # v0.5.1+: 停止检查 + 线程身份校验（防止旧线程的幽灵消息）
                if self._stop_event.is_set() or current_thread is not self._task:
                    break

                # v0.5.1: 线程安全 — 全部交给主线程处理（不在此改 history/计数）
                entry = {
                    "name": name,
                    "display_name": dname,
                    "text": reply,
                    "time": datetime.now().strftime("%H:%M:%S"),
                }
                self._queue.put(("msg", entry))

                # 等待（v0.5.1: 移除自动换场景逻辑）
                for _ in range(int(self.speed * 10)):
                    if self._stop_event.is_set() or self.paused:
                        break
                    time.sleep(0.1)
            except Exception:
                time.sleep(0.5)

    # ═══════════════════════════════════════════
    #  Queue Polling (v0.5.1: 线程安全 msg 处理)
    # ═══════════════════════════════════════════

    def _poll_queue(self, dt):
        try:
            while True:
                cmd, val = self._queue.get_nowait()
                try:
                    self._handle_cmd(cmd, val)
                except Exception:
                    pass  # 防止单条消息错误导致闪退
        except Empty:
            pass

    def _handle_cmd(self, cmd, val):
        # v0.5.1: msg 处理 — 在主线程更新所有共享状态
        if cmd == "msg":
            if self.running:
                # v0.8.6: extract and strip [NEXT:Name] from character response
                text = val.get("text", "")
                next_match = re.search(r'\[NEXT:([^\]]+)\]', text)
                if next_match:
                    next_name = next_match.group(1).strip()
                    if next_name in self._get_effective_order():
                        self._suggested_next = next_name
                    # Strip the [NEXT] line from display text (anchored at end)
                    val["text"] = re.sub(r'\s*\[NEXT:[^\]]+\]\s*$', '', text).strip()
                else:
                    self._suggested_next = None
                self.history.append(val)
                # v0.5.1+: 限制 history 长度，防止无限膨胀（AI 只取最近 8 条）
                if len(self.history) > 500:
                    self.history.pop(0)
                self.turn_idx += 1
                self.turn_count += 1
                # v0.8.6: track silence for dynamic mode
                name = val.get("name", "")
                if name and name != "You":
                    self._char_last_turn[name] = self.turn_count
                self._append_message(val)
        elif cmd == "user_msg":
            # v0.5.1: 用户消息 — 同样通过主线程处理
            self._suggested_next = None  # v0.8.6: user message invalidates previous hint
            self.history.append(val)
            self.turn_idx += 1
            self.turn_count += 1
            self._char_last_turn["You"] = self.turn_count  # v0.9.1: fix — 用户发言后重置 silence
            self._append_message(val)
            self._toggle_save_btn(False)
        elif cmd == "scene":
            self._update_scene_label()
        elif cmd == "start":
            self._do_start()
        elif cmd == "stop":
            self._do_stop()
        elif cmd == "reset":
            self._do_reset()
        elif cmd == "speed":
            self.speed = max(1, min(10, val))
            if hasattr(self, 'speed_spinner'):
                self.speed_spinner.text = str(self.speed)
        elif cmd == "mode":
            self.mode = val
            mode_labels = {"round": "轮流", "random": "随机", "dynamic": "动态"}
            self.btn_mode.text = mode_labels.get(val, "轮流")
            self._char_last_turn.clear()
            self._suggested_next = None  # v0.8.6: reset hint on mode change
        elif cmd == "user_turn":
            # v0.5.1: 轮到用户发言
            self.paused = True
            self.btn_start_pause.text = "继续"
            self.btn_start_pause.btn_color = theme.accent
            self.btn_start_pause.set_btn_color(theme.accent)
            self._set_status("轮到你了～", theme.info)
            self._show_input_bar("user")
            self._toggle_save_btn(True)  # v0.8.7: 用户回合也显示保存按钮
        elif cmd == "pause":
            self.paused = True
            self.btn_start_pause.text = "继续"
            self.btn_start_pause.btn_color = theme.accent
            self.btn_start_pause.set_btn_color(theme.accent)
            self._set_status("已暂停", theme.warning)
            # v0.5.1: 暂停时如果导演模式开启，显示导演输入栏
            if self.director_mode:
                self._show_input_bar("director")
            self._auto_save()  # v0.8.7: 暂停时自动存档
            self._toggle_save_btn(True)  # v0.8.7: 暂停时显示保存按钮
        elif cmd == "resume":
            # v0.6.5: 检查当前是否因为轮到用户而暂停，避免误隐藏输入框
            effective_order = self._get_effective_order()
            current_char = effective_order[self.turn_idx % len(effective_order)] if effective_order else None
            if current_char == "You":
                # 恢复到用户等待状态，不清除输入栏
                self.btn_start_pause.text = "继续"
                self.btn_start_pause.btn_color = theme.accent
                self.btn_start_pause.set_btn_color(theme.accent)
                self._set_status("轮到你了～", theme.info)
                self._show_input_bar("user")
            else:
                self.paused = False
                self.btn_start_pause.text = "暂停"
                self.btn_start_pause.btn_color = theme.warning
                self.btn_start_pause.set_btn_color(theme.warning)
                self._set_status("运行中", theme.accent)
                # v0.5.1: 恢复时隐藏输入栏
                self._hide_input_frame()
                self._toggle_save_btn(False)  # v0.8.7: 恢复时隐藏保存按钮
        elif cmd == "api_error_stop":
            # v0.5.2: API 连续失败 → 自动暂停并弹窗
            self._do_stop()
            self._show_api_error_popup(val)
        elif cmd == "quit":
            self.stop()

    def _do_start(self):
        if self.running:
            return
        # v0.5.2: 开始前检查 API Key
        if not config.API_KEY:
            self._show_no_api_popup()
            return
        self.running = True
        self.paused = False
        self._stop_event.clear()
        self._char_last_turn.clear()
        self._task = Thread(target=self._run_loop, daemon=True)
        self._task.start()
        self.btn_start_pause.text = "暂停"
        self.btn_start_pause.btn_color = theme.warning
        self.btn_start_pause.set_btn_color(theme.warning)
        self._set_status("运行中", theme.accent)
        # v0.5.1: 对话开始后自动隐藏场景横幅
        self._hide_scene_banner()
        self._toggle_save_btn(False)  # v0.8.7: 对话开始后隐藏保存按钮

    def _show_no_api_popup(self):
        """v0.5.2: 未配置 API Key 时弹出提示"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        msg = make_popup_label(
            "角色们需要 API Key 才能发言哦～\n\n请在设置中填写 DeepSeek API Key，\n否则只能手动操作角色了。",
            halign="center",
            valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        )
        content.add_widget(msg)
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12), padding=(dp(16), 0))
        btn_cancel = RoundedButton(
            btn_color=theme.GRAY_600,
            text="取消",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1),
            font_size=dp(12),
        )
        btn_goto = RoundedButton(
            btn_color=theme.accent,
            text="去设置",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1),
            font_size=dp(12),
            bold=True,
        )
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_goto)
        content.add_widget(btns)
        popup = Popup(
            title=" 未配置 API Key",
            content=content,
            size_hint=(0.85, 0.4),
            background_color=hex_to_rgba(theme.window_bg),
            auto_dismiss=True,
        )
        btn_cancel.bind(on_release=popup.dismiss)
        btn_goto.bind(on_release=lambda *a: (popup.dismiss(), self._open_settings()))
        popup.open()

    def _show_api_error_popup(self, err_msg):
        """v0.5.2: API 连续失败后弹出提示"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        msg = make_popup_label(
            f"角色们连续尝试发言都失败了～\n\n原因：{err_msg}\n\n请检查 API 设置或网络后重试。",
            halign="center",
            valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        )
        content.add_widget(msg)
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12), padding=(dp(16), 0))
        btn_ok = RoundedButton(
            btn_color=theme.GRAY_600,
            text="知道了",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1),
            font_size=dp(12),
        )
        btn_goto = RoundedButton(
            btn_color=theme.accent,
            text="去设置",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1),
            font_size=dp(12),
            bold=True,
        )
        btns.add_widget(btn_ok)
        btns.add_widget(btn_goto)
        content.add_widget(btns)
        popup = Popup(
            title=" API 错误",
            content=content,
            size_hint=(0.85, 0.42),
            background_color=hex_to_rgba(theme.window_bg),
            auto_dismiss=True,
        )
        btn_ok.bind(on_release=popup.dismiss)
        btn_goto.bind(on_release=lambda *a: (popup.dismiss(), self._open_settings()))
        popup.open()

    def _do_stop(self):
        # v0.5.1: 线程安全 — 先设置停止标志
        self.running = False
        self.paused = False
        self._stop_event.set()
        self._task = None
        # v0.5.1: 清空队列残留（防止停止后旧消息弹出）
        while True:
            try:
                self._queue.get_nowait()
            except Empty:
                break
        self.btn_start_pause.text = "开始"
        self.btn_start_pause.btn_color = theme.accent
        self.btn_start_pause.set_btn_color(theme.accent)
        self._set_status("已停止", theme.GRAY_600)
        # v0.5.1: 停止后显示场景横幅
        self._show_scene_banner()
        self._hide_input_frame()
        self._toggle_save_btn(False)  # v0.8.7: 停止后隐藏保存按钮

    def _do_reset(self):
        self._do_stop()
        self.history.clear()
        self.turn_idx = 0
        self.turn_count = 0
        self.message_count = 0
        self.scene_idx = 0
        self._char_last_turn.clear()  # v0.8.6: reset silence tracking
        self._suggested_next = None  # v0.8.6: reset [NEXT] hint
        self.chat_view.clear()
        self.chat._loaded_chat_path = None  # v0.8.7: 停止后清除加载路径
        self._show_welcome()
        self._update_scene_label()
        self._check_api_setup()  # v0.5.2: 重置后重新检查 API Key
        # v0.5.1: 重置时隐藏输入栏
        self._hide_input_frame()

# ═══════════════════════════════════════════════
#  Entry Point
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    DormApp().run()
