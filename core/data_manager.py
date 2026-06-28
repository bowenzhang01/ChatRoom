# -*- coding: utf-8 -*-
"""
Dorm Life - 数据管理器 (extracted from main.py 2026-06-27)
  DataManager: profile/角色/场景的加载、保存、迁移
"""

import json
import os
from pathlib import Path

import config
from utils import load_json, save_json


class DataManager:
    """数据管理器 — 注入到 DormApp 中"""

    def __init__(self, app):
        self.app = app

    # ── 迁移 ──

    def _migrate_if_needed(self):
        """v0.6.5: 首次启动时自动将旧数据迁移到 profiles/ 下"""
        if not config.PROFILES_DIR.exists() or not any(
            p.is_dir() for p in config.PROFILES_DIR.iterdir()
        ):
            default_name = "dorm_girls"
            default_profile = config.PROFILES_DIR / default_name
            default_profile.mkdir(parents=True, exist_ok=True)
            (default_profile / "characters").mkdir(exist_ok=True)

            # 迁移旧 scenes.json
            old_scenes = config.BASE_DIR / "scenes.json"
            if old_scenes.exists():
                import shutil
                shutil.copy(str(old_scenes), str(default_profile / "scenes.json"))

            # 迁移旧 characters/
            old_chars = config.BASE_DIR / "characters"
            if old_chars.exists():
                import shutil
                for f in old_chars.glob("*.json"):
                    shutil.copy(str(f), str(default_profile / "characters" / f.name))

            # 生成 profile config.json
            old_ac = config.app_config.get("app", {})
            old_turn = config.app_config.get("turn", {})
            profile_config_data = {
                "app": {
                    "title": old_ac.get("title", "ChatRoom"),
                    "welcome_title": old_ac.get("welcome_title", "欢迎来到女生寝室"),
                    "welcome_text": old_ac.get("welcome_text", "四个女孩的日常即将开始～"),
                    "director_mode": old_ac.get("director_mode", False),
                    "user_mode": old_ac.get("user_mode", False),
                },
                "turn": {
                    "order": old_turn.get("order", ["Jane", "Jill", "Kate", "Lily"]),
                    "history_size": old_turn.get("history_size", 8),
                },
                "speed": {"default": config.app_config.get("speed", {}).get("default", 3)},
            }
            save_json(default_profile / "config.json", profile_config_data)

            # 更新全局 config
            if "active_profile" not in config.app_config:
                config.app_config["active_profile"] = default_name
                save_json(config.BASE_DIR / "config.json", config.app_config)

            print(f"[v0.6.5] 已自动迁移数据到 profiles/{default_name}/")

    # ── Profile 加载 ──

    def load_profile(self, profile_name):
        """v0.6.5: 动态加载指定剧本的所有数据"""
        app = self.app
        app.profile_dir = config.PROFILES_DIR / profile_name
        app.char_dir = app.profile_dir / "characters"

        # 确保目录存在
        app.profile_dir.mkdir(parents=True, exist_ok=True)
        app.char_dir.mkdir(parents=True, exist_ok=True)
        (app.profile_dir / "chats").mkdir(exist_ok=True)

        # 加载 profile 专属配置
        app._profile_config = load_json(app.profile_dir / "config.json")
        ac = app._profile_config.get("app", {})
        tc = app._profile_config.get("turn", {})
        sc = app._profile_config.get("speed", {})

        app.title = ac.get("title", profile_name)
        app.turn_order = list(tc.get("order", []))
        app._raw_turn_order = app.turn_order  # 暂存
        app.speed = max(1, min(10, sc.get("default", 3)))
        app.director_mode = ac.get("director_mode", False)
        app.user_mode = ac.get("user_mode", False)

        # 加载场景
        app.scenes = load_json(app.profile_dir / "scenes.json") or []
        if not app.scenes:
            app.scenes = [{"time": "傍晚", "location": "", "scene": "一个普通的场景", "mood": "普通"}]
        app.scene_idx = 0

        # 加载角色
        app.characters = {}
        if app.char_dir.exists():
            for f in sorted(app.char_dir.glob("*.json")):
                try:
                    c = json.loads(f.read_text("utf-8"))
                    app.characters[c["name"]] = c
                except:
                    pass

        # 派生样式
        app.char_styles = {
            c["name"]: {
                "color": c.get("color", "#888"),
                "bg": c.get("bg_color", "#f5f5f5"),
                "name": c.get("display_name", c["name"]),
            }
            for c in app.characters.values()
        }

        # v0.9.x: 过滤发言顺序，只保留存在于当前角色列表中的名字（含 You）
        valid = set(app.characters.keys())
        if hasattr(app, '_raw_turn_order'):
            app.turn_order = [n for n in app._raw_turn_order if n in valid]
            del app._raw_turn_order
        else:
            app.turn_order = [n for n in app.turn_order if n in valid]

        # v0.9.x: 迁移 — 用户模式开启且 You 存在但不在发言顺序中时，自动追加
        if app.user_mode and "You" in app.characters and "You" not in app.turn_order:
            app.turn_order.append("You")

    # ── Profile 查询 ──

    def get_profile_list(self):
        """v0.8.7: 获取所有可用剧本名称列表（按 config.json 修改时间倒序）"""
        if not config.PROFILES_DIR.exists():
            return ["dorm_girls"]
        profiles = []
        for p in config.PROFILES_DIR.iterdir():
            if p.is_dir() and (p / "config.json").exists():
                mtime = (p / "config.json").stat().st_mtime
                profiles.append((p.name, mtime))
        profiles.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in profiles] or ["dorm_girls"]

    def get_profile_display_names(self):
        """v0.6.5: 获取剧本显示名称列表（用于 UI 下拉）"""
        names = []
        for pn in self.get_profile_list():
            pc = load_json(config.PROFILES_DIR / pn / "config.json")
            dname = pc.get("app", {}).get("display_name", pn)
            names.append(dname)
        return names

    def profile_name_to_display(self, folder_name):
        """v0.6.5: 文件夹名 -> 显示名"""
        pc = load_json(config.PROFILES_DIR / folder_name / "config.json")
        return pc.get("app", {}).get("display_name", folder_name)

    def profile_display_to_name(self, display_name):
        """v0.6.5: 显示名 -> 文件夹名"""
        for pn in self.get_profile_list():
            if self.profile_name_to_display(pn) == display_name:
                return pn
        return display_name

    # ── 数据 I/O ──

    def _safe_write(self, path, data, desc=""):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存失败: {desc} - {e}")
            return False

    def _save_scenes(self):
        if not self._safe_write(self.app.profile_dir / "scenes.json", list(self.app.scenes), "scenes"):
            self.app._set_status("保存场景失败！", "#ef5350")

    def _save_config(self):
        if not self._safe_write(config.BASE_DIR / "config.json", config.app_config, "config"):
            self.app._set_status("保存配置失败！", "#ef5350")

    def _save_turn_order(self):
        pc = self.app._profile_config
        pc.setdefault("turn", {})["order"] = self.app.turn_order
        save_json(self.app.profile_dir / "config.json", pc)

    def _save_character(self, filename, data):
        if not self.app.char_dir:
            return
        self.app.char_dir.mkdir(parents=True, exist_ok=True)
        if not self._safe_write(self.app.char_dir / filename, data, "character"):
            self.app._set_status("保存角色失败！", "#ef5350")

    def _delete_character(self, name):
        if not self.app.char_dir:
            return
        fpath = self.app.char_dir / (name + ".json")
        if fpath.exists():
            fpath.unlink()

    def _reload_data(self):
        """v0.6.5: 从当前剧本目录重新加载角色/样式"""
        app = self.app
        if not app.char_dir:
            return
        app.characters.clear()
        app.char_styles.clear()
        if app.char_dir.exists():
            for f in sorted(app.char_dir.glob("*.json")):
                try:
                    c = json.loads(f.read_text("utf-8"))
                    app.characters[c["name"]] = c
                except:
                    pass
        app.char_styles = {
            c["name"]: {
                "color": c.get("color", "#888"),
                "bg": c.get("bg_color", "#f5f5f5"),
                "name": c.get("display_name", c["name"]),
            }
            for c in app.characters.values()
        }
