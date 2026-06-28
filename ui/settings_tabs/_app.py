# -*- coding: utf-8 -*-
"""SettingsPopup — 应用设置 Tab (剧本切换/聊天管理)"""

import os
import re
import time
import shutil
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import load_json, save_json, hex_to_rgba, make_popup_label
from ui.base_widgets import FitSpinner, FitSpinnerOption, ScrollDropdown, RoundedButton
from ui.theme import theme


class AppTabMixin:
    """应用设置 Tab — 剧本切换、对话记录管理"""

    def _build_app_tab(self):
        box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box_scroll = ScrollView(size_hint=(1, 1))
        box_scroll.add_widget(box)

        # ═══ v0.6.5: 剧本切换 ═══
        box.add_widget(Label(
            text=" 剧本套件（切换将清空对话）：", size_hint_y=None, height=dp(22),
            halign="left", color=(0.91, 0.30, 0.24, 1), bold=True, font_size=dp(12),
        ))

        # 第一行：选择 + 切换 + 重命名
        profile_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        self._profile_spinner = FitSpinner(
            font_name=config.FONT_DEFAULT,
            text=self.app.profile_name_to_display(config.app_config.get("active_profile", "dorm_girls")),
            values=self.app.get_profile_display_names(),
            size_hint_x=1,
            background_normal="",
            background_color=(1, 1, 1, 1),
            color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12),
            sync_height=True,
            option_cls=FitSpinnerOption,
            dropdown_cls=ScrollDropdown,
        )
        profile_row.add_widget(self._profile_spinner)

        switch_btn = RoundedButton(
            btn_color="#ff8a65",
            text="切换",
            size_hint_x=None, width=dp(60),
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        switch_btn.bind(on_release=self._switch_profile)
        profile_row.add_widget(switch_btn)

        rename_profile_btn = RoundedButton(
            btn_color="#42a5f5",
            text="重命名",
            size_hint_x=None, width=dp(70),
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        rename_profile_btn.bind(on_release=self._rename_profile)
        profile_row.add_widget(rename_profile_btn)
        box.add_widget(profile_row)

        # 第二行：新建 + 删除 + AI创建
        action_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        new_profile_btn = RoundedButton(
            btn_color="#66bb6a",
            text="新建",
            size_hint_x=1,
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        new_profile_btn.bind(on_release=self._create_new_profile)
        action_row.add_widget(new_profile_btn)

        del_profile_btn = RoundedButton(
            btn_color="#ef5350",
            text="删除",
            size_hint_x=1,
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        del_profile_btn.bind(on_release=self._delete_current_profile)
        action_row.add_widget(del_profile_btn)

        ai_create_btn = RoundedButton(
            btn_color="#7e57c2",
            text="AI创建",
            size_hint_x=1,
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        ai_create_btn.bind(on_release=self._ai_create_profile)
        action_row.add_widget(ai_create_btn)
        box.add_widget(action_row)

        # ═══ v0.8.0: 对话记录管理 ═══
        box.add_widget(Widget(size_hint_y=None, height=dp(10)))
        box.add_widget(Label(
            text=" 对话记录：", size_hint_y=None, height=dp(22),
            halign="left", color=(0.30, 0.55, 0.25, 1), bold=True, font_size=dp(12),
        ))

        self._chat_files = self.app._list_chat_files()
        self._chat_spinner_values = []
        self._chat_spinner_paths = []
        for fp in self._chat_files:
            meta = self.app._read_chat_meta(fp)
            if meta:
                label = f"{meta['title'][:20]}  {meta['created_at'][5:10]}  ({meta['message_count']}条)"
                self._chat_spinner_values.append(label)
                self._chat_spinner_paths.append(fp)

        chat_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        self._chat_spinner = FitSpinner(
            font_name=config.FONT_DEFAULT,
            text=self._chat_spinner_values[0] if self._chat_spinner_values else "(无保存的对话)",
            values=self._chat_spinner_values or ["(无保存的对话)"],
            size_hint_x=1,
            background_normal="",
            background_color=(1, 1, 1, 1),
            color=(0.15, 0.12, 0.10, 1),
            font_size=dp(11),
            sync_height=True,
            option_cls=FitSpinnerOption,
            dropdown_cls=ScrollDropdown,
        )
        chat_row.add_widget(self._chat_spinner)

        rename_btn = RoundedButton(
            btn_color="#42a5f5",
            text="重命名",
            size_hint_x=None,
            width=dp(70),
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        rename_btn.bind(on_release=self._rename_selected_chat)
        chat_row.add_widget(rename_btn)

        load_btn = RoundedButton(
            btn_color="#66bb6a",
            text="读取",
            size_hint_x=None,
            width=dp(56),
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        load_btn.bind(on_release=self._load_selected_chat)
        chat_row.add_widget(load_btn)

        del_chat_btn = RoundedButton(
            btn_color="#ef5350",
            text="删除",
            size_hint_x=None,
            width=dp(56),
            color=(1, 1, 1, 1),
            font_size=dp(10),
        )
        del_chat_btn.bind(on_release=self._delete_selected_chat)
        chat_row.add_widget(del_chat_btn)
        box.add_widget(chat_row)

        box.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Save/export buttons
        btns_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        save_chat_btn = RoundedButton(
            btn_color="#7e57c2",
            text="保存当前对话",
            color=(1, 1, 1, 1), font_size=dp(11),
        )
        save_chat_btn.bind(on_release=self._save_chat_from_settings)
        btns_row.add_widget(save_chat_btn)

        copy_btn = RoundedButton(
            btn_color="#42a5f5",
            text="复制全部对话",
            color=(1, 1, 1, 1), font_size=dp(11),
        )
        copy_btn.bind(on_release=self._copy_chat_log)
        btns_row.add_widget(copy_btn)
        box.add_widget(btns_row)

        self.content_area.add_widget(box_scroll)
        # 切页后注入字体
        Clock.schedule_once(lambda dt: self._apply_settings_font(), 0.05)

    def _on_profile_selected(self, spinner, text):
        """v0.8.0: 仅更新 spinner 选中状态，不再自动弹窗"""
        pass  # 切换由「切换」按钮触发，重命名由「重命名」按钮触发

    def _switch_profile(self, *args):
        """v0.8.7: 点击切换按钮 → 弹窗确认 + 保存提醒"""
        text = self._profile_spinner.text
        folder_name = self.app.profile_display_to_name(text)
        active_folder = config.app_config.get("active_profile", "")
        if folder_name == active_folder:
            return  # 相同剧本，不操作

        has_unsaved = bool(self.app.history) and (time.time() - self.app.chat._last_save_time > 30)

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        msg_text = f"切换到「{text}」将清空当前全部对话记录。"
        if has_unsaved:
            msg_text += "\n\n当前对话尚未保存！"
        msg_text += "\n\n确定要切换吗？"
        msg = make_popup_label(
            msg_text,
            halign="center", valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        )
        content.add_widget(msg)
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8), padding=(dp(8), 0))
        btn_cancel = RoundedButton(
            btn_color="#78909c",
            text="取消",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1),
            font_size=dp(11),
        )
        btn_confirm = RoundedButton(
            btn_color="#ff8a65",
            text="确定切换",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1),
            font_size=dp(11),
        )
        btns.add_widget(btn_cancel)

        if has_unsaved:
            btn_save_switch = RoundedButton(
                btn_color="#66bb6a",
                text="保存并切换",
                font_name=config.FONT_DEFAULT,
                color=(1, 1, 1, 1),
                font_size=dp(11),
            )
            btns.add_widget(btn_save_switch)
        btns.add_widget(btn_confirm)
        content.add_widget(btns)

        popup = Popup(
            title="切换剧本",
            content=content,
            size_hint=(0.88, 0.4),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=True,
        )

        def on_cancel(*args):
            self._profile_spinner.text = self.app.profile_name_to_display(config.app_config.get("active_profile", "dorm_girls"))
            popup.dismiss()

        def on_confirm(*args):
            popup.dismiss()
            self._was_running = False
            self.dismiss()
            Clock.schedule_once(lambda dt: self._do_switch(folder_name), 0.3)

        def on_save_switch(*args):
            popup.dismiss()
            self._was_running = False
            self.app.save_current_chat(show_popup=True)
            self.dismiss()
            Clock.schedule_once(lambda dt: self._do_switch(folder_name), 0.3)

        btn_cancel.bind(on_release=on_cancel)
        btn_confirm.bind(on_release=on_confirm)
        if has_unsaved:
            btn_save_switch.bind(on_release=on_save_switch)
        popup.open()

    def _rename_profile(self, *args):
        """v0.8.7: 重命名当前选中的剧本（修改显示名）"""
        text = self._profile_spinner.text
        folder_name = self.app.profile_display_to_name(text)
        if not folder_name:
            return

        profile_dir = config.PROFILES_DIR / folder_name
        pc = load_json(profile_dir / "config.json")
        old_name = pc.get("app", {}).get("display_name", text)

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        content.add_widget(Label(
            text=f"重命名剧本：\n\n当前名称：{old_name}",
            font_name=config.FONT_DEFAULT,
            halign="center", valign="middle",
            color=(0.55, 0.48, 0.42, 1),
            font_size=dp(13),
            size_hint_y=None, height=dp(50),
        ))
        name_input = TextInput(
            text=old_name,
            multiline=False,
            size_hint_y=None, height=dp(40),
            background_color=(1, 1, 1, 1),
            foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(13),
            padding=(dp(10), dp(8)),
        )
        content.add_widget(name_input)

        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10), padding=(dp(8), 0))
        btn_cancel = RoundedButton(
            btn_color="#78909c",
            text="取消",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btn_confirm = RoundedButton(
            btn_color="#42a5f5",
            text="确认",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_confirm)

        popup = Popup(
            title="重命名剧本",
            content=content,
            size_hint=(0.8, 0.35),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=False,
        )

        _confirmed = [False]
        def _on_dismiss(instance):
            if not _confirmed[0]:
                active_display = self.app.profile_name_to_display(
                    config.app_config.get("active_profile", "")
                )
                self._profile_spinner.text = active_display
        popup.bind(on_dismiss=_on_dismiss)

        def on_confirm(*args):
            _confirmed[0] = True
            new_name = name_input.text.strip()
            if not new_name or new_name == old_name:
                popup.dismiss()
                return
            pc.setdefault("app", {})["display_name"] = new_name
            save_json(profile_dir / "config.json", pc)
            # 如果更名的是当前激活剧本，更新标题
            if folder_name == config.app_config.get("active_profile", ""):
                self.app.title = new_name
                if hasattr(self.app, 'title_label'):
                    self.app.title_label.text = new_name
            popup.dismiss()
            # 刷新 spinner 列表
            self._profile_spinner.values = self.app.get_profile_display_names()
            self._profile_spinner.text = new_name

        btn_cancel.bind(on_release=popup.dismiss)
        btn_confirm.bind(on_release=on_confirm)
        popup.open()

    def _do_switch(self, new_name):
        """v0.6.5: 执行剧本切换 + 刷新 UI"""
        self.app.switch_profile(new_name)
        self.app._show_scene_banner()

    def _make_safe_folder_name(self, display_name):
        """v0.6.5: 将显示名转为安全的英文文件夹名"""
        import hashlib
        if all(ord(c) < 128 for c in display_name):
            s = re.sub(r'[^a-zA-Z0-9_-]', '_', display_name).strip('_').lower()
            return s or "profile"
        h = hashlib.md5(display_name.encode()).hexdigest()[:8]
        return f"profile_{h}"

    def _create_new_profile(self, *args):
        """v0.6.5: 创建新剧本"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text="输入新剧本名称：",
            font_name=config.FONT_DEFAULT,
            halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
            size_hint_y=None, height=dp(26),
        ))
        name_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(42),
            foreground_color=(0.15, 0.12, 0.10, 1), background_color=(0.96, 0.96, 0.96, 1),
            font_size=dp(13), padding=[dp(10), dp(12), dp(10), dp(10)],
            hint_text="例如：星际飞船",
        )
        content.add_widget(name_input)

        btns_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = RoundedButton(
            btn_color="#90a4ae",
            text="取消", size_hint_y=1, size_hint_x=1,
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        confirm_btn = RoundedButton(
            btn_color="#66bb6a",
            text="创建", size_hint_y=1, size_hint_x=1,
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        btns_row.add_widget(cancel_btn)
        btns_row.add_widget(confirm_btn)
        content.add_widget(btns_row)

        popup = Popup(
            title="新建剧本",
            content=content,
            size_hint=(0.8, 0.3),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=False,
        )

        def do_create(instance):
            display_name = name_input.text.strip()
            if not display_name:
                return
            # 生成安全的英文文件夹名
            folder_name = self._make_safe_folder_name(display_name)
            profile_dir = config.PROFILES_DIR / folder_name
            if profile_dir.exists():
                i = 2
                while (config.PROFILES_DIR / f"{folder_name}_{i}").exists():
                    i += 1
                folder_name = f"{folder_name}_{i}"
                profile_dir = config.PROFILES_DIR / folder_name

            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "characters").mkdir(exist_ok=True)
            (profile_dir / "chats").mkdir(exist_ok=True)

            # 默认 config（含 display_name 用于 UI 显示）
            save_json(profile_dir / "config.json", {
                "app": {
                    "display_name": display_name,
                    "title": display_name,
                    "welcome_title": f"欢迎来到{display_name}",
                    "welcome_text": "点击 (开始) 启动对话~",
                    "director_mode": False,
                    "user_mode": False,
                },
                "world": {"setting": ""},
                "turn": {"order": [], "history_size": 8},
                "speed": {"default": 3},
            })
            # 默认场景
            save_json(profile_dir / "scenes.json", [
                {"id": "default", "time": "日常",
                 "location": "",
                 "scene": f"{display_name}的日常场景。请在这里编辑场景描述。",
                 "mood": "普通"}
            ])
            # 默认 You.json
            save_json(profile_dir / "characters" / "You.json", {
                "name": "You",
                "display_name": "你",
                "color": "#42a5f5",
                "bg_color": "#f0f7ff",
                "personality": "你自己",
                "description": "请在这里编辑你的角色描述。",
                "system_prompt": "你是这里的一员，自然地和大家聊天。用*星号*描述动作和表情。回复简短自然，100-200字。",
                "prompt_hint": "is here with you. Talk to them directly."
            })

            popup.dismiss()
            # 刷新下拉列表
            self._profile_spinner.values = self.app.get_profile_display_names()
            self._profile_spinner.text = display_name

        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn.bind(on_release=do_create)
        popup.open()

    def _delete_current_profile(self, *args):
        """v0.7.5: 删除下拉框选中的剧本（优先）或当前激活剧本，自动切换到第一个剩余"""
        # 1. 优先用下拉框选中的剧本，fallback 到当前激活的
        if hasattr(self, '_profile_spinner') and self._profile_spinner.text:
            selected_display = self._profile_spinner.text
            active_folder = self.app.profile_display_to_name(selected_display)
        else:
            active_folder = config.app_config.get("active_profile", "")
        if not active_folder:
            return
        # 安全守卫：至少保留一个剧本
        all_dirs = [d.name for d in config.PROFILES_DIR.iterdir() if d.is_dir()]
        if len(all_dirs) <= 1:
            self.app._set_status("删除失败：必须保留至少一个剧本！", "#ef5350")
            return

        current_display = self.app.profile_name_to_display(active_folder)

        # 2. 二次确认弹窗
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(make_popup_label(
            f"确定要删除当前剧本「{current_display}」吗？\n删除后所有场景、角色及对话将永久丢失！",
            halign="center", valign="middle",
            color=(0.75, 0.70, 0.65, 1), font_size=dp(13),
        ))
        popup = Popup(
            title="危险操作提示", content=content,
            size_hint=(0.85, 0.3), auto_dismiss=False,
            background_color=hex_to_rgba("#fff8f5"),
        )

        def do_delete(instance):
            popup.dismiss()
            self._was_running = False
            try:
                # 3. 物理删除
                target_dir = config.PROFILES_DIR / active_folder
                if target_dir.exists():
                    shutil.rmtree(str(target_dir))
                # 4. 获取第一个剩余剧本
                remaining = [d.name for d in config.PROFILES_DIR.iterdir() if d.is_dir()]
                first_profile = remaining[0]
                # 5. 核心：切换剧本并强刷主界面
                self.app.switch_profile(first_profile)
                self.app._show_scene_banner()
                # 6. 核心：强刷设置弹窗自身
                if hasattr(self, '_profile_spinner'):
                    self._profile_spinner.values = self.app.get_profile_display_names()
                    self._profile_spinner.text = self.app.profile_name_to_display(first_profile)
                # 7. 大招：重构当前标签页，强制所有 TextInput 重新读取新剧本数据
                self._switch_tab(getattr(self, '_current_tab', 'app'))
                self.app._set_status(f"剧本「{current_display}」已删除", "#66bb6a")
            except Exception as e:
                self.app._set_status(f"删除失败: {str(e)}", "#ef5350")

        # 组装按钮
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        def _on_dismiss(instance):
            # 取消时重置下拉框为当前激活剧本
            if hasattr(self, '_profile_spinner'):
                active_display = self.app.profile_name_to_display(
                    config.app_config.get("active_profile", "")
                )
                self._profile_spinner.text = active_display
        popup.bind(on_dismiss=_on_dismiss)
        cancel_btn = RoundedButton(
            btn_color="#90a4ae",
            text="取消",
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn = RoundedButton(
            btn_color="#ef5350",
            text="确定删除",
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        confirm_btn.bind(on_release=do_delete)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)
        content.add_widget(Widget(size_hint_y=1))
        popup.open()

    def _refresh_app_inputs(self):
        """v0.6.5: 等布局完成后注入设置页文本并重置水平滚动（仅当控件已创建时有效）"""
        if not hasattr(self, '_app_title_input'):
            return
        ac = self.app._profile_config.get("app", {})
        self._app_title_input.text = ac.get("title", "")
        self._app_welcome_title.text = ac.get("welcome_title", "")
        self._app_welcome_text.text = ac.get("welcome_text", "")
        if hasattr(self, '_world_input'):
            wc = self.app._profile_config.get("world", {})
            self._world_input.text = wc.get("setting", "")
        self._app_title_input.scroll_x = 0
        self._app_welcome_title.scroll_x = 0
        if hasattr(self, '_app_order_label'):
            effective = self.app._get_effective_order()
            names = []
            for n in effective:
                st = self.app.char_styles.get(n, {})
                names.append(st.get("name", n))
            self._app_order_label.text = " \u2192 ".join(names) if names else "(\u65e0)"
            self._app_order_label.text_size = (self._app_order_label.width - dp(4), None)

    def _save_app_settings(self, *args):
        # v0.6.5: 保存到当前剧本的 config.json
        pc = self.app._profile_config
        old_app = pc.get("app", {})
        pc["app"] = {
            "title": self._app_title_input.text.strip(),
            "welcome_title": self._app_welcome_title.text.strip(),
            "welcome_text": self._app_welcome_text.text.strip(),
            "director_mode": self.app.director_mode,
            "user_mode": self.app.user_mode,
            "display_name": old_app.get("display_name", old_app.get("title", "")),  # v0.8.7: 保留重命名后的名称
        }
        # 保存到 profile 目录（发言顺序在"发言"标签中单独保存）
        wc = pc.get("world", {})
        world_text = self._world_input.text.strip() if hasattr(self, '_world_input') else wc.get("setting", "")
        pc["world"] = {"setting": world_text}
        save_json(self.app.profile_dir / "config.json", pc)
        self.app.title = pc["app"]["title"]
        self.app._set_status("设置已保存", "#66bb6a")

    def _reset_chat(self, *args):
        self.app._do_reset()
        Clock.schedule_once(lambda dt: self.dismiss(), 0.3)

    def _save_chat_log(self, *args):
        self.app._save_log()

    def _copy_chat_log(self, *args):
        self.app._copy_log()

    def _refresh_chat_list(self):
        """刷新对话下拉列表（保存/删除后调用）"""
        if not hasattr(self, '_chat_spinner'):
            return
        self._chat_files = self.app._list_chat_files()
        self._chat_spinner_values = []
        self._chat_spinner_paths = []
        for fp in self._chat_files:
            meta = self.app._read_chat_meta(fp)
            if meta:
                label = f"{meta['title'][:20]}  {meta['created_at'][5:10]}  ({meta['message_count']}条)"
                self._chat_spinner_values.append(label)
                self._chat_spinner_paths.append(fp)
        self._chat_spinner.values = self._chat_spinner_values or ["(无保存的对话)"]
        self._chat_spinner.text = self._chat_spinner_values[0] if self._chat_spinner_values else "(无保存的对话)"

    def _save_chat_from_settings(self, *args):
        """从设置页保存当前对话，保存后刷新列表"""
        self.app.save_current_chat(show_popup=True)
        # 延迟刷新列表（等保存完成+弹窗关闭）
        Clock.schedule_once(lambda dt: self._refresh_chat_list(), 3.5)

    def _load_selected_chat(self, *args):
        """读取选中的对话"""
        sel = self._chat_spinner.text
        if sel == "(无保存的对话)" or sel not in self._chat_spinner_values:
            return
        idx = self._chat_spinner_values.index(sel)
        if idx >= len(self._chat_spinner_paths):
            return
        filepath = self._chat_spinner_paths[idx]

        # 确认弹窗
        meta = self.app._read_chat_meta(filepath)
        title = meta["title"] if meta else "?"

        has_unsaved = bool(self.app.history) and (time.time() - self.app.chat._last_save_time > 30)

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        msg_text = f"读取后将覆盖当前对话。"
        if has_unsaved:
            msg_text += "\n\n当前对话尚未保存！"
        msg_text += f"\n\n「{title}」\n\n确定要读取吗？"
        content.add_widget(make_popup_label(
            msg_text,
            halign="center", valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        ))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8), padding=(dp(8), 0))
        btn_cancel = RoundedButton(
            btn_color="#78909c",
            text="取消",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(11),
        )
        btns.add_widget(btn_cancel)

        if has_unsaved:
            btn_save_read = RoundedButton(
                btn_color="#66bb6a",
                text="保存并读取",
                font_name=config.FONT_DEFAULT,
                color=(1, 1, 1, 1),
                font_size=dp(11),
            )
            btns.add_widget(btn_save_read)

        btn_confirm = RoundedButton(
            btn_color="#ff8a65",
            text="读取",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(11),
        )
        btns.add_widget(btn_confirm)
        content.add_widget(btns)

        popup = Popup(
            title="读取对话",
            content=content,
            size_hint=(0.88, 0.45),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=True,
        )

        def on_confirm(*args):
            popup.dismiss()
            self.dismiss()
            success = self.app.load_chat(filepath)
            if not success:
                Clock.schedule_once(lambda dt: self.app._set_status("读取失败", "#ef5350"), 0.3)

        def on_save_read(*args):
            popup.dismiss()
            self.app.save_current_chat(show_popup=True)
            self.dismiss()
            success = self.app.load_chat(filepath)
            if not success:
                Clock.schedule_once(lambda dt: self.app._set_status("读取失败", "#ef5350"), 0.3)

        btn_cancel.bind(on_release=popup.dismiss)
        btn_confirm.bind(on_release=on_confirm)
        if has_unsaved:
            btn_save_read.bind(on_release=on_save_read)
        popup.open()

    def _rename_selected_chat(self, *args):
        """v0.8.7: 重命名选中的对话"""
        sel = self._chat_spinner.text
        if sel == "(无保存的对话)" or sel not in self._chat_spinner_values:
            return
        idx = self._chat_spinner_values.index(sel)
        if idx >= len(self._chat_spinner_paths):
            return
        filepath = self._chat_spinner_paths[idx]

        meta = self.app._read_chat_meta(filepath)
        old_title = meta["title"] if meta else "?"

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        content.add_widget(Label(
            text=f"重命名对话：\n\n「{old_title}」",
            font_name=config.FONT_DEFAULT,
            halign="center", valign="middle",
            color=(0.55, 0.48, 0.42, 1),
            font_size=dp(13),
            size_hint_y=None, height=dp(50),
        ))
        name_input = TextInput(
            text=old_title,
            multiline=False,
            size_hint_y=None, height=dp(40),
            background_color=(1, 1, 1, 1),
            foreground_color=(0.15, 0.12, 0.10, 1),
            font_size=dp(13),
            padding=(dp(10), dp(8)),
        )
        content.add_widget(name_input)

        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10), padding=(dp(8), 0))
        btn_cancel = RoundedButton(
            btn_color="#78909c",
            text="取消",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btn_confirm = RoundedButton(
            btn_color="#42a5f5",
            text="确认",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_confirm)
        content.add_widget(btns)
        content.add_widget(Widget(size_hint_y=1))

        popup = Popup(
            title="重命名对话",
            content=content,
            size_hint=(0.8, 0.35),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=False,
        )

        _chat_spinner_before = sel
        _confirmed = [False]
        def _on_dismiss(instance):
            if not _confirmed[0] and hasattr(self, '_chat_spinner'):
                self._chat_spinner.text = _chat_spinner_before
        popup.bind(on_dismiss=_on_dismiss)

        def on_confirm(*args):
            _confirmed[0] = True
            new_title = name_input.text.strip()
            if not new_title or new_title == old_title:
                popup.dismiss()
                return
            data = load_json(filepath)
            if data:
                data["title"] = new_title
                data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_json(filepath, data)
            popup.dismiss()
            self._refresh_chat_list()

        btn_cancel.bind(on_release=popup.dismiss)
        btn_confirm.bind(on_release=on_confirm)
        popup.open()

    def _delete_selected_chat(self, *args):
        """删除选中的对话"""
        sel = self._chat_spinner.text
        if sel == "(无保存的对话)" or sel not in self._chat_spinner_values:
            return
        idx = self._chat_spinner_values.index(sel)
        if idx >= len(self._chat_spinner_paths):
            return
        filepath = self._chat_spinner_paths[idx]

        meta = self.app._read_chat_meta(filepath)
        title = meta["title"] if meta else "?"
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(make_popup_label(
            f"确定要删除对话吗？\n\n「{title}」\n\n此操作不可撤销。",
            halign="center", valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        ))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12), padding=(dp(16), 0))
        btn_cancel = RoundedButton(
            btn_color="#78909c",
            text="取消",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btn_confirm = RoundedButton(
            btn_color="#ef5350",
            text="删除",
            font_name=config.FONT_DEFAULT,
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_confirm)
        content.add_widget(btns)
        content.add_widget(Widget(size_hint_y=1))

        popup = Popup(
            title="删除对话",
            content=content,
            size_hint=(0.85, 0.32),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=False,
        )

        _chat_spinner_before = sel
        _confirmed = [False]
        def _on_dismiss(instance):
            if not _confirmed[0] and hasattr(self, '_chat_spinner'):
                self._chat_spinner.text = _chat_spinner_before
        popup.bind(on_dismiss=_on_dismiss)

        def on_confirm(*args):
            _confirmed[0] = True
            popup.dismiss()
            self.app.delete_chat(filepath)
            self._refresh_chat_list()

        btn_cancel.bind(on_release=popup.dismiss)
        btn_confirm.bind(on_release=on_confirm)
        popup.open()
