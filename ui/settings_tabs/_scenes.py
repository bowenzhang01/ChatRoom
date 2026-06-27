# -*- coding: utf-8 -*-
"""SettingsPopup — 场景管理 Tab"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import hex_to_rgba
from ui.base_widgets import FitSpinner, FitSpinnerOption, ScrollDropdown, RoundedButton
from ui.theme import theme


class ScenesTabMixin:
    """场景管理 Tab — CRUD"""

    def _build_scenes_tab(self):
        box = BoxLayout(orientation="vertical", spacing=dp(4))

        # Scene list spinner
        names = [s.get("time", "?") for s in self.app.scenes] or ["(空)"]
        self._scene_spinner = FitSpinner(
            font_name=config.FONT_DEFAULT,
            text=names[0] if names else "(空)",
            values=names,
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=(1, 1, 1, 1),
            color=(0.15, 0.12, 0.10, 1),
            option_cls=FitSpinnerOption,
            dropdown_cls=ScrollDropdown,
        )
        self._scene_spinner.bind(text=self._on_scene_selected)
        box.add_widget(self._scene_spinner)

        # Edit fields
        def make_row(label_text):
            row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
            row.add_widget(Label(
                text=label_text, size_hint_x=0.2, halign="right", valign="middle",
                color=(0.75, 0.70, 0.65, 1), font_size=dp(12),
            ))
            inp = TextInput(
                text="", size_hint_x=0.8, multiline=False,
                background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
                font_size=dp(12), padding=(dp(6), dp(8)),
            )
            row.add_widget(inp)
            return row, inp

        row_t, self._sc_time_input = make_row("时间：")
        box.add_widget(row_t)
        row_l, self._sc_location_input = make_row("地点：")
        box.add_widget(row_l)
        row_m, self._sc_mood_input = make_row("氛围：")
        box.add_widget(row_m)

        box.add_widget(Label(
            text="场景描述：", size_hint_y=None, height=dp(22),
            halign="left", color=(0.75, 0.70, 0.65, 1), font_size=dp(12),
        ))
        self._sc_desc_input = TextInput(
            text="", multiline=True, size_hint_y=1,
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12), padding=(dp(6), dp(8)),
        )
        box.add_widget(self._sc_desc_input)

        # Buttons
        btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        for txt, bg, cmd in [
            ("保存", theme.accent, self._save_scene),
            ("切换到此", "#ff8a65", self._use_scene),
            ("添加", theme.info, self._add_scene),
            ("删除", theme.danger, self._del_scene),
        ]:
            btn = RoundedButton(
                btn_color=bg,
                text=txt,
                color=(1, 1, 1, 1), font_size=dp(10), bold=True,
            )
            btn.bind(on_release=lambda _, c=cmd: c())
            btns.add_widget(btn)
        box.add_widget(btns)

        # AI 辅助按钮
        ai_btns = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        for txt, bg, cmd in [
            ("AI补全", theme.purple, self._ai_fill_scene),
            ("AI生成", "#7e57c2", self._ai_gen_scene),
        ]:
            btn = RoundedButton(
                btn_color=bg,
                text=txt,
                color=(1, 1, 1, 1), font_size=dp(10), bold=True,
            )
            btn.bind(on_release=lambda _, c=cmd: c())
            ai_btns.add_widget(btn)
        box.add_widget(ai_btns)

        self.content_area.add_widget(box)
        if self.app.scenes and self.app.scene_idx < len(self.app.scenes):
            self._scene_spinner.text = self.app.scenes[self.app.scene_idx].get("time", "?")
        if self.app.scenes:
            Clock.schedule_once(lambda dt: self._load_scene_fields(self.app.scenes[0]), 0.1)

    def _on_scene_selected(self, spinner, text):
        for i, s in enumerate(self.app.scenes):
            if s.get("time", "?") == text:
                self._load_scene_fields(s)
                return

    def _load_scene_fields(self, s):
        self._sc_time_input.text = s.get("time", "")
        self._sc_location_input.text = s.get("location", "")
        self._sc_mood_input.text = s.get("mood", "")
        self._sc_desc_input.text = s.get("scene", "")

    def _save_scene(self):
        sel_text = self._scene_spinner.text
        for i, s in enumerate(self.app.scenes):
            if s.get("time", "?") == sel_text:
                self.app.scenes[i] = {
                    "time": self._sc_time_input.text.strip(),
                    "location": self._sc_location_input.text.strip(),
                    "mood": self._sc_mood_input.text.strip(),
                    "scene": self._sc_desc_input.text.strip(),
                }
                self.app._save_scenes()
                self._refresh_scene_spinner()
                self.app._refresh_scene_display()
                return

    def _use_scene(self):
        sel_text = self._scene_spinner.text
        for i, s in enumerate(self.app.scenes):
            if s.get("time", "?") == sel_text:
                self.app.scene_idx = i
                self.app._update_scene_label()
                return

    def _add_scene(self):
        self.app.scenes.append({"time": "新场景", "location": "", "mood": "普通", "scene": "在这里写场景描述..."})
        self.app._save_scenes()
        self._refresh_scene_spinner()
        self._scene_spinner.text = "新场景"
        self._load_scene_fields(self.app.scenes[-1])

    def _del_scene(self):
        sel_text = self._scene_spinner.text
        if len(self.app.scenes) <= 1:
            return

        from kivy.uix.popup import Popup
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text=f"确定要删除场景「{sel_text}」吗？\n\n此操作不可撤销。",
            font_name=config.FONT_DEFAULT,
            halign="center", valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        ))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12), padding=(dp(16), 0))
        btn_cancel = RoundedButton(
            btn_color=theme.GRAY_600,
            text="取消",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btn_confirm = RoundedButton(
            btn_color=theme.danger,
            text="删除",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12), bold=True,
        )
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_confirm)
        content.add_widget(btns)
        popup = Popup(
            title="删除场景",
            content=content,
            size_hint=(0.85, 0.32),
            background_color=hex_to_rgba(theme.window_bg),
            auto_dismiss=False,
        )
        def do_delete(*args):
            popup.dismiss()
            for i, s in enumerate(self.app.scenes):
                if s.get("time", "?") == sel_text:
                    del self.app.scenes[i]
                    self.app._save_scenes()
                    self._refresh_scene_spinner()
                    if self.app.scene_idx >= len(self.app.scenes):
                        self.app.scene_idx = 0
                    self.app._update_scene_label()
                    return
        btn_cancel.bind(on_release=popup.dismiss)
        btn_confirm.bind(on_release=do_delete)
        popup.open()

    def _refresh_scene_spinner(self):
        names = [s.get("time", "?") for s in self.app.scenes]
        self._scene_spinner.values = names
        self._scene_spinner.text = names[0] if names else "(空)"
