# -*- coding: utf-8 -*-
"""SettingsPopup — 发言顺序 Tab (拖拽排序)"""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

import config
from utils import hex_to_rgba, save_json
from ui.base_widgets import RoundedButton
from ui.theme import theme
from ui.widgets._drag_list import ReorderableList, ReorderableListScroll


class SpeakTabMixin:

    def _build_speak_tab(self):
        box = BoxLayout(orientation="vertical", spacing=dp(6))
        self.content_area.add_widget(box)

        box.add_widget(Label(
            text="发言顺序 (长按 \u2261 拖拽排序)",
            size_hint_y=None, height=dp(22),
            halign="left", color=(0.75, 0.70, 0.65, 1), bold=True, font_size=dp(11),
        ))

        self._order_list = ReorderableList(
            items=[],
            on_order_changed=self._on_order_list_changed,
            on_remove=self._on_order_item_remove,
            get_remove_disabled=self._is_remove_disabled,
            size_hint_y=None,
        )

        order_scroll = ReorderableListScroll()
        order_scroll.add_widget(self._order_list)
        self._order_list._scroll_wrapper = order_scroll
        box.add_widget(order_scroll)

        box.add_widget(Widget(size_hint_y=None, height=dp(8)))

        box.add_widget(Label(
            text="可选角色 (点击 [+] 加入发言顺序)",
            size_hint_y=None, height=dp(22),
            halign="left", color=(0.55, 0.48, 0.42, 1), font_size=dp(11),
        ))

        self._optional_box = BoxLayout(
            orientation="vertical",
            spacing=dp(3),
            size_hint_y=None,
            padding=(0, 0),
        )
        self._optional_box.bind(minimum_height=self._optional_box.setter("height"))

        opt_scroll = ScrollView(
            size_hint_y=None,
            height=dp(160),
            do_scroll_x=False,
        )
        opt_scroll.add_widget(self._optional_box)
        box.add_widget(opt_scroll)

        buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        box.add_widget(Widget(size_hint_y=1))
        box.add_widget(buttons)

        reset_btn = RoundedButton(
            btn_color=theme.GRAY_600,
            text="取消修改",
            size_hint_x=0.5,
            color=(1, 1, 1, 1), font_size=dp(11), bold=True,
        )
        reset_btn.bind(on_release=self._reset_order)
        buttons.add_widget(reset_btn)

        save_btn = RoundedButton(
            btn_color=theme.accent,
            text="保存顺序",
            size_hint_x=0.5,
            color=(1, 1, 1, 1), font_size=dp(11), bold=True,
        )
        save_btn.bind(on_release=self._save_speak_order)
        buttons.add_widget(save_btn)

        Clock.schedule_once(lambda dt: self._refresh_speak_tab(), 0.1)

    def _refresh_speak_tab(self):
        if not hasattr(self, '_order_list'):
            return

        app = self.app
        order = list(app.turn_order)

        if not app.user_mode:
            order = [n for n in order if n != "You"]
        elif "You" in app.characters and "You" not in order:
            order.append("You")

        order_items = []
        for name in order:
            st = app.char_styles.get(name, {})
            if name == "You":
                c = app.characters.get(name, {})
                dname = c.get("display_name", "\u4f60")
                color = "#42a5f5"
            else:
                dname = st.get("name", name)
                color = st.get("color", "#888")
            order_items.append({
                "name": name,
                "display_name": dname,
                "color": color,
            })

        self._order_list.set_items(order_items)

        optional_names = []
        all_char_names = set(app.characters.keys())
        order_names = set(order)
        for name in sorted(all_char_names):
            if name == "You":
                continue
            if name not in order_names:
                optional_names.append(name)

        self._optional_box.clear_widgets()
        for name in optional_names:
            st = app.char_styles.get(name, {})
            dname = st.get("name", name)
            color = st.get("color", "#888")

            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(40),
                spacing=dp(4), padding=(dp(8), dp(2)),
            )
            with row.canvas.before:
                from kivy.graphics import Color as KColor, RoundedRectangle
                row._bg_c = KColor(*hex_to_rgba("#ffffff"))
                row._bg_r = RoundedRectangle(radius=[dp(6)] * 4)
            row.bind(
                pos=lambda w, p: setattr(w._bg_r, "pos", p),
                size=lambda w, s: setattr(w._bg_r, "size", s),
            )

            btn = RoundedButton(
                btn_color=theme.info,
                text="+",
                size_hint_x=None,
                width=dp(36),
                color=(1, 1, 1, 1),
                font_size=dp(16),
                bold=True,
                radius=dp(4),
            )
            btn._add_name = name
            btn.bind(on_release=self._add_optional_to_order)
            row.add_widget(btn)

            dot = Label(
                text="\u25cf",
                font_name=config.FONT_DEFAULT,
                size_hint_x=None,
                width=dp(20),
                color=hex_to_rgba(color),
                font_size=dp(11),
                halign="center",
                valign="middle",
            )
            row.add_widget(dot)

            name_label = Label(
                text=dname,
                font_name=config.FONT_DEFAULT,
                size_hint_x=1,
                color=(0.15, 0.12, 0.10, 1),
                font_size=dp(12),
                halign="left", valign="middle",
                shorten=True,
            )
            name_label.bind(size=lambda lbl, s: setattr(lbl, "text_size", (s[0] - dp(4), None)))
            row.add_widget(name_label)

            self._optional_box.add_widget(row)

    def _add_optional_to_order(self, btn):
        name = btn._add_name
        if name not in self.app.characters:
            return
        if name not in self.app.turn_order:
            self.app.turn_order.append(name)
        self._refresh_speak_tab()

    def _on_order_list_changed(self, new_items):
        new_names = [item["name"] for item in new_items]
        self.app.turn_order = new_names

    def _on_order_item_remove(self, item_data):
        name = item_data["name"]
        if name == "You":
            return
        if name in self.app.turn_order:
            self.app.turn_order.remove(name)
        self._refresh_speak_tab()

    def _is_remove_disabled(self, item_data):
        name = item_data["name"]
        if name == "You" and self.app.user_mode:
            return True
        return False

    def _reset_order(self, *args):
        self._refresh_speak_tab()

    def _save_speak_order(self, *args):
        app = self.app
        order_to_save = list(app.turn_order)
        if app.user_mode and "You" in app.characters and "You" not in order_to_save:
            order_to_save.append("You")
        app.turn_order = order_to_save
        pc = app._profile_config
        pc.setdefault("turn", {})["order"] = order_to_save
        save_json(app.profile_dir / "config.json", pc)
        app._set_status("发言顺序已保存", "#66bb6a")
