# -*- coding: utf-8 -*-
"""SettingsPopup — 角色管理 Tab"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex as hex_color

import os
import config
from utils import hex_to_rgba
from ui.base_widgets import FitSpinner, FitSpinnerOption, ScrollDropdown, RoundedButton
from ui.theme import theme


class CharsTabMixin:
    """角色管理 Tab — CRUD (v0.5.1: You.json 特殊处理)"""

    def _build_chars_tab(self):
        box = BoxLayout(orientation="vertical", spacing=dp(4))

        char_names = sorted(self.app.characters.keys())
        # 角色名列表
        display_names = []
        for name in char_names:
            st = self.app.char_styles.get(name, {})
            dname = st.get("name", name)
            label = dname
            if name == "You":
                label += "  [用户模式专属]"
            display_names.append(label)
        self._char_names_list = char_names  # 保存原始名称映射

        self._char_spinner = FitSpinner(
            font_name=config.FONT_DEFAULT,
            text=display_names[0] if display_names else "(无)",
            values=display_names,
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=(1, 1, 1, 1),
            color=(0.15, 0.12, 0.10, 1),
            option_cls=FitSpinnerOption,
            dropdown_cls=ScrollDropdown,
        )
        self._char_spinner.bind(text=self._on_char_selected)
        box.add_widget(self._char_spinner)

        self._ch_inputs = {}
        fields = [
            ("英文名", "name"), ("显示名", "dname"),
            ("颜色", "color"), ("背景色", "bg"),
        ]
        for label_text, key in fields:
            row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
            row.add_widget(Label(
                text=f"{label_text}：", size_hint_x=0.22, halign="right", valign="middle",
                color=(0.75, 0.70, 0.65, 1), font_size=dp(11),
            ))
            inp = TextInput(
                text="", size_hint_x=0.78, multiline=False,
                background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
                font_size=dp(11), padding=(dp(4), dp(7)),
            )
            row.add_widget(inp)
            self._ch_inputs[key] = inp
            box.add_widget(row)

        # Personality
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
        row.add_widget(Label(
            text="性格：", size_hint_x=0.22, halign="right", valign="middle",
            color=(0.75, 0.70, 0.65, 1), font_size=dp(11),
        ))
        self._ch_personality = TextInput(
            text="", size_hint_x=0.78, multiline=False,
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(11), padding=(dp(4), dp(7)),
        )
        row.add_widget(self._ch_personality)
        box.add_widget(row)

        box.add_widget(Label(
            text="描述：", size_hint_y=None, height=dp(18),
            halign="left", color=(0.75, 0.70, 0.65, 1), font_size=dp(11),
        ))
        self._ch_desc = TextInput(
            text="", multiline=True, size_hint_y=0.25,
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(11), padding=(dp(4), dp(7)),
        )
        box.add_widget(self._ch_desc)

        box.add_widget(Label(
            text="系统提示：", size_hint_y=None, height=dp(18),
            halign="left", color=(0.75, 0.70, 0.65, 1), font_size=dp(11),
        ))
        self._ch_prompt = TextInput(
            text="", multiline=True, size_hint_y=0.35,
            background_color=(1, 1, 1, 1), foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(11), padding=(dp(4), dp(7)),
        )
        box.add_widget(self._ch_prompt)

        # Buttons
        btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        for txt, bg, cmd in [
            ("保存", theme.accent, self._save_char),
            ("添加", theme.info, self._add_char),
        ]:
            btn = RoundedButton(
                btn_color=bg,
                text=txt,
                color=(1, 1, 1, 1), font_size=dp(10), bold=True,
            )
            btn.bind(on_release=lambda _, c=cmd: c())
            btns.add_widget(btn)

        self._del_btn = RoundedButton(
            btn_color=theme.danger,
            text="删除",
            color=(1, 1, 1, 1), font_size=dp(10), bold=True,
        )
        self._del_btn.bind(on_release=self._del_char)
        btns.add_widget(self._del_btn)
        box.add_widget(btns)

        # AI 辅助按钮
        ai_btns = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        for txt, bg, cmd in [
            ("AI补全", theme.purple, self._ai_fill_char),
            ("AI生成", "#7e57c2", self._ai_gen_char),
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
        if char_names:
            Clock.schedule_once(lambda dt: self._load_char_fields(char_names[0]), 0.1)

    def _get_selected_char_name(self):
        """从 spinner 显示文本解析回原始名称"""
        sel = self._char_spinner.text
        for i, dname in enumerate(self._char_spinner.values):
            if dname == sel and i < len(self._char_names_list):
                return self._char_names_list[i]
        return sel

    def _on_char_selected(self, spinner, text):
        name = self._get_selected_char_name()
        if name:
            self._load_char_fields(name)
        # v0.5.1: You 角色特殊处理
        self._update_char_buttons(name)

    def _update_char_buttons(self, name):
        """v0.5.1: You 角色禁用删除按钮，锁定英文名"""
        is_you = (name == "You")
        if is_you:
            self._del_btn.disabled = True
            self._del_btn.set_bg_color(theme.GRAY_300)
            self._del_btn.color = (0.6, 0.6, 0.6, 1)
            if "name" in self._ch_inputs:
                self._ch_inputs["name"].disabled = True
                self._ch_inputs["name"].background_color = (0.96, 0.96, 0.96, 1)
        else:
            self._del_btn.disabled = False
            self._del_btn.set_bg_color(theme.danger)
            self._del_btn.color = (1, 1, 1, 1)
            if "name" in self._ch_inputs:
                self._ch_inputs["name"].disabled = False
                self._ch_inputs["name"].background_color = (1, 1, 1, 1)

    def _load_char_fields(self, name):
        c = self.app.characters.get(name, {})
        st = self.app.char_styles.get(name, {})
        self._ch_inputs["name"].text = c.get("name", name)
        self._ch_inputs["dname"].text = c.get("display_name", name)
        self._ch_inputs["color"].text = c.get("color", "#888")
        self._ch_inputs["bg"].text = c.get("bg_color", "#f0f0f0")
        self._ch_personality.text = c.get("personality", "")
        self._ch_desc.text = c.get("description", "")
        self._ch_prompt.text = c.get("system_prompt", "")
        self._update_char_buttons(name)

    def _save_char(self):
        old_name = self._get_selected_char_name()
        new_name = self._ch_inputs["name"].text.strip()
        if not new_name:
            return
        # v0.5.1: You 角色英文名锁定
        if old_name == "You" and new_name != "You":
            new_name = "You"
            self._ch_inputs["name"].text = "You"
        char_data = {
            "name": new_name,
            "display_name": self._ch_inputs["dname"].text.strip(),
            "color": self._ch_inputs["color"].text.strip(),
            "bg_color": self._ch_inputs["bg"].text.strip(),
            "personality": self._ch_personality.text.strip(),
            "description": self._ch_desc.text.strip(),
            "system_prompt": self._ch_prompt.text.strip(),
        }
        fname = new_name + ".json"
        if new_name != old_name and new_name in self.app.characters:
            self.app._set_status(f"角色名「{new_name}」已存在！", theme.danger)
            return
        self.app._save_character(fname, char_data)
        if new_name != old_name:
            old_path = str(self.app.char_dir / (old_name + ".json"))
            if os.path.exists(old_path):
                os.remove(old_path)
            if old_name in self.app.turn_order:
                self.app.turn_order = [new_name if n == old_name else n for n in self.app.turn_order]
                self.app._save_turn_order()
        self.app._reload_data()
        self._refresh_char_spinner()

    def _add_char(self):
        base = "NewChar" + str(len(self.app.characters) + 1)
        char_data = {
            "name": base,
            "display_name": "新角色",
            "color": "#888888",
            "bg_color": "#f5f5f5",
            "personality": "待设定",
            "description": "请在这里写角色描述...",
            "system_prompt": "你是一个角色，请描述你自己。",
        }
        self.app._save_character(base + ".json", char_data)
        self.app._reload_data()
        self._refresh_char_spinner()
        for i, name in enumerate(self._char_names_list):
            if name == base:
                self._char_spinner.text = self._char_spinner.values[i]
                break
        Clock.schedule_once(lambda dt: self._load_char_fields(base), 0.15)

    def _del_char(self, *args):
        name = self._get_selected_char_name()
        if len(self.app.characters) <= 1 or name == "You":
            return

        st = self.app.char_styles.get(name, {})
        dname = st.get("name", name)

        from kivy.uix.popup import Popup
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text=f"确定要删除角色「{dname}」吗？\n\n此操作不可撤销。",
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
            title="删除角色",
            content=content,
            size_hint=(0.85, 0.32),
            background_color=hex_to_rgba(theme.window_bg),
            auto_dismiss=False,
        )
        def do_delete(*args):
            popup.dismiss()
            self.app._delete_character(name)
            if name in self.app.turn_order:
                self.app.turn_order.remove(name)
                self.app._save_turn_order()
            self.app._reload_data()
            self._refresh_char_spinner()
        btn_cancel.bind(on_release=popup.dismiss)
        btn_confirm.bind(on_release=do_delete)
        popup.open()

    def _refresh_char_spinner(self):
        char_names = sorted(self.app.characters.keys())
        self._char_names_list = char_names
        display_names = []
        for name in char_names:
            st = self.app.char_styles.get(name, {})
            dname = st.get("name", name)
            label = dname
            if name == "You":
                label += "  [用户模式专属]"
            display_names.append(label)
        self._char_spinner.values = display_names
        if display_names:
            self._char_spinner.text = display_names[0]
            Clock.schedule_once(lambda dt: self._load_char_fields(char_names[0]), 0.1)
