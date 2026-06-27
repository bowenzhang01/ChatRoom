# -*- coding: utf-8 -*-
"""SettingsPopup — API 配置 Tab"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hex_color
from threading import Thread

import config
from utils import hex_to_rgba, make_popup_label
from ui.base_widgets import FitSpinner, FitSpinnerOption, ScrollDropdown, RoundedButton
from ui.theme import theme
from api_service import fetch_models, APIError


class APITabMixin:
    """API 配置 Tab — Key/Base/Model 管理 + 连接测试"""

    def _build_api_tab(self):
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(8))

        box.add_widget(Label(
            text="API Key:", size_hint_y=None, height=dp(22),
            halign="left", color=(0.75, 0.70, 0.65, 1), font_size=dp(12),
        ))
        self._api_key_input = TextInput(
            text="", multiline=False, password=True, size_hint_y=None, height=dp(40),
            foreground_color=(0.15,0.12,0.10,1), background_color=(0.96,0.96,0.96,1),
            font_size=dp(12), padding=[dp(10), dp(10), dp(10), dp(10)],
        )
        box.add_widget(self._api_key_input)

        box.add_widget(Label(
            text="API Base:", size_hint_y=None, height=dp(22),
            halign="left", color=(0.75, 0.70, 0.65, 1), font_size=dp(12),
        ))
        self._api_base_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(40),
            foreground_color=(0.15,0.12,0.10,1), background_color=(0.96,0.96,0.96,1),
            font_size=dp(12), padding=[dp(10), dp(10), dp(10), dp(10)],
        )
        box.add_widget(self._api_base_input)

        box.add_widget(Label(
            text="Model:", size_hint_y=None, height=dp(22),
            halign="left", color=(0.75, 0.70, 0.65, 1), font_size=dp(12),
        ))
        #  v0.5.3: 模型下拉列表，支持从 /models 接口自动获取
        init_values = list(config.MODELS_LIST) if config.MODELS_LIST else [config.MODEL]
        if "自定义…" not in init_values:
            init_values.append("自定义…")
        self._api_model_spinner = FitSpinner(
            text=config.MODEL,
            values=init_values,
            size_hint_y=None, height=dp(40),
            background_normal="",
            background_color=(0.96, 0.96, 0.96, 1),
            color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12),
            sync_height=True,
            option_cls=FitSpinnerOption,
            dropdown_cls=ScrollDropdown,
        )
        self._api_model_spinner.bind(text=self._on_model_selected)
        box.add_widget(self._api_model_spinner)

        # Save + Test buttons row
        btns_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        save_btn = RoundedButton(
            btn_color=theme.accent,
            text="保存 API 配置", size_hint_y=1, size_hint_x=1,
            color=(1, 1, 1, 1), font_size=dp(12), bold=True,
        )
        save_btn.bind(on_release=self._save_api_settings)
        btns_row.add_widget(save_btn)

        self._test_api_btn = RoundedButton(
            btn_color=theme.info,
            text="测试连接", size_hint_y=1, size_hint_x=1,
            color=(1, 1, 1, 1), font_size=dp(12), bold=True,
        )
        self._test_api_btn.bind(on_release=self._test_api)
        btns_row.add_widget(self._test_api_btn)
        box.add_widget(btns_row)

        # 弹性空间
        box.add_widget(Widget(size_hint_y=1))

        self.content_area.add_widget(box)

        #  v0.5.3: 修复切换标签时输入框文字不渲染 — 等布局完成后再刷新
        Clock.schedule_once(lambda dt: self._refresh_api_inputs(), 0.1)

    def _refresh_api_inputs(self):
        """v0.5.3: 等布局完成后注入文本并重置水平滚动，彻底修复初始渲染错位"""
        self._api_key_input.text = config.API_KEY
        self._api_base_input.text = config.API_BASE
        self._api_key_input.scroll_x = 0
        self._api_base_input.scroll_x = 0

    def _test_api(self, *args):
        """v0.5.3: 一键测试 API，成功时自动获取模型列表并更新下拉框"""
        btn = self._test_api_btn
        key = self._api_key_input.text.strip()
        base = self._api_base_input.text.strip() or "https://api.deepseek.com"

        if not key:
            self._show_test_result("请先填写 API Key", theme.danger)
            return

        btn.text = "测试中…"
        btn.disabled = True
        btn.set_bg_color(theme.GRAY_400)

        # v0.6.5: 记录调用时的 profile，防止线程回调污染切换后的界面
        _caller_profile = config.app_config.get("active_profile", "")

        def do_test():
            if config.app_config.get("active_profile", "") != _caller_profile:
                return
            try:
                models = fetch_models(api_key=key, api_base=base)
                if config.app_config.get("active_profile", "") != _caller_profile:
                    return
                current = self._api_model_spinner.text.strip() or config.MODEL
                models = sorted(set(models))
                if "自定义…" not in models:
                    models.append("自定义…")
                found = any(current in m for m in models if m != "自定义…")
                Clock.schedule_once(
                    lambda dt: self._update_model_spinner(models, current if found else (models[0] if models else current)), 0
                )
                config.app_config["model"]["models"] = [m for m in models if m != "自定义…"]
                self.app._save_config()
                Clock.schedule_once(
                    lambda dt: self._show_test_result(
                        f"连接成功！" + (f"\n模型「{current}」可用" if found else f"\n已获取 {len([m for m in models if m != '自定义…'])} 个可用模型"),
                        theme.accent
                    ), 0
                )
            except APIError as e:
                if e.status_code == 401:
                    Clock.schedule_once(lambda dt: self._show_test_result("API Key 无效", theme.danger), 0)
                else:
                    Clock.schedule_once(lambda dt: self._show_test_result(str(e), theme.warning), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._show_test_result(f"连接失败: {str(e)[:60]}", theme.danger), 0)
            finally:
                Clock.schedule_once(lambda dt: self._reset_test_btn(), 0)

        Thread(target=do_test, daemon=True).start()

    def _show_test_result(self, msg, color):
        """v0.5.2: 显示测试结果弹窗"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        lbl = make_popup_label(
            msg,
            halign="center", valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
        )
        content.add_widget(lbl)
        btn = RoundedButton(
            btn_color=color,
            text="确定", size_hint_y=None, height=dp(40),
            color=(1, 1, 1, 1), font_size=dp(13),
        )
        content.add_widget(btn)
        popup = Popup(
            title="API 测试",
            content=content,
            size_hint=(0.8, 0.35),
            background_color=hex_to_rgba(theme.window_bg),
            auto_dismiss=True,
        )
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def _reset_test_btn(self):
        """v0.5.2: 恢复测试按钮状态"""
        self._test_api_btn.text = "测试连接"
        self._test_api_btn.disabled = False
        self._test_api_btn.set_bg_color(theme.info)

    def _update_model_spinner(self, models, select_model):
        """v0.5.3: 更新模型下拉列表并选中指定项"""
        self._api_model_spinner.values = models
        self._api_model_spinner.text = select_model

    def _on_model_selected(self, spinner, text):
        """v0.5.3: 模型下拉选择回调 — 选中「自定义…」时弹出输入框"""
        if text == "自定义…":
            self._show_custom_model_dialog()

    def _show_custom_model_dialog(self):
        """v0.5.3: 弹出对话框让用户输入自定义模型名"""
        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(Label(
            text="输入自定义模型名：",
            font_name=config.FONT_DEFAULT,
            halign="left", valign="middle",
            color=(0.75, 0.70, 0.65, 1),
            font_size=dp(13),
            size_hint_y=None, height=dp(26),
        ))
        model_input = TextInput(
            text="", multiline=False, size_hint_y=None, height=dp(42),
            foreground_color=(0.15,0.12,0.10,1), background_color=(0.96,0.96,0.96,1),
            font_size=dp(13), padding=[dp(10), dp(12), dp(10), dp(10)],
        )
        content.add_widget(model_input)

        btns_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cancel_btn = RoundedButton(
            btn_color=theme.GRAY_400,
            text="取消", size_hint_y=1, size_hint_x=1,
            color=(1,1,1,1), font_size=dp(13),
        )
        confirm_btn = RoundedButton(
            btn_color=theme.info,
            text="确定", size_hint_y=1, size_hint_x=1,
            color=(1,1,1,1), font_size=dp(13),
        )
        btns_row.add_widget(cancel_btn)
        btns_row.add_widget(confirm_btn)
        content.add_widget(btns_row)

        content.add_widget(Widget(size_hint_y=1))

        popup = Popup(
            title="自定义模型",
            content=content,
            size_hint=(0.8, 0.35),
            background_color=hex_to_rgba(theme.window_bg),
            auto_dismiss=False,
        )

        def on_confirm(instance):
            custom = model_input.text.strip()
            if custom:
                # 插入到「自定义…」之前
                vals = list(self._api_model_spinner.values)
                if custom not in vals:
                    # 找到「自定义…」的位置
                    try:
                        idx = vals.index("自定义…")
                        vals.insert(idx, custom)
                    except ValueError:
                        vals.append(custom)
                        vals.append("自定义…")
                    self._api_model_spinner.values = vals
                self._api_model_spinner.text = custom
            else:
                # 没输入就恢复到上一个有效值
                self._api_model_spinner.text = config.MODEL
            popup.dismiss()

        def on_cancel(instance):
            self._api_model_spinner.text = config.MODEL
            popup.dismiss()

        confirm_btn.bind(on_release=on_confirm)
        cancel_btn.bind(on_release=on_cancel)
        popup.open()

    def _save_api_settings(self, *args):
        key = self._api_key_input.text.strip()
        if not key:
            return
        sel_model = self._api_model_spinner.text.strip()
        # 过滤掉「自定义…」占位项
        if sel_model == "自定义…":
            sel_model = config.MODEL
        config.app_config["model"]["api_key"] = key
        config.app_config["model"]["api_base"] = self._api_base_input.text.strip() or config.API_BASE
        config.app_config["model"]["model"] = sel_model
        config.API_KEY = key
        config.API_BASE = config.app_config["model"]["api_base"]
        config.MODEL = sel_model
        config.MODELS_LIST = config.app_config["model"].get("models", [])
        self.app._save_config()
        self.app._set_status("API 已保存", theme.accent)
