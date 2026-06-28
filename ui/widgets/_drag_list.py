# -*- coding: utf-8 -*-
"""Drag-drop reorderable list widget for speaking order management."""

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle

import config
from utils import hex_to_rgba
from ui.theme import theme
from ui.base_widgets import RoundedButton


class DragListItem(BoxLayout):

    def __init__(self, item_data, on_remove, remove_disabled=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(42)
        self.spacing = dp(4)
        self.padding = (dp(8), dp(4))

        self._item_data = item_data
        self._on_remove = on_remove

        with self.canvas.before:
            self._bg_color = Color(*hex_to_rgba("#ffffff"))
            self._bg_rect = RoundedRectangle(radius=[dp(6)] * 4)
            self._shadow_c = Color(0, 0, 0, 0)
            self._shadow_r = RoundedRectangle(radius=[dp(6)] * 4)

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        name = item_data.get("display_name", item_data.get("name", "?"))
        color_hex = item_data.get("color", "#888")

        drag_lbl = Label(
            text="\u2261",
            font_name=config.FONT_DEFAULT,
            size_hint_x=None,
            width=dp(26),
            color=(0.7, 0.7, 0.7, 1),
            font_size=dp(18),
            halign="center",
            valign="middle",
            bold=True,
        )
        drag_lbl.bind(size=lambda lbl, s: setattr(lbl, "text_size", s))
        self.add_widget(drag_lbl)

        dot = Label(
            text="\u25cf",
            font_name=config.FONT_DEFAULT,
            size_hint_x=None,
            width=dp(20),
            color=hex_to_rgba(color_hex),
            font_size=dp(11),
            halign="center",
            valign="middle",
        )
        self.add_widget(dot)

        name_label = Label(
            text=name,
            font_name=config.FONT_DEFAULT,
            size_hint_x=1,
            color=(0.15, 0.12, 0.10, 1),
            font_size=dp(12),
            halign="left",
            valign="middle",
            shorten=True,
        )
        name_label.bind(size=lambda lbl, s: setattr(lbl, "text_size", (s[0] - dp(4), None)))
        self.add_widget(name_label)

        self._rm_btn = RoundedButton(
            btn_color="#ef5350",
            text="\u79fb\u9664",
            size_hint_x=None,
            width=dp(52),
            color=(1, 1, 1, 1),
            font_size=dp(9),
            bold=True,
            radius=dp(4),
        )
        self._rm_btn.bind(on_release=self._on_remove_press)
        self.add_widget(self._rm_btn)

        if remove_disabled:
            self.set_remove_disabled(True)

        self._drag_handle = drag_lbl

    def _update_canvas(self, *args):
        x, y = self.pos
        w, h = self.size
        self._bg_rect.pos = (x, y)
        self._bg_rect.size = (w, h)
        offset = dp(2.5)
        self._shadow_r.pos = (x - offset, y - offset)
        self._shadow_r.size = (w + dp(4), h + dp(4))

    def _on_remove_press(self, *args):
        if not self._rm_btn.disabled and self._on_remove:
            self._on_remove(self._item_data)

    def set_remove_disabled(self, disabled):
        self._rm_btn.disabled = disabled
        if disabled:
            self._rm_btn.set_bg_color(theme.GRAY_300)
            self._rm_btn.color = (0.6, 0.6, 0.6, 1)
        else:
            self._rm_btn.set_bg_color("#ef5350")
            self._rm_btn.color = (1, 1, 1, 1)

    def set_dragging(self, active):
        if active:
            self.opacity = 0.75
            self._bg_color.rgba = hex_to_rgba("#fffaf5")
            self._shadow_c.rgba = (0, 0, 0, 0.18)
            self._drag_handle.color = (0.30, 0.55, 0.25, 1)
        else:
            self.opacity = 1.0
            self._bg_color.rgba = hex_to_rgba("#ffffff")
            self._shadow_c.rgba = (0, 0, 0, 0)
            self._drag_handle.color = (0.7, 0.7, 0.7, 1)


class ReorderableListScroll(ScrollView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_scroll_x = False
        self.do_scroll_y = True
        self.size_hint_y = None
        self.height = dp(200)
        self._drag_active = False
        self._scroll_dir = 0
        self._autoscroll_ev = None

    def on_touch_down(self, touch):
        if self._drag_active:
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._drag_active:
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._drag_active:
            return True
        return super().on_touch_up(touch)

    def _do_autoscroll(self, dt):
        if self._scroll_dir == 0 or not self.children:
            return
        cw = self.children[0]
        scrollable = max(0, cw.height - self.height)
        if scrollable <= 0:
            return
        step = dp(10) / scrollable
        self.scroll_y = max(0, min(1, self.scroll_y + self._scroll_dir * step))

    def start_autoscroll(self, direction):
        if self._scroll_dir == direction:
            return
        self._scroll_dir = direction
        if self._autoscroll_ev is None:
            self._autoscroll_ev = Clock.schedule_interval(self._do_autoscroll, 1.0 / 30.0)

    def stop_autoscroll(self):
        self._scroll_dir = 0
        if self._autoscroll_ev:
            self._autoscroll_ev.cancel()
            self._autoscroll_ev = None


class ReorderableList(BoxLayout):

    def __init__(self, items=None, on_order_changed=None, on_remove=None,
                 get_remove_disabled=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(5)
        self.size_hint_y = None

        self._items = items or []
        self._item_widgets = []
        self._on_order_changed = on_order_changed
        self._on_remove = on_remove
        self._get_remove_disabled = get_remove_disabled or (lambda _: False)

        self._drag_idx = -1
        self._drag_touch_uid = None
        self._drag_widget = None
        self._drag_active = False
        self._last_target = -1
        self._long_press_event = None
        self._scroll_wrapper = None

        with self.canvas.after:
            self._ind_c = Color(0, 0, 0, 0)
            self._ind_r = RoundedRectangle(
                radius=[dp(3)] * 4, size=(0, dp(4))
            )

        self._rebuild()

    def _rebuild(self):
        self.clear_widgets()
        self._item_widgets.clear()
        for item in self._items:
            disabled = self._get_remove_disabled(item)
            w = DragListItem(
                item_data=item,
                on_remove=self._handle_remove,
                remove_disabled=disabled,
            )
            self._item_widgets.append(w)
            self.add_widget(w)
        self._update_height()

    def _handle_remove(self, item_data):
        if self._on_remove:
            self._on_remove(item_data)

    def set_items(self, items):
        self._items = items or []
        self._rebuild()

    def _update_height(self):
        total = sum(w.height + self.spacing for w in self._item_widgets) + dp(2)
        self.height = max(dp(40), total)

    def _get_item_at_y(self, local_y):
        for i, w in enumerate(self._item_widgets):
            if w.y - self.spacing / 2.0 <= local_y <= w.y + w.height + self.spacing / 2.0:
                return i
        return -1

    def _is_on_drag_handle(self, item_idx, local_x, local_y):
        w = self._item_widgets[item_idx]
        if not (w.y <= local_y <= w.y + w.height):
            return False
        hx = w.x + w._drag_handle.x
        hw = w._drag_handle.width
        return hx <= local_x <= hx + hw

    def _touch_to_local(self, touch):
        return touch.pos[0] - self.x, touch.pos[1] - self.y

    def _show_indicator_at(self, local_y, item_idx):
        if item_idx < 0 or not self._item_widgets:
            self._ind_c.rgba = (0, 0, 0, 0)
            return

        w = self._item_widgets[item_idx]
        slot_y = w.y - self.spacing / 2.0 - dp(2)
        margin = dp(16)
        line_w = max(0, self.width - margin * 2)
        self._ind_c.rgba = hex_to_rgba(theme.accent)
        self._ind_r.pos = (margin, slot_y)
        self._ind_r.size = (line_w, dp(4))

    def _hide_indicator(self):
        self._ind_c.rgba = (0, 0, 0, 0)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        local_x, local_y = self._touch_to_local(touch)

        item_idx = self._get_item_at_y(local_y)
        if item_idx < 0:
            return super().on_touch_down(touch)

        if not self._is_on_drag_handle(item_idx, local_x, local_y):
            return super().on_touch_down(touch)

        if touch.is_double_tap:
            return super().on_touch_down(touch)

        self._drag_idx = item_idx
        self._drag_touch_uid = touch.uid
        self._last_target = item_idx
        self._long_press_event = Clock.schedule_once(
            lambda dt: self._start_drag(), 0.30
        )
        touch.grab(self)
        self._set_scroll_allowed(False)
        return True

    def _start_drag(self):
        if self._drag_idx < 0 or self._drag_active:
            return
        self._drag_active = True
        self._drag_widget = self._item_widgets[self._drag_idx]
        self._drag_widget.set_dragging(True)

    def on_touch_move(self, touch):
        if touch.uid != self._drag_touch_uid:
            return super().on_touch_move(touch)

        local_x, local_y = self._touch_to_local(touch)

        if self._long_press_event is not None and not self._drag_active:
            if abs(touch.opos[1] - touch.pos[1]) > dp(5):
                self._long_press_event.cancel()
                self._long_press_event = None
                self._start_drag()

        if not self._drag_active:
            return True

        if self._check_edge_scroll(touch):
            return True

        target = self._get_item_at_y(local_y)
        if target >= 0 and target != self._last_target:
            self._swap_items(self._last_target, target)
            self._drag_idx = target
            self._last_target = target

        if target >= 0:
            self._show_indicator_at(local_y, target)
        else:
            self._hide_indicator()
        return True

    def _check_edge_scroll(self, touch):
        ws = self._scroll_wrapper
        if ws is None:
            return False

        edge = dp(20)
        can_up = ws.scroll_y < 0.999
        can_dn = ws.scroll_y > 0.001
        if not can_up and not can_dn:
            return False

        # touch position in the content's (ReorderableList's) local space
        local_x, local_y = self._touch_to_local(touch)

        viewport_h = ws.height
        content_h = self.height
        scrollable = max(0, content_h - viewport_h)

        # The visible area of the scrollview, expressed in content's local coords.
        # content.y = -scroll_y * scrollable
        # visible_bottom_in_content = -content.y = scroll_y * scrollable
        # visible_top_in_content   = visible_bottom_in_content + viewport_h
        visible_bottom = ws.scroll_y * scrollable
        visible_top = visible_bottom + viewport_h

        if can_up and local_y > visible_top - edge:
            ws.start_autoscroll(1)
            return True
        if can_dn and local_y < visible_bottom + edge:
            ws.start_autoscroll(-1)
            return True

        ws.stop_autoscroll()
        return False

    def _swap_items(self, idx_a, idx_b):
        if idx_a == idx_b:
            return

        self._items[idx_a], self._items[idx_b] = self._items[idx_b], self._items[idx_a]
        self._item_widgets[idx_a], self._item_widgets[idx_b] = \
            self._item_widgets[idx_b], self._item_widgets[idx_a]

        self.clear_widgets()
        for w in self._item_widgets:
            self.add_widget(w)
        self._update_height()

    def on_touch_up(self, touch):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None

        if touch.uid == self._drag_touch_uid:
            changed = self._drag_active

            self._stop_autoscroll()
            if self._drag_widget:
                self._drag_widget.set_dragging(False)

            if self._on_order_changed and changed:
                self._on_order_changed(list(self._items))

            self._drag_idx = -1
            self._drag_touch_uid = None
            self._drag_widget = None
            self._drag_active = False
            self._last_target = -1
            self._hide_indicator()
            if touch.grab_current is self:
                touch.ungrab(self)
            self._set_scroll_allowed(True)
            return True

        return super().on_touch_up(touch)

    def _set_scroll_allowed(self, allowed):
        if self._scroll_wrapper:
            self._scroll_wrapper._drag_active = not allowed

    def _stop_autoscroll(self):
        if self._scroll_wrapper:
            self._scroll_wrapper.stop_autoscroll()
