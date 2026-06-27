# -*- coding: utf-8 -*-
"""SettingsPopup — AI 辅助功能 (prompt 构建 / API 调用 / 生成逻辑)"""

import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hex_color

import config
from utils import load_json, save_json, hex_to_rgba, extract_json
from ui.theme import theme
from api_service import call_chat_completion_async


class AIMixin:
    """AI 辅助 — prompt 构建、API 调用、AI 填充/生成/创建剧本"""

    # ── 通用工具 ──

    def _get_world_context(self):
        """读取当前剧本的世界观设定"""
        wc = self.app._profile_config.get("world", {})
        return wc.get("setting", "")

    def _do_ai_call(self, prompt, on_done, show_loading=True, max_tokens=800):
        """在后台线程执行 AI API 调用。show_loading=False 时不弹加载窗（批量调用用）"""
        key = config.resolve_key()
        if not key:
            Clock.schedule_once(lambda dt: on_done(None, "请先在API设置中配置API Key"))
            return
        loading_popup = None
        if show_loading:
            loading_content = BoxLayout(orientation="vertical", padding=dp(24))
            loading_content.add_widget(Label(
                text="AI处理中，请稍候…",
                font_name=config.FONT_DEFAULT, halign="center", valign="middle",
                color=(0.4, 0.4, 0.4, 1), font_size=dp(14),
            ))
            loading_popup = Popup(
                title="请稍候", content=loading_content,
                size_hint=(0.55, 0.18), auto_dismiss=False,
                background_color=hex_to_rgba("#fff8f5"),
            )
            loading_popup.open()
        _caller_profile = config.app_config.get("active_profile", "")
        def _dismiss_loading():
            if loading_popup:
                loading_popup.dismiss()
        def _on_result(content):
            if config.app_config.get("active_profile", "") != _caller_profile:
                _dismiss_loading()
                return
            result, err = extract_json(content)
            _dismiss_loading()
            on_done(result, content if err else None)
        def _on_error(err):
            _dismiss_loading()
            on_done(None, str(err))
        call_chat_completion_async(
            messages=[{"role": "user", "content": prompt}],
            api_key=key,
            temperature=0.7,
            max_tokens=max_tokens,
            on_result=_on_result,
            on_error=_on_error,
        )

    def _show_ai_raw_popup(self, title, raw_text):
        """弹窗显示AI原始返回（JSON解析失败时供用户手动复制）"""
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        content.add_widget(Label(
            text="AI返回无法自动解析，请手动复制：",
            font_name=config.FONT_DEFAULT, halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1), font_size=dp(12),
            size_hint_y=None, height=dp(24),
        ))
        raw_label = TextInput(
            text=raw_text or "", readonly=True, multiline=True,
            foreground_color=(0.15, 0.12, 0.10, 1),
            background_color=(0.96, 0.96, 0.96, 1),
            font_size=dp(10),
        )
        content.add_widget(raw_label)
        close_btn = Button(
            text="关闭", size_hint_y=None, height=dp(36),
            background_normal="", background_color=hex_to_rgba("#78909c"),
            color=(1, 1, 1, 1),
        )
        popup = Popup(
            title=title, content=content,
            size_hint=(0.9, 0.7), auto_dismiss=True,
            background_color=hex_to_rgba("#fff8f5"),
        )
        close_btn.bind(on_release=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    # ── Prompt 构建 ──

    def _build_scene_ai_prompt(self, fill_mode, user_input="", world_override=None):
        """构建场景AI提示词。fill_mode=True=补全模式, False=生成模式"""
        world = world_override if world_override is not None else self._get_world_context()
        if fill_mode:
            t = self._sc_time_input.text.strip() or "未填写"
            l = self._sc_location_input.text.strip() or "未填写"
            m = self._sc_mood_input.text.strip() or "未填写"
            s = self._sc_desc_input.text.strip() or "未填写"
            world_line = f"【世界观】\n{world}\n\n" if world else ""
            return f"""你是一个场景设计师。根据已填信息补全或优化场景设置。

{world_line}【已有信息】
- 时间：{t}
- 地点：{l}
- 氛围：{m}
- 场景描述：{s}
（标注"未填写"的字段请根据已填字段合理推断，全部未填则自由发挥）

【字段说明】
- time（时间）：简洁的时间段名称，2-6字
- location（地点）：具体地点名称，2-6字
- mood（氛围）：氛围标签，2-4字
- scene（场景描述）：80-150字，像小说段落。必须包含光线、声音、气味中的至少两种感官描写，让读者有身临其境的感觉

【规则】
1. 已填字段可以优化润色，未填字段合理补全
2. 所有字段风格统一，互相呼应
3. 根据已有信息推断场景的时代和世界观

【输出格式】只返回纯JSON，不要```代码块，不要任何解释：
{{"time":"...","location":"...","mood":"...","scene":"..."}}"""
        else:
            world_line = f"【世界观】\n{world}\n\n" if world else ""
            return f"""你是一个场景设计师。根据一句话描述，创建一个完整的场景。

{world_line}【用户输入】
{user_input}

请根据这句话，补全以下所有字段：
- time（时间）：简洁的时间段名称，2-6字
- location（地点）：具体地点名称，2-6字
- mood（氛围）：氛围标签，2-4字
- scene（场景描述）：80-150字，像小说段落。必须包含光线、声音、气味中的至少两种感官描写，让读者有身临其境的感觉

【规则】
1. 根据输入推断场景的时代和世界观
2. 所有字段风格统一，互相呼应
3. scene 要生动有沉浸感

【输出格式】只返回纯JSON，不要```代码块，不要任何解释：
{{"time":"...","location":"...","mood":"...","scene":"..."}}"""

    def _build_char_ai_prompt(self, fill_mode, user_input="", world_override=None):
        """构建角色AI提示词。fill_mode=True=补全模式, False=生成模式"""
        world = world_override if world_override is not None else self._get_world_context()
        if fill_mode:
            n = self._ch_inputs["name"].text.strip() or "未填写"
            d = self._ch_inputs["dname"].text.strip() or "未填写"
            c = self._ch_inputs["color"].text.strip() or "未填写"
            b = self._ch_inputs["bg"].text.strip() or "未填写"
            p = self._ch_personality.text.strip() or "未填写"
            desc = self._ch_desc.text.strip() or "未填写"
            sp = self._ch_prompt.text.strip() or "未填写"
            world_line = f"【世界观】\n{world}\n\n" if world else ""
            return f"""你是一个角色设计师。根据已填信息补全或优化角色设定。

{world_line}【已有信息】
- 英文名：{n}
- 显示名：{d}
- 颜色：{c}
- 背景色：{b}
- 性格：{p}
- 描述：{desc}
- 系统提示：{sp}
（标注"未填写"的字段请根据已填字段合理推断，全部未填则自由发挥）

【字段说明】
- name：英文名，首字母大写，2-5字母
- display_name：中文显示名，2-3字，与英文名音译或意译对应
- color：主题色hex。根据性格气质选择柔和色调
- bg_color：背景色hex。必须比color浅很多，用于聊天气泡底色
- personality：性格标签，2-4字
- description：外貌特征简述，20-40字。包含发色发型、眼睛、肤色、身材等
- system_prompt：完整角色人设，按以下结构组织：
  1. 外在形象：外貌、穿着
  2. 性格：核心性格 + 展开描述
  3. 语气风格：说话方式、常用语气词
  4. 表达方式：对话内容用直角引号「」包裹，动作描写用*星号*包裹。给出示例
  5. 背景：角色所处的环境/世界，与其他角色的关系
  6. 规则：回复100-200字、描述动作表情、延续话题、特质自然融入对话

【输出格式】只返回纯JSON，不要```代码块，不要任何解释。
重要：system_prompt 必须是单行字符串——换行用\\n。
【引号规则】所有文本内容中如需引用、强调、书名等，一律使用中文引号「」或单引号''，绝对不要使用英文双引号"，否则JSON解析会崩溃！
{{"name":"...","display_name":"...","color":"...","bg_color":"...","personality":"...","description":"...","system_prompt":"..."}}"""
        else:
            world_line = f"【世界观】\n{world}\n\n" if world else ""
            return f"""你是一个角色设计师。根据一句话描述，创建一个完整的角色。

{world_line}【用户输入】
{user_input}

请根据这句话，补全以下所有字段：
- name：英文名，首字母大写，2-5字母
- display_name：中文显示名，2-3字，与英文名音译或意译对应
- color：主题色hex。根据性格气质选择柔和色调
- bg_color：背景色hex。必须比color浅很多，用于聊天气泡底色
- personality：性格标签，2-4字
- description：外貌特征简述，20-40字。包含发色发型、眼睛、肤色、身材等
- system_prompt：完整角色人设，按以下结构组织：
  1. 外在形象：外貌、穿着
  2. 性格：核心性格 + 展开描述
  3. 语气风格：说话方式、常用语气词
  4. 表达方式：对话内容用直角引号「」包裹，动作描写用*星号*包裹。给出示例
  5. 背景：角色所处的环境/世界，与其他角色的关系
  6. 规则：回复100-200字、描述动作表情、延续话题、特质自然融入对话

【输出格式】只返回纯JSON，不要```代码块，不要任何解释。
重要：system_prompt 必须是单行字符串——换行用\\n。
【引号规则】所有文本内容中如需引用、强调、书名等，一律使用中文引号「」或单引号''，绝对不要使用英文双引号"，否则JSON解析会崩溃！
{{"name":"...","display_name":"...","color":"...","bg_color":"...","personality":"...","description":"...","system_prompt":"..."}}"""

    def _build_you_ai_prompt(self, hint, world):
        """构建 You 角色的专用 AI 提示词。You 是用户化身，需要代入感。"""
        world_line = f"【世界观】\n{world}\n\n" if world else ""
        return f"""你是一个角色设计师。为用户角色（You）创建设定。

{world_line}【角色提示】
{hint}

You 是用户在这个世界中的化身——一个有具体身份的角色，不是旁观者。
让用户通过它真正融入这个世界。

请生成：
- display_name：中文名，默认"你"，身份特殊可调整，3字以内
- color：主题色hex，推荐蓝色系如 #42a5f5
- bg_color：背景色hex，极浅，如 #f0f7ff
- personality：性格标签，2-4字
- description：身份/外貌简述，15-30字
- system_prompt：角色人设：
  1. 身份定位：在这个世界中的具体角色
  2. 语气风格：自然真实
  3. 表达方式：对话内容用直角引号「」包裹，动作描写用*星号*包裹。给出示例
  4. 规则：回复100-200字、描述动作表情、延续话题、特质自然融入

返回JSON：
{{"display_name":"你","color":"#42a5f5","bg_color":"#f0f7ff","personality":"...","description":"...","system_prompt":"..."}}
system_prompt必须单行，换行用\\n。name固定为You。
【引号规则】所有文本内容中如需引用或强调，一律使用中文引号「」或单引号''，绝对不要使用英文双引号"，否则JSON解析会崩溃！"""

    def _build_app_settings_prompt(self, brief, world):
        """构建应用设置AI提示词（自动化用）"""
        return f"""你是一个应用设置设计师。根据世界观和描述，生成应用设置。

【世界观】{world}
【描述】{brief}

请生成：
- title：应用标题，5-15字
- welcome_title：欢迎标题，5-15字
- welcome_text：欢迎文字，20-50字，有画面感

返回JSON：{{"title":"...","welcome_title":"...","welcome_text":"..."}}"""

    # ── 场景 AI ──

    def _ai_fill_scene(self, *args):
        """AI补全当前场景的空白/不完善字段"""
        prompt = self._build_scene_ai_prompt(fill_mode=True)
        def _done(result, err):
            if result:
                if result.get("time"):
                    self._sc_time_input.text = result["time"]
                if result.get("location"):
                    self._sc_location_input.text = result["location"]
                if result.get("mood"):
                    self._sc_mood_input.text = result["mood"]
                if result.get("scene"):
                    self._sc_desc_input.text = result["scene"]
            elif err:
                self._show_ai_raw_popup("AI补全场景 - 原始返回", err)
        self._do_ai_call(prompt, _done)

    def _ai_gen_scene(self, *args):
        """AI生成场景：弹窗输入一句话 → AI生成完整场景 → 添加"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text="输入一句话描述想要的场景：",
            font_name=config.FONT_DEFAULT, halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1), font_size=dp(13),
            size_hint_y=None, height=dp(26),
        ))
        desc_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(42),
            foreground_color=(0.15, 0.12, 0.10, 1),
            background_color=(0.96, 0.96, 0.96, 1),
            font_size=dp(13), padding=[dp(10), dp(12)],
            hint_text="例如：深夜的图书馆自习室",
        )
        content.add_widget(desc_input)
        popup = Popup(
            title="AI生成场景", content=content,
            size_hint=(0.85, None), height=dp(240), auto_dismiss=False,
            background_color=hex_to_rgba("#fff8f5"),
        )
        def _do_gen(instance):
            u = desc_input.text.strip()
            if not u:
                return
            popup.dismiss()
            prompt = self._build_scene_ai_prompt(fill_mode=False, user_input=u)
            def _done(result, err):
                if result:
                    time_val = result.get("time", "新场景")
                    existing_times = {s.get("time", "") for s in self.app.scenes}
                    if time_val in existing_times:
                        base = time_val
                        suffix = 2
                        while f"{base}({suffix})" in existing_times:
                            suffix += 1
                        time_val = f"{base}({suffix})"
                    self.app.scenes.append({
                        "time": time_val,
                        "location": result.get("location", ""),
                        "mood": result.get("mood", "普通"),
                        "scene": result.get("scene", "…"),
                    })
                    self.app._save_scenes()
                    self._refresh_scene_spinner()
                    self._scene_spinner.text = time_val
                    self._load_scene_fields(self.app.scenes[-1])
                elif err:
                    self._show_ai_raw_popup("AI生成场景 - 原始返回", err)
            self._do_ai_call(prompt, _done)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = Button(
            text="取消", background_normal="", background_color=hex_to_rgba("#90a4ae"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn = Button(
            text="生成", background_normal="", background_color=hex_to_rgba("#7e57c2"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        confirm_btn.bind(on_release=_do_gen)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)
        # 弹性空间：把内容推到顶部，消除空档
        content.add_widget(Widget(size_hint_y=1))
        popup.open()

    # ── 角色 AI ──

    def _ai_fill_char(self, *args):
        """AI补全当前角色的空白/不完善字段"""
        prompt = self._build_char_ai_prompt(fill_mode=True)
        def _done(result, err):
            if result:
                if result.get("name"):
                    self._ch_inputs["name"].text = result["name"]
                if result.get("display_name"):
                    self._ch_inputs["dname"].text = result["display_name"]
                if result.get("color"):
                    self._ch_inputs["color"].text = result["color"]
                if result.get("bg_color"):
                    self._ch_inputs["bg"].text = result["bg_color"]
                if result.get("personality"):
                    self._ch_personality.text = result["personality"]
                if result.get("description"):
                    self._ch_desc.text = result["description"]
                if result.get("system_prompt"):
                    self._ch_prompt.text = result["system_prompt"]
            elif err:
                self._show_ai_raw_popup("AI补全角色 - 原始返回", err)
        self._do_ai_call(prompt, _done)

    def _ai_gen_char(self, *args):
        """AI生成角色：弹窗输入一句话 → AI生成完整角色 → 创建"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text="输入一句话描述想要的角色：",
            font_name=config.FONT_DEFAULT, halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1), font_size=dp(13),
            size_hint_y=None, height=dp(26),
        ))
        desc_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(42),
            foreground_color=(0.15, 0.12, 0.10, 1),
            background_color=(0.96, 0.96, 0.96, 1),
            font_size=dp(13), padding=[dp(10), dp(12)],
            hint_text="例如：一个傲娇的短发运动系女生",
        )
        content.add_widget(desc_input)
        popup = Popup(
            title="AI生成角色", content=content,
            size_hint=(0.85, None), height=dp(240), auto_dismiss=False,
            background_color=hex_to_rgba("#fff8f5"),
        )
        def _do_gen(instance):
            u = desc_input.text.strip()
            if not u:
                return
            popup.dismiss()
            prompt = self._build_char_ai_prompt(fill_mode=False, user_input=u)
            def _done(result, err):
                if result:
                    name = result.get("name", "NewChar")
                    if name in self.app.characters:
                        base = name
                        suffix = 2
                        while f"{base}{suffix}" in self.app.characters:
                            suffix += 1
                        name = f"{base}{suffix}"
                    char_data = {
                        "name": name,
                        "display_name": result.get("display_name", name),
                        "color": result.get("color", "#888888"),
                        "bg_color": result.get("bg_color", "#f5f5f5"),
                        "personality": result.get("personality", "待设定"),
                        "description": result.get("description", ""),
                        "system_prompt": result.get("system_prompt", ""),
                    }
                    self.app._save_character(name + ".json", char_data)
                    if name not in self.app.turn_order:
                        self.app.turn_order.append(name)
                    self.app._save_turn_order()
                    self.app._reload_data()
                    self._refresh_char_spinner()
                    self._char_spinner.text = name
                    self._load_char_fields(name)
                elif err:
                    self._show_ai_raw_popup("AI生成角色 - 原始返回", err)
            self._do_ai_call(prompt, _done)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = Button(
            text="取消", background_normal="", background_color=hex_to_rgba("#90a4ae"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn = Button(
            text="生成", background_normal="", background_color=hex_to_rgba("#7e57c2"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        confirm_btn.bind(on_release=_do_gen)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)
        # 弹性空间：把内容推到顶部，消除空档
        content.add_widget(Widget(size_hint_y=1))
        popup.open()

    # ── 设置 AI ──

    def _ai_infer_world(self, *args):
        """AI根据现有场景和角色推断世界观"""
        scenes_info = []
        for s in self.app.scenes:
            parts = [s.get('time',''), s.get('location',''), s.get('mood',''), s.get('scene','')]
            scenes_info.append(' | '.join(p for p in parts if p))
        chars_info = []
        for name, c in self.app.characters.items():
            if name != "You":
                chars_info.append(f"{c.get('display_name', name)}：{c.get('personality','')}，{c.get('description','')}")
        prompt_lines = ["根据以下场景和角色信息，推断这个世界的大背景/世界观（50-200字）。"]
        if scenes_info:
            prompt_lines.append("【关联场景】\n" + "\n".join(scenes_info))
        if chars_info:
            prompt_lines.append("【角色设定】\n" + "\n".join(chars_info))
        prompt_lines.append('描述要像小说开篇的世界介绍，概括时空、氛围、特色。')
        prompt_lines.append('返回JSON：{"world":"世界观描述"}')
        def _done(result, err):
            if result and result.get("world"):
                self._world_input.text = result["world"]
            elif err:
                self._show_ai_raw_popup("AI推断世界观 - 原始返回", err)
        self._do_ai_call("\n".join(prompt_lines), _done)

    def _ai_fill_app_settings(self, *args):
        """AI补全应用设置（标题、欢迎标题、欢迎文字）"""
        world = self._world_input.text.strip() or "未设定"
        scenes_summary = ", ".join([s.get('time','') for s in self.app.scenes[:4]])
        chars_summary = ", ".join([
            c.get('display_name', n) for n, c in self.app.characters.items() if n != "You"
        ][:4])
        prompt = f"""根据世界观和已有内容，补全应用设置。

【世界观】{world}
【场景】{scenes_summary or '暂无'}
【角色】{chars_summary or '暂无'}

请补全：
- title：应用标题，5-15字
- welcome_title：欢迎标题，5-15字
- welcome_text：欢迎文字，20-50字，有画面感

返回JSON：{{"title":"...","welcome_title":"...","welcome_text":"..."}}"""
        def _done(result, err):
            if result:
                if result.get("title"):
                    self._app_title_input.text = result["title"]
                if result.get("welcome_title"):
                    self._app_welcome_title.text = result["welcome_title"]
                if result.get("welcome_text"):
                    self._app_welcome_text.text = result["welcome_text"]
            elif err:
                self._show_ai_raw_popup("AI补全设置 - 原始返回", err)
        self._do_ai_call(prompt, _done)

    def _ai_gen_app_settings(self, *args):
        """AI生成设置：弹窗输入一句话 → 生成世界观+标题+欢迎"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text="输入一句话描述剧本主题：",
            font_name=config.FONT_DEFAULT, halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1), font_size=dp(13),
            size_hint_y=None, height=dp(26),
        ))
        desc_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(42),
            foreground_color=(0.15, 0.12, 0.10, 1),
            background_color=(0.96, 0.96, 0.96, 1),
            font_size=dp(13), padding=[dp(10), dp(12)],
            hint_text="例如：星际飞船上的船员日常",
        )
        content.add_widget(desc_input)
        popup = Popup(
            title="AI生成设置", content=content,
            size_hint=(0.85, None), height=dp(240), auto_dismiss=False,
            background_color=hex_to_rgba("#fff8f5"),
        )
        def _do_gen(instance):
            u = desc_input.text.strip()
            if not u:
                return
            popup.dismiss()
            prompt = f"""根据一句话创建完整应用设置。

【用户输入】{u}

请生成：
- title：应用标题，5-15字
- welcome_title：欢迎标题，5-15字
- welcome_text：欢迎文字，20-50字，有画面感
- world：世界大背景描述，50-150字

返回JSON：{{"title":"...","welcome_title":"...","welcome_text":"...","world":"..."}}"""
            def _done(result, err):
                if result:
                    if result.get("title"):
                        self._app_title_input.text = result["title"]
                    if result.get("welcome_title"):
                        self._app_welcome_title.text = result["welcome_title"]
                    if result.get("welcome_text"):
                        self._app_welcome_text.text = result["welcome_text"]
                    if result.get("world"):
                        self._world_input.text = result["world"]
                elif err:
                    self._show_ai_raw_popup("AI生成设置 - 原始返回", err)
            self._do_ai_call(prompt, _done)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = Button(
            text="取消", background_normal="", background_color=hex_to_rgba("#90a4ae"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn = Button(
            text="生成", background_normal="", background_color=hex_to_rgba("#7e57c2"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        confirm_btn.bind(on_release=_do_gen)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)
        content.add_widget(Widget(size_hint_y=1))
        popup.open()

    # ── AI 一键创建剧本 ──

    def _ai_create_profile(self, *args):
        """AI一键创建剧本：弹窗输入一句话 → 生成规划 → 并行生成所有内容"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text="输入一句话描述想要的剧本：",
            font_name=config.FONT_DEFAULT, halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1), font_size=dp(13),
            size_hint_y=None, height=dp(26),
        ))
        desc_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(42),
            foreground_color=(0.15, 0.12, 0.10, 1),
            background_color=(0.96, 0.96, 0.96, 1),
            font_size=dp(13), padding=[dp(10), dp(12)],
            hint_text="例如：星际飞船上的船员日常",
        )
        content.add_widget(desc_input)
        popup = Popup(
            title="AI创建剧本", content=content,
            size_hint=(0.85, None), height=dp(240), auto_dismiss=False,
            background_color=hex_to_rgba("#fff8f5"),
        )
        def _do_create(instance):
            u = desc_input.text.strip()
            if not u:
                return
            if self.app.history:
                popup.dismiss()
                from kivy.uix.popup import Popup as P
                wc = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
                wc.add_widget(Label(
                    text="AI创建剧本将清空当前全部对话记录。\n\n确定要继续吗？",
                    font_name=config.FONT_DEFAULT, halign="center", valign="middle",
                    color=(0.75, 0.70, 0.65, 1), font_size=dp(13),
                ))
                wb = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8), padding=(dp(8), 0))
                btn_no = Button(text="取消", font_name=config.FONT_DEFAULT,
                    background_normal="", background_color=hex_to_rgba("#78909c"),
                    color=(1,1,1,1), font_size=dp(11))
                btn_yes = Button(text="继续创建", font_name=config.FONT_DEFAULT,
                    background_normal="", background_color=hex_to_rgba("#ef5350"),
                    color=(1,1,1,1), font_size=dp(11), bold=True)
                wb.add_widget(btn_no)
                wb.add_widget(btn_yes)
                wc.add_widget(wb)
                wc.add_widget(Widget(size_hint_y=1))
                warn = P(title="确认操作", content=wc, size_hint=(0.85, 0.35),
                    background_color=hex_to_rgba("#fff8f5"), auto_dismiss=False)
                def on_yes(*a):
                    warn.dismiss()
                    self._run_ai_create_profile(u)
                btn_no.bind(on_release=warn.dismiss)
                btn_yes.bind(on_release=on_yes)
                warn.open()
                return
            popup.dismiss()
            self._run_ai_create_profile(u)
        btn_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = Button(
            text="取消", background_normal="", background_color=hex_to_rgba("#90a4ae"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        cancel_btn.bind(on_release=popup.dismiss)
        confirm_btn = Button(
            text="生成", background_normal="", background_color=hex_to_rgba("#7e57c2"),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        confirm_btn.bind(on_release=_do_create)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)
        content.add_widget(Widget(size_hint_y=1))
        popup.open()

    def _run_ai_create_profile(self, user_input):
        """执行AI创建剧本流程：规划 → 并行生成 → 写入"""
        _caller_profile = config.app_config.get("active_profile", "")

        # 进度弹窗
        prog_label = Label(
            text="AI创建中…(生成规划)",
            font_name=config.FONT_DEFAULT, halign="center", valign="middle",
            color=(0.4, 0.4, 0.4, 1), font_size=dp(14),
        )
        prog_content = BoxLayout(orientation="vertical", padding=dp(30))
        prog_content.add_widget(prog_label)
        prog_popup = Popup(
            title="请稍候", content=prog_content,
            size_hint=(0.7, 0.22), auto_dismiss=False,
            background_color=hex_to_rgba("#fff8f5"),
        )
        prog_popup.open()

        # 调用1：生成规划
        hints_prompt = f"""根据一句话描述，为剧本创作生成规划。

【用户输入】
{user_input}

请返回JSON（完整，不要省略）：
- world: 世界观描述，50-150字
- app_title: 应用标题，5-15字
- app_welcome_title: 欢迎标题，5-15字
- app_welcome_text: 欢迎文字，20-50字
- scenes: 4个场景的一句话提示，每个10-20字。所有场景提示互不相同
- characters: 4-5个角色的提示（每个含name和hint），hint每个10-20字。所有角色名互不相同
- you_hint: You角色的一句话身份描述，10-20字

返回格式：
{{"world":"...","app_title":"...","app_welcome_title":"...","app_welcome_text":"...","scenes":["...","...","...","..."],"characters":[{{"name":"...","hint":"..."}},{{"name":"...","hint":"..."}},{{"name":"...","hint":"..."}},{{"name":"...","hint":"..."}}],"you_hint":"..."}}"""

        def _on_hints_done(hints, err):
            if config.app_config.get("active_profile", "") != _caller_profile:
                prog_popup.dismiss()
                return
            if not hints:
                prog_popup.dismiss()
                self._show_ai_raw_popup("AI创建剧本失败", err or "规划生成失败")
                return

            world = hints.get("world", "")
            # 清洗引号污染：AI生成的世界观文本中的双引号会破坏后续 JSON
            world = world.replace('"', '\u201c').replace('"', '\u201d')
            app_title = hints.get("app_title", user_input)
            app_welcome_title = hints.get("app_welcome_title", "")
            app_welcome_text = hints.get("app_welcome_text", "")
            scenes_hints = hints.get("scenes", [])
            chars_hints = hints.get("characters", [])
            you_hint = hints.get("you_hint", "你自己")

            # 用于汇总的容器（turn_order 在全部生成后自动推导）
            results = {
                "world": world,
                "app": {"title": app_title, "welcome_title": app_welcome_title, "welcome_text": app_welcome_text},
                "scenes": {},
                "characters": {},
                "you": None,
            }
            errors = []

            total = 1 + len(scenes_hints) + len(chars_hints) + 1  # app + scenes + chars + you
            done_count = [0]

            def _update_prog():
                done_count[0] += 1
                if config.app_config.get("active_profile", "") == _caller_profile:
                    prog_label.text = f"AI创建中…(生成场景与角色, {done_count[0]}/{total})"

            def _check_complete():
                if config.app_config.get("active_profile", "") != _caller_profile:
                    prog_popup.dismiss()
                    return
                if done_count[0] >= total:
                    prog_popup.dismiss()
                    self._write_ai_created_profile(results, errors)

            # 收集所有任务，延緩分派以避免 API 限流 (429)
            tasks = []

            # 1) 应用设置
            app_prompt = self._build_app_settings_prompt(
                f"{app_title} - {app_welcome_title}", world
            )
            def _cb_app(r, e):
                if r:
                    results["app"] = {
                        "title": r.get("title", app_title),
                        "welcome_title": r.get("welcome_title", app_welcome_title),
                        "welcome_text": r.get("welcome_text", app_welcome_text),
                    }
                else:
                    errors.append("应用设置")
                _update_prog()
                _check_complete()
            tasks.append((app_prompt, _cb_app, 800))

            # 2) 场景
            for idx, hint in enumerate(scenes_hints):
                sp = self._build_scene_ai_prompt(False, hint, world)
                def _mk_scene_cb(i):
                    def _cb(r, e):
                        if r:
                            results["scenes"][i] = r
                        else:
                            errors.append(f"场景{i+1}")
                        _update_prog()
                        _check_complete()
                    return _cb
                tasks.append((sp, _mk_scene_cb(idx), 800))

            # 3) 角色
            for ch in chars_hints:
                name = ch.get("name", "?")
                hint = ch.get("hint", name)
                cp = self._build_char_ai_prompt(False, hint, world)
                def _mk_char_cb(n):
                    def _cb(r, e):
                        if r:
                            results["characters"][n] = r
                        else:
                            errors.append(f"角色{n}")
                        _update_prog()
                        _check_complete()
                    return _cb
                tasks.append((cp, _mk_char_cb(name), 1500))

            # 4) You 角色（独立提示词 + 失败自动兜底）
            yp = self._build_you_ai_prompt(you_hint, world)
            def _cb_you(r, e):
                if r:
                    r["name"] = "You"
                    if not r.get("display_name"):
                        r["display_name"] = "你"
                    results["you"] = r
                else:
                    # 兜底：使用硬编码 You 配置，确保用户模式永远可用
                    results["you"] = {
                        "name": "You",
                        "display_name": "你",
                        "color": "#42a5f5",
                        "bg_color": "#f0f7ff",
                        "personality": "你自己",
                        "description": f"在这个世界中，你就是你。",
                        "system_prompt": "你是这个世界的参与者。用*星号*描述你的动作和表情。\n自然地和大家互动，回应他人的话题。\n回复简短自然，100-200字，要有画面感。",
                    }
                _update_prog()
                _check_complete()
            tasks.append((yp, _cb_you, 1000))

            # 延缓分派：每个任务间隔 350ms，防止 API 429 限流
            STAGGER_MS = 0.35
            for i, tup in enumerate(tasks):
                prompt, cb = tup[0], tup[1]
                mt = tup[2] if len(tup) > 2 else 800
                Clock.schedule_once(
                    lambda dt, p=prompt, c=cb, m=mt: self._do_ai_call(p, c, show_loading=False, max_tokens=m),
                    i * STAGGER_MS
                )

        self._do_ai_call(hints_prompt, _on_hints_done, show_loading=False, max_tokens=1500)

    def _write_ai_created_profile(self, results, errors):
        """将AI生成的结果写入新剧本目录"""
        app = results["app"]
        display_name = app.get("title", "新剧本")
        folder_name = self._make_safe_folder_name(display_name)
        profile_dir = config.PROFILES_DIR / folder_name
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / "characters").mkdir(exist_ok=True)
        (profile_dir / "chats").mkdir(exist_ok=True)

        # scenes.json（含去重）
        scenes_list = []
        seen_times = set()
        for key in sorted(results["scenes"].keys()):
            s = results["scenes"][key]
            time_val = s.get("time", "")
            # 场景时间去重
            if time_val in seen_times:
                time_val = f"{time_val}(2)"
            seen_times.add(time_val)
            scenes_list.append({
                "id": f"scene_{key}",
                "time": time_val,
                "location": s.get("location", ""),
                "mood": s.get("mood", ""),
                "scene": s.get("scene", ""),
            })
        save_json(profile_dir / "scenes.json", scenes_list)

        # characters（含角色名去重）—— 先保存角色，再根据实际名字推导发言顺序
        written_names = set()
        for name in sorted(results["characters"].keys()):
            c = results["characters"][name]
            # 角色名去重
            safe_name = c.get("name", name)
            if safe_name in written_names or safe_name == "You":
                base = safe_name
                suffix = 2
                while f"{base}{suffix}" in written_names:
                    suffix += 1
                safe_name = f"{base}{suffix}"
            written_names.add(safe_name)
            char_data = {
                "name": safe_name,
                "display_name": c.get("display_name", name),
                "color": c.get("color", "#888888"),
                "bg_color": c.get("bg_color", "#f5f5f5"),
                "personality": c.get("personality", ""),
                "description": c.get("description", ""),
                "system_prompt": c.get("system_prompt", ""),
            }
            save_json(profile_dir / "characters" / f"{safe_name}.json", char_data)

        # 从实际保存的角色名推导发言顺序（使用 AI 返回的真实名字，而非规划阶段名字）
        turn_order = sorted(written_names)

        # config.json
        save_json(profile_dir / "config.json", {
            "app": {
                "display_name": display_name,
                "title": app.get("title", display_name),
                "welcome_title": app.get("welcome_title", ""),
                "welcome_text": app.get("welcome_text", ""),
                "director_mode": False,
                "user_mode": False,
            },
            "world": {"setting": results.get("world", "")},
            "turn": {
                "order": turn_order,
                "history_size": 8,
            },
            "speed": {"default": 3},
        })

        # You character
        if results["you"]:
            y = results["you"]
            you_data = {
                "name": "You",
                "display_name": y.get("display_name", "你"),
                "color": y.get("color", "#42a5f5"),
                "bg_color": y.get("bg_color", "#f0f7ff"),
                "personality": y.get("personality", "你自己"),
                "description": y.get("description", ""),
                "system_prompt": y.get("system_prompt", ""),
            }
            save_json(profile_dir / "characters" / "You.json", you_data)

        # 切换到新剧本
        self.app.switch_profile(folder_name)
        self.app._show_scene_banner()
        if hasattr(self, '_profile_spinner'):
            self._profile_spinner.values = self.app.get_profile_display_names()
            self._profile_spinner.text = self.app.profile_name_to_display(folder_name)
        self._refresh_app_inputs()
        self._refresh_chat_list()
        if hasattr(self, '_scene_spinner'):
            self._refresh_scene_spinner()
        if hasattr(self, '_char_spinner'):
            self._refresh_char_spinner()

        if errors:
            # 弹窗提示部分失败
            err_content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
            err_content.add_widget(Label(
                text="剧本已创建，以下内容需手动补全：",
                font_name=config.FONT_DEFAULT, halign="left", valign="middle",
                color=(0.4, 0.4, 0.4, 1), font_size=dp(13),
                size_hint_y=None, height=dp(26),
            ))
            err_list = TextInput(
                text="  \u2022 " + "\n  \u2022 ".join(errors[:8]),
                readonly=True, multiline=True,
                foreground_color=(0.15, 0.12, 0.10, 1),
                background_color=(0.96, 0.96, 0.96, 1),
                font_size=dp(12), padding=[dp(8), dp(8)],
            )
            err_content.add_widget(err_list)
            err_popup = Popup(
                title="部分失败", content=err_content,
                size_hint=(0.85, 0.4), auto_dismiss=True,
                background_color=hex_to_rgba("#fff8f5"),
            )
            err_popup.open()
        else:
            self.app._set_status(f"剧本「{display_name}」创建完成！", "#66bb6a")
