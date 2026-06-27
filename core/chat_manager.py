# -*- coding: utf-8 -*-
"""
Dorm Life - 对话存档管理器 (extracted from main.py 2026-06-27)
  ChatManager: 保存/读取/删除/自动存档 + AI 标题生成
"""

import time
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import load_json, save_json, extract_json, hex_to_rgba, make_popup_label
from api_service import call_chat_completion_async


class ChatManager:
    """对话存档管理 — 注入到 DormApp 中"""

    def __init__(self, app):
        self.app = app
        self._loaded_chat_path = None   # 记录加载的对话路径，保存时覆盖
        self._last_save_time = 0.0      # 上次保存时间戳
        self._last_autosave_len = 0     # 上次自动存档时的消息数
        self._saving_popup = None       # 保存中弹窗引用

    @property
    def chats_dir(self):
        """当前剧本的对话存档目录"""
        return self.app.profile_dir / "chats" if self.app.profile_dir else None

    def _ensure_chats_dir(self):
        """确保 chats/ 目录存在"""
        if self.chats_dir and not self.chats_dir.exists():
            self.chats_dir.mkdir(parents=True, exist_ok=True)

    def _list_chat_files(self):
        """v0.8.7: 列出对话文件，按文件名时间戳倒序（新的在前），兼容安卓 st_mtime 不准"""
        if not self.chats_dir or not self.chats_dir.exists():
            return []
        files = list(self.chats_dir.glob("chat_*.json"))
        import re as _re
        def _sort_key(fp):
            m = _re.search(r'chat_(\d{8}_\d{6})', fp.name)
            if m:
                return m.group(1)
            return "00000000_000000"
        files.sort(key=_sort_key, reverse=True)
        return files

    def _read_chat_meta(self, filepath):
        """读取对话文件的元信息（title, message_count, created_at）"""
        try:
            data = load_json(filepath)
            return {
                "title": data.get("title", filepath.stem),
                "message_count": data.get("message_count", 0),
                "created_at": data.get("created_at", ""),
            }
        except Exception:
            return None

    def _save_chat_to_file(self, filepath, title):
        """将当前对话写入文件"""
        data = {
            "title": title,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": len(self.app.history),
            "scene_idx": self.app.scene_idx,
            "turn_idx": self.app.turn_idx,
            "turn_count": self.app.turn_count,
            "history": list(self.app.history),
        }
        return save_json(filepath, data)

    def _generate_chat_title(self, callback):
        """AI 生成对话标题（后台线程），完成后调用 callback(title)"""
        recent = self.app.history[-6:] if len(self.app.history) >= 4 else self.app.history[:]
        if not recent or not config.API_KEY:
            callback(self._fallback_chat_title())
            return

        lines = []
        for m in recent:
            name = m.get("display_name", m.get("name", "?"))
            txt = m.get("text", "")[:80]
            lines.append(f"{name}: {txt}")

        lines_str = "\n".join(lines)
        prompt = f"""根据以下对话片段，生成一个简短标题（5-15字），概括这段对话的主题。

{lines_str}

返回纯JSON：{{"title":"标题"}}"""

        def _on_title_result(content):
            result, err = extract_json(content)
            if result and result.get("title"):
                callback(result["title"].strip())
            else:
                print(f"[AI标题生成] JSON提取失败: {err}, 原始返回: {content}")
                callback(self._fallback_chat_title())

        def _on_title_error(err):
            print(f"[AI标题生成] API异常: {err}")
            callback(self._fallback_chat_title())

        call_chat_completion_async(
            messages=[
                {"role": "system", "content": "你是一个对话标题生成器，只返回JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=300,
            timeout=15.0,
            on_result=_on_title_result,
            on_error=_on_title_error,
        )

    def _fallback_chat_title(self):
        """AI 不可用时的备选标题：剧本名 - 场景 - 时间"""
        ac = self.app._profile_config.get("app", {})
        profile_name = ac.get("display_name", ac.get("title", self.app.title))
        scene_time = self.app.scenes[self.app.scene_idx].get("time", "") if self.app.scenes and self.app.scene_idx < len(self.app.scenes) else ""
        now = datetime.now().strftime("%H:%M")
        parts = [profile_name]
        if scene_time:
            parts.append(scene_time)
        parts.append(now)
        return " - ".join(parts)

    def save_current_chat(self, show_popup=True):
        """保存当前对话（含 AI 标题生成 + 弹窗反馈）"""
        if not self.app.history:
            if show_popup:
                self._show_save_result_popup("没有对话内容可保存", False)
            return

        self._ensure_chats_dir()
        if self._loaded_chat_path is not None:
            filepath = self._loaded_chat_path
            self._loaded_chat_path = None
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{ts}.json"
            filepath = self.chats_dir / filename

        saved_data = {
            "title": "保存中...",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": len(self.app.history),
            "scene_idx": self.app.scene_idx,
            "turn_idx": self.app.turn_idx,
            "turn_count": self.app.turn_count,
            "history": list(self.app.history),
        }
        save_json(filepath, saved_data)

        _caller_profile = config.app_config.get("active_profile", "")

        def _on_title_ready(title):
            if config.app_config.get("active_profile", "") != _caller_profile:
                return
            saved_data["title"] = title
            saved_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json(filepath, saved_data)
            self._last_save_time = time.time()
            self._clear_autosave()
            if show_popup:
                Clock.schedule_once(
                    lambda dt: self._show_save_result_popup(title, True), 0.1
                )

        if show_popup:
            self._show_saving_popup()
        self._generate_chat_title(_on_title_ready)

    def _show_saving_popup(self):
        """显示「正在保存…」弹窗"""
        content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(12))
        content.add_widget(make_popup_label(
            "正在保存...\nAI 正在生成对话标题...",
            halign="center", valign="middle",
            color=(0.55, 0.48, 0.42, 1),
            font_size=dp(14),
        ))
        popup = Popup(
            title="保存对话",
            content=content,
            size_hint=(0.75, 0.3),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=True,
        )
        self._saving_popup = popup
        popup.open()

    def _show_save_result_popup(self, title, success):
        """显示保存结果弹窗"""
        if self._saving_popup:
            try:
                self._saving_popup.dismiss()
            except Exception:
                pass
        self._saving_popup = None

        if success:
            popup_text = f"保存成功\n\n标题：{title}"
        else:
            popup_text = "保存失败"
        content = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
        content.add_widget(make_popup_label(
            popup_text,
            halign="center", valign="middle",
            color=(0.55, 0.48, 0.42, 1),
            font_size=dp(14),
        ))
        btn = Button(
            text="确定", size_hint_y=None, height=dp(40),
            background_normal="", background_color=hex_to_rgba("#66bb6a"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        content.add_widget(btn)
        popup = Popup(
            title="保存对话",
            content=content,
            size_hint=(0.75, 0.35),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=True,
        )
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def load_chat(self, filepath):
        """读取对话文件，恢复历史 + UI"""
        app = self.app
        data = load_json(filepath)
        if not data or "history" not in data:
            app._set_status("对话文件损坏", "#ef5350")
            return False

        app._do_stop()
        app.history = data.get("history", [])
        app.turn_idx = data.get("turn_idx", 0)
        app.turn_count = data.get("turn_count", 0)
        app.message_count = data.get("message_count", len(app.history))
        app._char_last_turn = {}
        for i, entry in enumerate(reversed(app.history)):
            name = entry.get("name", "")
            if name and name not in app._char_last_turn:
                app._char_last_turn[name] = app.turn_count - i
        app._suggested_next = None
        saved_scene = data.get("scene_idx", 0)
        if saved_scene < len(app.scenes):
            app.scene_idx = saved_scene

        app.chat_view.clear()
        for entry in app.history:
            name = entry.get("name", "?")
            dname = entry.get("display_name", name)
            text = entry.get("text", "")
            t = entry.get("time", "")
            msg_type = entry.get("type", "normal")
            color = "#2e7d32" if msg_type == "director" else app.char_styles.get(name, {}).get("color", "#888")
            app.chat_view.add_message(
                name=name, dname=dname, text=text, t=t,
                color=color, msg_type=msg_type,
            )

        app._update_scene_label()
        app._hide_scene_banner()
        app.msg_label.text = f" {app.message_count}条"
        app.btn_start_pause.text = "开始"
        app.btn_start_pause.btn_color = "#66bb6a"
        app.btn_start_pause.set_btn_color("#66bb6a")
        self._loaded_chat_path = filepath
        app._set_status(f"已加载: {data.get('title', '?')}", "#66bb6a")
        return True

    def delete_chat(self, filepath):
        """删除对话文件"""
        try:
            filepath.unlink()
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            return False

    def _auto_save(self):
        """v0.8.7: 每次暂停 / app 切后台时自动存档（静默，不调 AI 标题）"""
        if not self.app.history:
            return

        self._ensure_chats_dir()
        if not self.chats_dir:
            return

        filepath = self.chats_dir / "_autosave.json"
        title = self._fallback_chat_title()
        self._save_chat_to_file(filepath, title)
        self._last_autosave_len = len(self.app.history)
        self._last_save_time = time.time()

    def _clear_autosave(self):
        """删除自动存档文件（用户已手动保存）"""
        if not self.chats_dir:
            return
        p = self.chats_dir / "_autosave.json"
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    def check_autosave_on_start(self):
        """启动时检测是否有自动存档，有则弹窗询问恢复"""
        if not self.chats_dir:
            return
        p = self.chats_dir / "_autosave.json"
        if not p.exists():
            return

        data = load_json(p)
        if not data or not data.get("history"):
            try:
                p.unlink()
            except Exception:
                pass
            return

        msg_count = data.get("message_count", 0)
        title = data.get("title", "自动存档")

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(make_popup_label(
            f"检测到上次未保存的对话\n\n「{title}」\n{msg_count}条消息\n\n是否恢复？",
            halign="center", valign="middle",
            color=(0.55, 0.48, 0.42, 1),
            font_size=dp(13),
        ))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(12), padding=(dp(16), 0))
        btn_discard = Button(
            text="放弃",
            font_name=config.FONT_DEFAULT,
            background_normal="", background_color=hex_to_rgba("#78909c"),
            color=(1, 1, 1, 1), font_size=dp(12),
        )
        btn_restore = Button(
            text="恢复",
            font_name=config.FONT_DEFAULT,
            background_normal="", background_color=hex_to_rgba("#66bb6a"),
            color=(1, 1, 1, 1), font_size=dp(12), bold=True,
        )
        btns.add_widget(btn_discard)
        btns.add_widget(btn_restore)
        content.add_widget(btns)

        popup = Popup(
            title="恢复对话",
            content=content,
            size_hint=(0.85, 0.4),
            background_color=hex_to_rgba("#fff8f5"),
            auto_dismiss=False,
        )

        def on_discard(*args):
            popup.dismiss()
            try:
                p.unlink()
            except Exception:
                pass

        def on_restore(*args):
            popup.dismiss()
            self.load_chat(p)
            self._clear_autosave()

        btn_discard.bind(on_release=on_discard)
        btn_restore.bind(on_release=on_restore)
        popup.open()
