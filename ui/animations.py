# -*- coding: utf-8 -*-
"""
Dorm Life — 动画工具集
  基于 Kivy Animation，移动端优化：短时长、轻量属性，避免掉帧。
"""

from kivy.animation import Animation
from kivy.clock import Clock

__all__ = [
    "fade_in", "fade_out",
    "slide_in_up", "slide_out_down",
    "button_press_anim", "button_release_anim",
    "breathe",
]


def fade_in(widget, duration=0.25, target_opacity=1.0):
    """淡入"""
    anim = Animation(opacity=target_opacity, duration=duration, t='out_cubic')
    anim.start(widget)
    return anim


def fade_out(widget, duration=0.20, on_complete=None):
    """淡出"""
    anim = Animation(opacity=0, duration=duration, t='in_cubic')
    if on_complete:
        anim.bind(on_complete=lambda *a: on_complete())
    anim.start(widget)
    return anim


def slide_in_up(widget, distance=None, duration=0.30, initial_opacity=0):
    """从下方向上滑入（用于输入栏等底部元素显示）"""
    from kivy.metrics import dp
    d = distance or dp(40)
    widget.opacity = initial_opacity
    # 记录原始 y
    orig_y = widget.y
    widget.y = orig_y - d

    anim_op = Animation(opacity=1, duration=duration, t='out_cubic')
    anim_y = Animation(y=orig_y, duration=duration, t='out_cubic')
    anim_op.start(widget)
    anim_y.start(widget)
    return anim_op


def slide_out_down(widget, distance=None, duration=0.25, on_complete=None):
    """向下滑出并隐藏"""
    from kivy.metrics import dp
    d = distance or dp(40)
    anim_op = Animation(opacity=0, duration=duration, t='in_cubic')
    anim_y = Animation(y=widget.y - d, duration=duration, t='in_cubic')

    if on_complete:
        anim_op.bind(on_complete=lambda *a: on_complete())

    anim_op.start(widget)
    anim_y.start(widget)
    return anim_op


def button_press_anim(btn, scale_to=0.96, duration=0.08):
    """按钮按下时缩小"""
    # 保存原始尺寸
    if not hasattr(btn, '_orig_size'):
        btn._orig_size = btn.size
    if not hasattr(btn, '_orig_font_size'):
        btn._orig_font_size = btn.font_size

    from kivy.metrics import dp
    ow, oh = btn._orig_size
    anim = Animation(
        size=(ow * scale_to, oh * scale_to),
        duration=duration,
        t='out_quad',
    )
    anim.start(btn)
    return anim


def button_release_anim(btn, scale_from=0.96, duration=0.12):
    """按钮释放时弹回"""
    if not hasattr(btn, '_orig_size'):
        return
    ow, oh = btn._orig_size
    anim = Animation(size=(ow, oh), duration=duration, t='out_back')
    anim.start(btn)
    return anim


def breathe(widget, min_opacity=0.35, max_opacity=1.0, period=1.2):
    """呼吸循环动画（用于状态指示灯），返回取消回调"""
    running = [True]

    def _tick(dt):
        if not running[0]:
            return
        # 先淡到最亮
        anim_up = Animation(opacity=max_opacity, duration=period * 0.5, t='in_out_sine')
        anim_down = Animation(opacity=min_opacity, duration=period * 0.5, t='in_out_sine')
        anim_up.bind(on_complete=lambda *a: anim_down.start(widget))
        anim_down.bind(on_complete=lambda *a: Clock.schedule_once(
            lambda dt: _tick(dt), 0) if running[0] else None)
        anim_up.start(widget)

    _tick(0)

    def cancel():
        running[0] = False
        widget.opacity = max_opacity

    return cancel
