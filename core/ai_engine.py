# -*- coding: utf-8 -*-
"""
Dorm Life - AI 引擎 (extracted from main.py 2026-06-27)
  AIEngine: prompt 构建 / LLM 调用 / 动态发言人选策略
"""

import random

from api_service import call_chat_completion, APIError


class AIEngine:
    """AI 对话引擎 — 注入到 DormApp 中"""

    def __init__(self, app):
        self.app = app

    def _get_scene_text(self) -> str:
        s = self.app.scenes[self.app.scene_idx % len(self.app.scenes)] if self.app.scenes else {"time": "", "scene": "", "location": ""}
        loc = f"地点：{s.get('location', '')}。" if s.get('location', '') else ""
        return f"{s.get('time', '')}。{loc}{s.get('scene', '')}"

    def _build_prompt(self, name: str) -> str:
        char = self.app.characters.get(name, {})
        scene = self._get_scene_text()
        recent = self.app.history[-8:] if self.app.history else []
        lines = []
        for m in recent:
            # v0.5.1: 导演消息特殊处理
            if m.get("type") == "director":
                lines.append(f" [Director's note - incorporate this into the scene]: {m['text']}")
            else:
                dname = m.get("display_name", m["name"])
                lines.append(f"{dname}: {m['text']}")
        dialogue = "\n\n".join(lines) if lines else "(Just arrived)"

        # v0.5.1: 用户模式注入提示
        user_note = ""
        if self.app.user_mode and "You" in self.app.characters:
            uc = self.app.characters["You"]
            dname = uc.get('display_name', '你')
            desc = uc.get('description', '一个普通人')
            pers = uc.get('personality', '')
            pers_line = f"{dname}性格{pers}。" if pers else ""
            user_note = (
                f"\n\n【关于{dname}】\n"
                f"{dname}也在场——{desc}。{pers_line}\n"
                f"{dname}不是旁观者，是和大家一起生活的人。自然地与{dname}说话、互动，\n"
                f"像对待其他角色一样。不要无视{dname}的存在。"
            )

        return (
            f"{scene}{user_note}\n\n[Recent]\n{dialogue}\n\n"
            f"[Your turn - {char.get('display_name', name)}]\n"
            f"Respond naturally. Describe what you do."
            + self._build_next_hint(name)
        )

    def _build_next_hint(self, current_speaker: str) -> str:
        """v0.8.6: Append [NEXT] instruction only in dynamic mode."""
        if self.app.mode != "dynamic":
            return ""
        others = [n for n in self.app._get_effective_order() if n != current_speaker]
        if not others:
            return ""
        other_names = ", ".join(others)
        return (
            f"\n\nOn the very last line of your reply ONLY, add [NEXT:Name] "
            f"to suggest who should speak next. Pick from: {other_names}. "
            f"Do NOT include [NEXT] inside your dialogue or actions."
        )

    def _call_llm(self, name: str) -> str:
        char = self.app.characters.get(name)
        if not char:
            return "..."
        prompt = self._build_prompt(name)
        try:
            content = call_chat_completion(
                messages=[
                    {"role": "system", "content": char["system_prompt"]},
                    {"role": "user", "content": prompt},
                ],
            )
            self.app._api_error_count = 0
            return content
        except APIError as e:
            self.app._api_error_count += 1
            err_msg = str(e)
            self.app._set_status(f"API 错误: {err_msg}", "#ef5350")
            if self.app._api_error_count >= 3:
                self.app._queue.put(("api_error_stop", err_msg))
                self.app._api_error_count = 0
                return f"*{name} 遇到了问题*"
            return f"*{name} thought for a moment*"

    def _pick_next_speaker_rules(self):
        """Rule-based weighted random selection. Zero API cost.
        Factors: silence penalty, direct mention, anti-self-repeat, [NEXT] hint."""
        effective_order = self.app._get_effective_order()
        if not effective_order or len(effective_order) <= 1:
            return None

        # Hard fallback: force-insert any character silent for >= 15 turns
        HARD_SILENCE = 15
        USER_HARD_SILENCE = 12  # 用户沉默上限略短，更快被拉入
        for name in effective_order:
            last = self.app._char_last_turn.get(name, -1)
            silence = self.app.turn_count if last < 0 else self.app.turn_count - last
            limit = USER_HARD_SILENCE if name == "You" else HARD_SILENCE
            if silence >= limit:
                print(f"[director] hard silence: {name} ({silence} turns)")
                return name

        # Gather context from last message
        last_speaker = None
        last_text = ""
        if self.app.history:
            last_msg = self.app.history[-1]
            last_speaker = last_msg.get("name", "")
            last_text = last_msg.get("text", "")

        # Debug: show hint status
        if self.app._suggested_next:
            print(f"[director] hint from prev char: {self.app._suggested_next}")

        # Compute weights
        weights = {}
        total = 0.0
        for name in effective_order:
            w = 1.0
            factors = []

            # A: silence penalty (+0.25 per turn, capped at 10 turns for weighting)
            #    user gets 0.6x attenuation to avoid dominating the conversation
            last = self.app._char_last_turn.get(name, -1)
            silence = self.app.turn_count if last < 0 else self.app.turn_count - last
            sil_bonus = min(silence, 10) * 0.25
            if name == "You":
                sil_bonus *= 0.6
            w += sil_bonus
            if sil_bonus > 0:
                factors.append(f"silence+{sil_bonus:.1f}")

            # B: direct mention in last message (x3.0)
            if last_text and name in last_text:
                w *= 3.0
                factors.append("mentioned")

            # C: anti-self-repeat (x0.1 for the character who just spoke)
            if name == last_speaker:
                w *= 0.1
                factors.append("self")

            # D: [NEXT] hint from previous character (x5.0)
            if name == self.app._suggested_next:
                w *= 5.0
                factors.append("hint")

            weights[name] = (w, factors)
            total += w

        if total <= 0:
            picked = random.choice(effective_order)
            print(f"[director] zero weights -> random: {picked}")
            return picked

        # Weighted random selection
        r = random.random() * total
        cumulative = 0.0
        for name in effective_order:
            w, factors = weights[name]
            pct = w / total * 100
            factor_str = ", ".join(factors) if factors else "base"
            print(f"[director]   {name}: w={w:.2f} ({pct:.0f}%) [{factor_str}]")
            cumulative += w
            if r <= cumulative:
                picked = name
                break
        else:
            picked = effective_order[-1]

        print(f"[director] picked: {picked}")
        return picked
