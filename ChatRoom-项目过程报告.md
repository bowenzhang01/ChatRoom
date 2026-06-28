# ChatRoom 项目开发过程报告

> **项目代号**：ChatRoom（曾用名：Dorm Life / 室友日常 / 女生寝室）  
> **项目周期**：2026年6月17日 — 2026年6月26日（持续10天）  
> **开发方式**：人机协作（用户主导需求 + AI助手辅助执行）  
> **当前版本**：v0.9.1（拖拽排序发言顺序 + 角色池管理）  
> **报告日期**：2026年6月28日（含 v0.9.0 → v0.9.1 更新）

---

## 一、项目概述

### 1.1 项目定义

ChatRoom 是一个基于大语言模型（LLM）的多角色 AI 对话模拟应用。用户创建多个具有独立人格的虚拟角色，由 DeepSeek API 驱动角色间的自动对话。应用支持导演模式（人工干预对话走向）和用户模式（用户以角色身份参与对话）。

### 1.2 最终交付物

| 产物 | 平台 | 框架 | 打包方式 | 状态 |
|------|------|------|----------|------|
| ChatRoom v0.5.1 (桌面版) | Windows | tkinter | PyInstaller → .exe | ✅ 已完成 |
| ChatRoom v0.5.3 (移动版) | Android | Kivy | Buildozer → .apk | ✅ 已完成 |
| **ChatRoom v0.6.5（移动版）** | **Windows/Android** | **Kivy** | **Buildozer → .apk** | **✅ 已完成** |
| 配置文件集 | 跨平台 | JSON | 纯文本 | ✅ 已统一 |

### 1.3 技术栈总览

```
前端层：  tkinter (桌面) / Kivy (移动，纯原生，零 KivyMD 依赖)
AI 层：   DeepSeek API (deepseek-chat / v4-flash / v4-pro)
          AI 辅助系统：场景/角色/设置 AI 补全与生成
          世界观系统：跨 AI 操作共享上下文锚点
          一键创建剧本：一句话 → 完整多角色剧本
打包层：  PyInstaller (桌面) / Buildozer + p4a (移动)
平台层：  Windows 11 + WSL2 (Ubuntu 24.04)
语言：    Python 3.x（约 4650 行主程序）
网络：    v2rayN 代理 + ghproxy 镜像 + 清华 PyPI 镜像
```

---

## 二、版本演进历史

ChatRoom 在短短6天内经历了从原型到多平台分发版本的快速迭代：

### 2.1 Version Timeline（按 CHANGELOG.md）

```
2026-06-17 ━━━━━━━━━━━━━━━━━━━━━━━━ 项目诞生日（10个版本，同日完成）
│
├── v1.0～v0.5.1  ……（详见上文）
│
2026-06-22 ━━━━━━━━━━━━━━━━━━━━━━━━ 第二次重大回退
│
├── 放弃 KivyMD 2.0：回退纯 Kivy 原生 Button
│    解决 6 层依赖链问题 / buildozer.spec 大瘦身
│    APK 体积从 ~58MB → ~25MB / minapi 31 → 21
│
2026-06-23 ━━━━━━━━━━━━━━━━━━━━━━━━ UI 精装修 & 新功能 & 架构升级（今日）
│
├── v0.5.3  聊天气泡系统（Canvas RoundedRectangle）
├── v0.5.3  API 模型自动获取 + 下拉选择 + 持久化
├── v0.5.3  Markdown 转 Kivy Markup（**粗体** / *动作*）
├── v0.5.3  删除「说一句」单步发言功能（含 UI + 死锁 bug）
├── v0.5.3  TextInput 零宽度渲染 Bug 彻底修复
├── v0.5.3  工具栏三按钮宽高字体统一
├── v0.5.3  发言顺序 You 可视化 + 保存过滤
├── v0.5.3  自定义模型弹窗 / Spinner 颜色统一
│
├── v0.6.5  ★ 多剧本/多配置组系统（profiles/ 目录隔离）
├── v0.6.5  ★ 剧本切换（强制清空上下文 + Spinner UI）
├── v0.6.5  ★ 新建/删除剧本（中文名自动→英文文件夹名）
├── v0.6.5  ★ You 角色硬编码"室友"→数据驱动 prompt_hint
├── v0.6.5  ★ 全局变量→App 动态属性（SCENES/CHARACTERS/CHAR_STYLES等）
├── v0.6.5  ★ 首次启动自动迁移旧数据→profiles/
├── v0.6.5  ★ 剧本文件夹英文名 + display_name 中文显示
│
├── v0.6.5 隐藏 Bug 修复×5（Android路径/气泡宽度/标题引用/僵尸线程/发言校验）
├── v0.6.5 Emoji 清理（Kivy不支持，代码+配置文件全剥离）
├── v0.6.5 全部按钮圆角化（RoundedButton + ColoredButton 按下变深）
├── v0.6.5 buildozer.spec 打包适配 + Android init 时机修正
└── v0.6.5 回底按钮等高 / 设置按钮圆角 / 删除剧本功能

2026-06-24 ━━━━━━━━━━━━━━━━━━━━━━━━ AI 辅助系统 + 世界观 + 一键创建（今日）
│
├── v0.7.0  新增地点字段（场景 time→location→mood 完整信息链）
├── v0.7.0  AI 场景补全 / AI 场景生成（弹窗输入一句话→完整场景）
├── v0.7.0  AI 角色补全 / AI 角色生成（弹窗输入一句话→完整角色含 system_prompt）
├── v0.7.0  extract_json() 通用 JSON 清洗（代码块剥离 + 尾部逗号修复 + 数组回退）
├── v0.7.0  角色管理按钮顺序修正（保存/添加/删除）
├── v0.7.0  弹窗空档修复（Widget 弹性空间法）
├── v0.7.0  AI 调用加载弹窗（show_loading 可切换参数）
│
├── v0.7.1  世界观/大背景系统（world.setting 字段）
├── v0.7.1  AI 推断世界观（根据已有场景+角色→生成世界设定）
├── v0.7.1  AI 补全设置 / AI 生成设置（标题/欢迎文字）
├── v0.7.1  场景/角色 AI 提示词全部接入世界观锚点
├── v0.7.1  3 个现有 Profile 的 config.json 预填默认世界观
│
├── v0.7.2  AI 一键创建完整剧本
│   ├── 调用1：生成规划（world, scenes_hints, char_hints, app, you_hint, turn_order）
│   └── 调用2：10路延缓分派（app+4场景+4角色+You）→复用已有AI生成逻辑
├── v0.7.2  config.json max_tokens: 300→500
├── v0.7.2  剧本管理行新增「AI创建」按钮
├── v0.7.2  错误提示简化（短名称 + TextInput 可滚动换行）
│
├── v0.7.3  BubbleLabel Window.unbind 内存泄漏修复
├── v0.7.3  API 429 限流防护（延缓分派 STAGGER_MS=350ms）
├── v0.7.3  文件夹命名统一使用 _make_safe_folder_name()
├── v0.7.3  turn_order 改名全量替换（列表推导取代 .index()）
└── v0.7.3  extract_json 新增数组 [ ... ] 回退正则

2026-06-26 ━━━━━━━━━━━━━━━━━━━━━━━━ UI 重构 & 对话存档系统（今日）
│
├── v0.7.5  ★ 设置页 Tab 重组：新增「剧本」Tab（置于「场景」之前）
│   ├── 从「设置」Tab 拆分出：应用标题/欢迎标题/欢迎文字/世界观/发言顺序/AI补全/AI生成
│   ├── 「剧本」Tab 独立保存按钮
│   ├── 「设置」Tab 精简为仅保留剧本套件切换 + 导出日志/复制对话
│   └── Tab 按钮全部复用 RoundedButton 圆角样式
├── v0.7.5  默认打开设置页改为「剧本」Tab
├── v0.7.5  发言顺序输入框初始不显示文字 → 复用 v0.5.3 修复方案（空初始化 + 延迟注入）
│
├── v0.8.0  ★ 对话存档系统（保存/读取/删除）
│   ├── 每个 Profile 下新建 chats/ 目录
│   ├── 文件命名：chat_YYYYMMDD_HHMMSS.json（纯英文时间戳）
│   ├── AI 自动生成对话标题（5-15字），备选方案「剧本名 - 场景 - 时间」
│   ├── 保存流程：写临时标题 → 后台线程调 AI 生成标题 → 回写正确标题 → 弹窗反馈
│   ├── 读取流程：确认弹窗 → 停止当前 → 恢复 history/turn_idx/turn_count/scene → 重建 chat_view
│   └── 删除流程：确认弹窗 → 删文件 → 刷新下拉列表
├── v0.8.0  ★「设置」Tab 新增对话管理 UI
│   ├── Spinner 下拉列表：{标题前20字} {MM-DD} ({N}条)
│   ├── [读取] [删除] 按钮（含确认弹窗）
│   └── [保存当前对话] [复制全部对话] 按钮
├── v0.8.0  ★ Android 自动存档（on_pause）
│   ├── 切后台时：有新消息 → 静默写 _autosave.json；无变化 → 跳过
│   ├── 标题使用备选方案（不调 AI，节省时间窗口）
│   └── 消息数量对比去重（非时间去重）
├── v0.8.0  ★ 启动自动存档恢复
│   ├── 启动时检测 chats/_autosave.json → 弹窗问「是否恢复？」
│   ├── [恢复]：加载历史 + 重建 chat_view + 暂停状态
│   └── [放弃]：删除 _autosave.json + 正常欢迎页
├── v0.8.0  ★ 破坏性操作保存提醒
│   ├── 停止按钮：有新消息且 30s 内未保存 → 三选一弹窗 [保存并停止] [直接停止] [取消]
│   ├── 切换剧本：有新消息且 30s 内未保存 → 新增 [保存并切换] 按钮
│   └── 无消息或已保存 → 无提醒，直接执行
├── v0.8.0  新建剧本（手动/AI）自动创建 chats/ 目录
│
├── v0.8.1  保存后对话列表不刷新 → 新增 _refresh_chat_list() 方法
├── v0.8.2  删除主界面「重置」按钮（停止按钮已覆盖全部功能）
├── v0.8.2  移除全部 Kivy 不支持的特殊符号（emoji / 标记字符）
├── v0.8.3  修复保存后清空对话 → 0 条记录的 bug
│   └── 根因：_on_title_ready 回调读写 self.history 时已被 _do_reset() 清空
│   └── 修复：保存时拍快照 saved_data = {history: list(self.history), ...}，回调用快照
├── v0.8.4  确认导演模式/用户模式消息可正确保存与读取（链路验证通过）
└── v0.8.5  AI 标题生成修复（核心：max_tokens 50→300 + 复用 extract_json + 错误日志）
    ├── max_tokens 太小：DeepSeek R1 的 <think> 标签消耗 token 预算 → 截断输出 → JSON 解析失败
    ├── 脆弱正则替换为全局 extract_json()：处理 <think> 标签/markdown 代码块/尾部逗号/json5
    └── except Exception 静默吞噬 → 添加 print 错误日志
└── v0.8.6  ★ Spinner 下拉文字溢出修复（FitSpinnerOption 自动换行类）

├── v0.8.6  ★ 动态发言顺序系统（三次架构迭代）
│   ├── 问题："轮流"/"随机"两种模式无视对话内容
│   ├── 目标：根据剧情内容动态调整发言顺序
│   ├── 迭代一：独立 AI 导演（导演 API → JSON 解析 → 纯名字输出）
│   │   ├── 发现：50% JSON 解析失败率、100% 缓存未命中、成本高
│   │   ├── 根因1：DeepSeek V4 <think> 标签消耗 token / 吞掉输出
│   │   ├── 根因2：导演 prompt 角色列表与 turn_order 一致 → 位置偏差
│   │   └── 结论：放弃独立导演方案
│   ├── 迭代二：纯规则引擎（沉默/点名/反重复/NEXT提示 四条规则加权随机）
│   │   └── 零成本、零延迟，但缺乏语义理解
│   └── 迭代三（最终方案）：角色嵌入点名 + 规则引擎兜底
│       ├── 动态模式下，角色 prompt 末尾追加 [NEXT:Name] 指令
│       ├── _handle_cmd("msg") 提取并剥离 [NEXT]（UI 不可见）
│       ├── [NEXT] 作为规则引擎 ×5.0 权重（约 65% 命中率）
│       └── 非动态模式完全不受影响（_build_next_hint 返回 ""）
├── v0.8.6  沉默追踪系统（_char_last_turn 字典）
│   ├── 每次发言后更新 _char_last_turn[name] = turn_count
│   ├── 切换剧本 → _do_reset() 清零
│   ├── 加载存档 → 遍历 history 重建
│   └── 硬兜底：沉默 >= 15 轮强制插入（跳过规则引擎）
├── v0.8.6  模式三态切换：轮流 → 随机 → 动态
├── v0.8.6  全量版本号修正（v0.6.6 残留标签 → v0.8.0 / v0.8.6）
└── v0.8.6  导演调试日志（控制台权重拆解：hint/沉默/点名/自罚 可视化）
```

### 2.2 架构演变路径

```
v1.0:  CLI 脚本
  ↓
v2.0:  FastAPI + WebSocket（Web 服务）
  ↓
v0.3.0:  tkinter 桌面应用（Windows 原生）
  ↓
v0.3.2:  PyInstaller → 可分发的 .exe
  ↓
v0.4.0:  导演模式（人机混合对话）
  ↓
v0.5.0:  用户模式 + 双开关
  ↓
并行:  Kivy 移动版 → Android APK
  ↓
v0.5.3:  纯 Kivy 聊天气泡 + 模型下拉 + Markdown 渲染
  ↓
v0.6.5:  多剧本多配置组系统（profiles/ 目录隔离）
  ↓
v0.6.5: 圆角按钮 + Android 存储适配 + 隐藏 Bug 修复
  ↓
v0.7.0:  场景地点字段 + AI 补全/生成（场景 & 角色）
  ↓
v0.7.1:  世界观系统 + AI 推断/补全/生成设置
  ↓
v0.7.2:  AI 一键创建完整剧本（规划→10路并行→写入）
  ↓
v0.7.3:  深层 Bug 修复（Window 内存泄漏/429 限流/文件夹命名/turn_order/extract_json）
  ↓
v0.7.5:  UI 重构 — 设置页 Tab 重组，新增「剧本」Tab（世界观统一管理）
  ↓
v0.8.0:  对话存档系统 — 保存/读取/删除 + AI 标题 + 自动存档恢复
  ↓
v0.8.5:  存档 Bug 修复 — 快照防清零 / AI 标题生成修复 / 列表刷新 / UI 清理
  ↓
v0.8.6:  动态发言顺序 — 三次架构迭代（导演API→规则引擎→角色嵌入+规则兜底）
```

---

## 三、项目分支结构

开发过程中自然分化出三个并行目录：

| 目录 | 主文件 | 框架 | 用途 | 创建时间 |
|------|--------|------|------|----------|
| `dorm-life/` | `main.py` | Kivy | Android APK 构建（WSL中） | 6/17 08:08 |
| `dorm-life-clean/` | `dorm_app.py` | tkinter | Windows 桌面版 + PyInstaller 打包 | 6/17 13:27 |
| `dorm-clean/` | `main.py` | Kivy/KivyMD 2.0 | Android 版（配置已统一为小雪阵容） | 后续创建 |

**分支关系**：
- `dorm-life` 和 `dorm-clean` 共享 Kivy 核心逻辑，配置文件 / 角色阵容可互换
- `dorm-life-clean` 为独立的 tkinter 重写，核心逻辑（LLM 调用 / 角色管理 / 场景切换）与 Kivy 版功能等价
- Android 构建资源共享：SDK、NDK、预下载包、ghproxy 版本 p4a

---

## 四、开发过程详细日志

### 4.1 第〇日：6月16日（周日）— 前奏

在 ChatRoom 项目正式启动之前，当天主要成果是完成了小说《四人之家》的创作工作：

- **下午 14:00—15:30**：使用 novel-writer 技能的"隔离锚定法"，通过 8 个子代理并行写出《四人之家》第7—20章。每个子代理独立负责一章，采用第三人称限知视角、高感官密度文风、角色语言指纹（莉莉的"～/人家"、凯特的"呢/啦"等反退化规则。

- **深夜 23:00 左右**：将小说《我们的屋檐下》全 20 章导出为排版精美的 Word 文档（宋体12号/1.5倍行距/首行缩进/每章分页）。

> 📌 这两部小说中的四名角色（莉莉/简/吉尔/凯特）后来成为了 ChatRoom 安卓版的第一代角色阵容，与小说形成了世界观的交叉。

### 4.2 第一日：6月17日（周三）— 爆发式开发

这是整个项目最密集的一天，当天完成了从 v1.0 到 v0.3.9 共 **10 个版本**的迭代。

#### 上午（08:00—12:00）：从零到桌面应用

- **v1.0**（约 08:00）: 项目创建。核心是一个 Python 脚本，调用 DeepSeek API 驱动 4 个 AI 角色（初始阵容为特殊设定角色：莉莉、简、吉尔、凯特）进行轮流发言。
- **v2.0**: 升级为 Web 版。FastAPI + WebSocket 实现浏览器实时对话，HTML/CSS 打造精美界面。
- **v0.3.0**: 桌面版 Tkinter 应用诞生。完整 GUI，场景/角色管理面板、日志保存功能。

#### 下午（13:00—17:00）：打磨与外部化

- **v0.3.1—v0.3.2**: 将所有配置（API Key、场景、角色）外部化为 JSON 文件。添加首次配置向导。用 PyInstaller 打包为独立 .exe。
- **v0.3.3—v0.3.5**: UI 清理。移除随机事件系统（避免打断剧情）、天数计数、精简按钮。
- **v0.3.6—v0.3.9**: Bug 修复密集期。文件写入加异常保护、角色改名 bug、turn_order 同步、日志保存优化、首次向导增强。

> 📌 当天完成了 `CHANGELOG.md` 的撰写并放入两个项目目录。

#### 晚间（20:00—深夜）：Android 移植启动

- 尝试在 WSL2 中为 dorm-life 构建 Android APK
- 诊断发现 WSL2 已安装但 **没有 Ubuntu 发行版**
- 指导用户执行 `wsl --install -d Ubuntu`

### 4.3 第二日：6月18日（周四）— 桌面版分发 & Android 地狱

#### 桌面版打包（上午）

- 清理 `dorm-life-clean` 的 API key
- 配置导演模式/用户模式默认关闭，确保干净分发
- PyInstaller 打包 → `ChatRoom.exe`（8.9 MB）
- 封装为 `chatroom v0.4.0.zip`（33.6 MB，含所有依赖）
- 分发结构：解压即用，首次运行弹出 API Key 配置向导

#### UI 细节打磨（下午）

- 统一标签颜色（场景/角色/API/设置标签 → 统一浅色系）
- 移除 icon 字段的输入和保存逻辑（Kivy 版残留字段）
- 按钮文字保持不变

#### Android 编译 16 坑（晚间—深夜）

这是整个项目中**技术难度最高**的阶段。从零开始搭建 Android 交叉编译环境，遇到以下问题：

**环境层（3 项）**：
1. `libtinfo5` → `libncurses-dev`（Ubuntu 24.04 兼容）
2. PEP 668 pip 限制 → 创建独立 venv
3. Kivy 编译失败 → 安装 SDL2/GL 系统库

**网络层（4 项）**：
4. GitHub SSL/超时 → ghproxy 镜像全局替换
5. v2ray WSL 不通 → 尝试过 mirrored 模式、proxychains 均失败；最终重启 v2rayN + ghproxy
6. 11 个源码包逐个卡 → Windows 端手动代理下载 + `.mark-` 标记文件
7. googlesource.com 子模块 → 直接删除 `.gitmodules` 引用

**编译层（1 项）**：
8. NDK r28c + glibc 头文件冲突 → 卸载宿主系统 SDL2 开发包

**代码层（3 项）**：
9. `BASE_DIR` 未定义闪退 → 字体注册移到变量定义后
10. JSON 被 PowerShell 清空 → 改用 Python 脚本
11. `color=` 参数重复 → 手动删除

**字体层（3 项）**：
12. 中文全方块 → 替换 Kivy 默认 Roboto 为系统 CJK 字体
13. 切标签页字体消失 → `_switch_tab` 后重新注入
14. Emoji 方块 → 清理配置 emoji

**UI层（2 项）**：
15. 场景横幅太小 → 自适应高度
16. 设置页空档 → `size_hint_y=None`

> 📄 当晚完成 `dorm-life-android-bug-report.md`，完整记录了全部 16 个问题。

### 4.4 第三日：6月19日（周五）— 多线并行

#### dorm-clean 启动

- 将 dorm-life 项目配置改造为独立的 dorm-clean
- 应用名改为 **Chatroom**（取代原来的 Roommate Daily）
- 通过软链接复用 dorm-life 的 SDK/NDK/预下载包/ghproxy 版 p4a
- 网络问题再度出现（httpx 下载卡住）
- 用户表态"给我指令，我自己编译"，标志着协作模式的一次调整

### 4.5 第四日：6月20日（周六）— 版本回退的艰难抉择

#### v0.5.1 崩溃诊断

- dorm-clean 编译出的 APK 启动即闪退
- 对比备份文件 `main_backup_before_ui_20260621_162924.py`（v0.5.1 功能代码，UI 改动前）与原始 v0.3.10
- 语法验证通过 → 确认非语法错误
- **结论：v0.5.1 新增的 572 行功能代码中，某项在 Android 环境有兼容性问题**
- **决策：回退到 v0.3.10（已验证工作的版本），仅施加最小必要修复**（字体名 + 关键 bug fix）

#### 第二轮编译诊断

- Git Clone 断连：zlib、dav1d、libavif、libjxl 四个子模块无法从 GitHub 克隆
  - 解决：从 `p4a_cache` 缓存解压到对应目录
- PyPI 下载超时：patchelf、Cython、build 等包超时
  - 解决：配置清华 PyPI 镜像 + 环境变量双重保险
  - 创建 `build_with_mirror.sh` 脚本

#### ChatRoom 桌面版 v0.4.0 分发版

- 确认 exe 打包完成
- API key 已清空
- 导演模式默认开启
- 输出：`chatroom v0.4.0.zip`（33.6 MB）

### 4.6 第五日：6月21日（周日）— 清理与预览

#### Emoji / 颜文字清理

- 将 `main.py` 中所有按钮/标签/输入栏中的 emoji 和 `[font=IconFont]` 标记全部删除
- 按钮文字恢复纯中文：`[>] 开始` → `开始`、`[||] 暂停` → `暂停`、`[font=IconFont]💬[/font] 说一句` → `说一句` 等
- 删除 `NotoEmoji-Regular.ttf` 注册代码
- 代码精简约 1.5KB

#### 寻找预览方案

- 推荐 Windows 原生 Kivy（`pip install kivy` → 直接跑 `main.py`）
- 备选 WSL + X Server（VcXsrv），但设置更复杂
- 目的：缩短"编译 APK → 传手机 → 安装 → 测试"的反馈循环（每次 15-30 分钟）

### 4.7 第六日：6月22日（周一）— 最漫长的一天

今日分成四个阶段，横跨多个 session：

#### 阶段一：KivyMD 1.2 / 2.0 版本冲突排查（上午 09:00—10:30）

前一日留下的 APK 编译成功但启动闪退。通过 adb pull crash log 逐层追踪：

- **第一次闪退**：`ModuleNotFoundError: No module named 'materialyoucolor'`
  - 原因：KivyMD 2.0 新增依赖，buildozer.spec 中未声明
  - 修复：添加 `materialyoucolor`

- **第二次闪退**：编译成功，启动成功，但 **点击按钮即闪退**
  - Crash log 追踪调用链：
    ```
    鼠标悬停 → hover_behavior → state_layer_behavior →
    navigationdrawer → appbar → asynckivy → asyncgui ❌ ModuleNotFoundError
    ```
  - 原因：`asynckivy` 又依赖 `asyncgui`（依赖的依赖，被遗漏）
  - 同时发现 `materialshapes` 依赖 `pycairo`（系统级 cairo 绑定）
  - 用户要求：**"一次性添加所有可能需要的依赖"**

- **完整 KivyMD 2.0.1.dev0 依赖树分析**：
  ```
  kivymd (2.0.1.dev0)
  ├── kivy>=2.3.0              ✅ 已有
  ├── pillow (pil)             ✅ 已有
  ├── materialyoucolor>=2.0.7  ✅ 新增（动态取色引擎）
  │   └── pillow               ✅ 已有
  ├── materialshapes>=0.3      ✅ 新增（Material 形状组件）
  │   └── pycairo              ✅ 新增（p4a 有 recipe）
  ├── asynckivy>=0.6           ✅ 新增（异步事件）
  │   └── asyncgui             ✅ 新增（asynckivy 底层库）
  ```
  - 最终 requirements：`kivymd_master.zip,pil,materialyoucolor,materialshapes,asynckivy,asyncgui,pycairo`

- **KivyMD 版本共存问题**：
  - APK 中同时存在 `kivymd-1.2.0.dist-info` 和 `kivymd-2.0.1.dev0.dist-info`
  - Python 加载时先找到了 1.2.0（旧版的 `MDButton` 不存在 → ImportError）
  - 用户解释了根因：之前的 session 中第一次 UI 美化用的是 1.2.0，编译后觉得效果不好，才让莉莉改成了 2.0 API。p4a 的 dist 缓存保留了旧版。
  - 尝试 PEP 508 格式 `kivymd @ file:///...` 强制指向本地 → 需要清 dist 缓存 → 触发重新 clone 外部依赖 → 网络断连

#### 阶段二：NDK 下载与指令模式切换（上午 10:30 左右）

- NDK r25b 从 Google 下载到 73% 被中断
- 尝试中国镜像 `googledownloads.cn` → 返回错误页面（仅 1449 字节）
- 用户指定 p4a_cache 位置：`C:\Users\bowen\.openclaw\workspace\temp\p4a_cache`
- **用户明确要求**："不要自动编译，给出指令让我来"——协作模式正式切换为指令模式

#### 阶段三：彻底放弃 KivyMD，回退纯 Kivy（中午 12:00—13:00）★ 第二次重大回退

经过上午的多轮 KivyMD 2.0 依赖调试，做出关键决策：

- **用 `main_backup_phase1_20260622.py`（纯 Kivy + 原生 Button，零 KivyMD 依赖）替换了当前 `main.py`**
- 旧版 KivyMD 代码备份为 `main_backup_v0.5.2_kivymd.py`
- 在回退版本上加了两处关键 bugfix：
  1. `import threading` — 防止 `NameError` 闪退
  2. `_save_scenes` / `_save_config` / `_save_character` 失败时状态栏提示

- **buildozer.spec 大瘦身**：

  | 删除项 | 省去内容 |
  |--------|----------|
  | `kivymd_master.zip` (~3MB) | 整个 KivyMD 包 + 5 个传递依赖 |
  | `materialyoucolor` | Material You 动态取色 |
  | `materialshapes` | Material 形状组件 |
  | `asynckivy` | 异步 Kivy 事件 |
  | `asyncgui` | asynckivy 底层库 |
  | `pycairo` | Cairo 2D 图形库绑定 |
  | `pil` | Pillow（未使用） |

  | 新增配置 | 效果 |
  |----------|------|
  | `source.exclude_dirs = tests,bin,backup,.buildozer,__pycache__` | 打包时排除无关目录 |
  | `source.exclude_patterns = *backup*.*` | 排除所有备份文件 |
  | `android.minapi = 31 → 21` | 支持 Android 5.0+（之前被 KivyMD 2.0 限制在 31） |

- **预估 APK 体积：从 ~58MB → ~25MB 以下**

#### 阶段四：配置统一 & 架构厘清（下午 12:30—13:00）

- 从 `dorm-life-clean` 复制配置文件到 `dorm-clean`：
  - `config.json`（API key 已清空，标题改为"🏠 室友日常"，导演模式默认开启）
  - `scenes.json`（4 个场景：清晨/午后/深夜/雨天）
  - `characters/`（5 个角色：小雪/小梅/小林/小瑞 + 用户角色）
- 旧角色备份到 `characters_backup_v0.5.1/`
- JSON 格式完全兼容（多了一个 `icon` 字段但代码不读，无影响）

- **最终确认**：两个项目的核心逻辑完全相同，差异仅在：
  - `dorm-life-clean` = tkinter（Windows 原生外观，零依赖）
  - `dorm-clean` = 纯 Kivy + 原生 Button（Material Design 风格）

#### 阶段五：本报告撰写（下午 14:00—14:30）

- 回顾 6 月 16—22 日全部 session 记录
- 结合 CHANGELOG.md、bug-report.md 等技术文档
- 产出本过程报告

### 4.8 第七日：6月23日（周二）— UI 精装修 & v0.5.3 新功能

今日是 UI 打磨 + 功能增强最为密集的一天，完成了聊天气泡系统、API 模型管理、Markdown 渲染等多项核心改进。

#### 会话一：API 模型自动获取与下拉选择（上午 11:00—12:00）

- **Model 输入框改造**：将原本的手动 `TextInput` 替换为 `Spinner` 下拉选择器
- **自动获取可用模型**：`_test_api` 测试成功后，请求 `{api_base}/models` 获取模型列表，去重排序后填充到下拉框
- **持久化缓存**：模型列表写入 `config.json` 的 `models` 字段，重启后无需重新获取
- **自定义模型弹窗**：Spinner 末尾始终有「自定义…」选项，选中弹出对话框输入任意模型名
- **逻辑精修**：
  - 只有测试 200 成功才更新列表，失败不动
  - 更换 API Base → 测试成功 → 新列表覆盖旧列表
  - "You" 永远不存 config，运行时动态追加
- **Spinner 颜色统一**：`background_normal=""` 去掉默认纹理，与 TextInput 颜色一致

#### 会话二：TextInput 零宽度渲染 Bug 彻底修复（下午 12:00—12:10）

- **根因分析**：`clear_widgets()` + 立即 `add_widget` → TextInput 在布局定型前被赋长文本（如 `https://api.deepseek.com`）→ Kivy 内部 `scroll_x` 在零宽度时错位锁死 → 文字渲染到视口之外
- **组合拳修复**：
  1. 初始化 `text=""`（不在零宽度时塞长文本）
  2. `padding=[dp(10), dp(10), dp(10), dp(10)]`（对称填充，防垂直偏移裁剪）
  3. `Clock.schedule_once(0.1s)` 延迟注入真实文本
  4. `scroll_x = 0`（强制复位视口）
- **修复范围**：API Key、API Base、应用标题、欢迎标题、欢迎文字、发言顺序共 6 个输入框

#### 会话三：删除「说一句」功能（下午 15:20—15:30）

- **原因**：手动单步发言存在两个隐蔽 bug —（1）`_handle_cmd` 中 `msg` 命令需 `self.running` 才生效，但手动发言在暂停状态，导致消息被丢弃；（2）`_is_stepping` 防抖锁从未复位，触发一次即永久死锁
- **清理内容**：
  - 角色设置页「说一句」按钮 UI + 绑定
  - `_speak_char()` 方法
  - `_do_step_character()` 完整方法（含 `_is_stepping` 防抖逻辑）
  - `_handle_cmd` 中 `"step"` 分支
  - `_show_input_bar` 中 `"user_single"` 模式
  - `_send_input` 中 `"user_single"` 分发
  - `_update_char_buttons` 中的 `_speak_btn` 相关逻辑
- **保留**：Bug #2（设置弹窗关闭后自动恢复）按设计保持不动

#### 会话四：发言顺序 You 可视化（下午 15:27）

- `_refresh_app_inputs`：用户模式下，发言顺序输入框末尾追加显示 `You`
- `_save_app_settings`：保存时过滤掉 `You`，防止写入 config 导致重复
- 导演模式下不显示 `You`，干净准确

#### 会话五：聊天气泡系统（下午 15:43—16:00）★

- **核心组件**：
  - `BubbleLabel(Label)`：Canvas `RoundedRectangle` 动态绘制圆角背景，`texture_size` 自适应宽高，最大宽度 65% 屏幕，`dp(13)` 字体
  - `ChatMessageRow(BoxLayout)`：水平布局 + `Widget(size_hint_x=1)` 弹簧占位，左对角色（灰底黑字）、右对 You/导演（蓝底白字）
- **替换范围**：完全取代旧的 `ChatMessage` 类和 `ChatView.add_message`
- **保留逻辑**：垫片沉底、300 条限制、回底按钮、`get_all_text` 导出
- **备份**：`main_backup_before_bubble_20260623.py`

#### 会话六：Markdown 转 Kivy Markup（下午 16:00—16:07）

- 新增 `parse_markdown_to_kivy_markup()` 函数
- `**粗体**` → `[b]粗体[/b]`（Kivy 原生粗体）
- `*动作/心理描写*` → `[color=#8a8a8a]动作[/color]`（灰色，免疫中文字体缺斜体问题）
- 右侧气泡（蓝底）自动替换为 `#bbdefb` 浅蓝，防止深灰在蓝底上看不清
- `BubbleLabel.markup = True` 开启富文本引擎

#### 会话七：工具栏三按钮统一（下午 16:07—16:13）

- 速度 Spinner "3"、模式按钮 "轮流"、设置按钮 "设置" 全部统一为：
  - 宽度 `dp(54)`
  - 高度 `dp(36)`
  - 字体 `dp(12)`
- 问题原因：Spinner 用了 `sync_height=True` 自适应、模式按钮用了 `size_hint_y=1` 拉伸填满，三者高度各不同

#### 今日技术要点

- **Canvas RoundedRectangle**：纯 GPU 渲染圆角，零纹理图片，长列表滚动丝滑
- **`parse_markdown_to_kivy_markup`**：轻量正则替换，`re.sub(r'\*(.*?)\*', …)` 精准匹配单星号
- **零宽度 Bug 修复**：`scroll_x=0` 是核心，`inp.text = inp.text` 无效的原因是它不会重置已错位的滚动偏移
- **「说一句」死锁**：`_is_stepping = True` 后无任何 `finally` 复位，除冷重启外无解

### 4.9 第七日（续）：v0.6.5 多剧本架构升级（晚间 20:00—21:00）

这是项目诞生以来最大规模的架构重构，将 ChatRoom 从单一的"女生寝室扮演"升级为**通用多剧本/多场景 AI 角色扮演平台**。

#### 核心设计：profiles/ 目录隔离

```
dorm-clean/
├── config.json                 # 仅全局: API key, base, model, active_profile
├── main.py                     # v0.6.5 (3014 行)
├── profiles/
│   ├── dorm_girls/             # 剧本 A: 女生寝室（原有数据迁移）
│   │   ├── config.json         #   app.title, welcome, turn.order, display_name
│   │   ├── scenes.json         #   7 个寝室场景
│   │   └── characters/         #   Jane, Jill, Kate, Lily, You
│   └── starship/               # 剧本 B: 星际飞船（全新创建）
│       ├── config.json
│       ├── scenes.json         #   6 个太空场景
│       └── characters/         #   CaptainRex, EngineerYuki, AndroidZoe, You
```

**设计原则**：
- **全局与局部分离**：API 配置留在根 `config.json`，切换剧本不换 API
- **剧本数据隔离**：每个 profile 拥有独立的 `characters/`、`scenes.json`、`config.json`
- **文件夹英文 + UI 中文**：文件夹名用英文（`dorm_girls`/`starship`），`config.json` 中 `display_name` 字段存中文用于 UI 显示
- **切换强清上下文**：调用 `_do_reset()` → 停止线程 → 清空 history → 清空 chat_view → 重新加载

#### 代码重构量（约 400+ 行改动）

| 改动 | 说明 |
|------|------|
| 全局变量→App 属性 | `SCENES`/`CHARACTERS`/`CHAR_STYLES`/`CHAR_DIR`/`TURN_ORDER` 全部移除，改为 `self.scenes`/`self.characters` 等 |
| `load_json()` 签名变更 | 从 `load_json(name: str)` → `load_json(path)`，接受 Path 对象 |
| 新增 `save_json()` | 安全写入 JSON，自动创建父目录 |
| 新增 `load_profile(name)` | 动态加载指定剧本的所有数据（config/scenes/characters/styles） |
| 新增 `switch_profile(name)` | 停止→清空→加载→刷新 UI→持久化 |
| 新增 `_migrate_if_needed()` | 首次启动自动将旧扁平数据迁移到 `profiles/` 下 |
| 新增 `get_profile_list()` 等 | 文件夹名↔显示名 转换方法（`profile_name_to_display`/`profile_display_to_name`） |
| `_build_prompt()` 硬编码修复 | `"is your roommate"` → 读取 `You.json` 的 `prompt_hint` 字段 |
| SettingsPopup 全适配 | 场景/角色管理改用 `self.app.scenes`/`self.app.characters`，保存到 profile 目录 |
| 设置页新增 UI | 剧本切换 Spinner +「新建」按钮 +「删除」按钮 |
| ChatMessageRow 适配 | 气泡着色改用 `App.get_running_app().char_styles` |

#### 配置文件拆分

**根 config.json（v0.6.5 精简后）**：
```json
{
  "model": { "api_key": "...", "api_base": "...", "model": "...", ... },
  "active_profile": "dorm_girls"
}
```

**剧本 config.json（新增 `display_name` 字段）**：
```json
{
  "app": {
    "display_name": "女生寝室",
    "title": "ChatRoom",
    "welcome_title": "欢迎来到女生寝室",
    ...
  },
  "turn": { "order": ["Jane", "Jill", "Kate", "Lily"] }
}
```

#### You.json 的 prompt_hint 数据驱动

```json
// dorm_girls/characters/You.json
"prompt_hint": "is your roommate, sitting right here with you..."

// starship/characters/You.json  
"prompt_hint": "is the First Officer on the bridge with the crew..."
```

代码不再硬编码任何剧本设定，全部由 `prompt_hint` 字段驱动。

#### 新建剧本的中文名处理

- `_make_safe_folder_name()`：纯英文名→小写+下划线；中文名→`profile_` + MD5 前8位
- 文件夹名始终是安全的英文，`display_name` 存中文原文
- Android 文件系统完全兼容

#### 新增「星际飞船」剧本

作为 v0.6.5 的验证案例，手写了完整的第二个剧本：
- **3 个 AI 角色**：雷克斯舰长（沉稳果断）、小雪工程师（活泼好奇）、佐伊仿生人（理性温柔）
- **6 个太空场景**：舰桥日间值班、引擎室巡航、舰员餐厅晚餐、观景台深夜、黄色警报、停泊港休整
- **You 角色**：定位为副官，`prompt_hint` 为 First Officer

### 4.10 v0.6.5—v0.6.5：隐藏 Bug 修复与 UI 精修（晚间 21:00—21:55）

#### v0.6.5：5 个隐藏 Bug 修复

基于代码审查发现并修复了 5 个高危/中危隐患：

| # | Bug | 风险 | 修复方案 |
|---|-----|------|----------|
| 1 | Android 只读路径闪退（`BASE_DIR` 在 APK 中不可写） | 高危 | `_setup_workspace()`：Android 上切换到 `user_data_dir`，首次运行自动复制内置剧本 |
| 2 | 气泡宽度固化（`Window.width * 0.65` 只取一次） | 中危 | `Window.bind(on_resize=...)` 动态更新 `text_size`，软键盘弹出/横竖屏自动适配 |
| 3 | 标题更新靠硬编码 UI 遍历（3 层嵌套 for 循环找 Label） | 中危 | `title_lbl` → `self.title_label`，`switch_profile()` 和 `_do_switch()` 直接赋值 |
| 4 | API 测试僵尸线程污染（旧回调在新剧本执行） | 中危 | 线程创建时记录 `_caller_profile`，Clock 回调前校验 profile 是否一致 |
| 5 | 发言顺序校验缺失（输入"Jame"→KeyError 闪退） | 高危 | `_save_app_settings` 保存时过滤不存在角色名 + `load_profile` 加载时二次校验 |

#### v0.6.5：Emoji 全面清理

- 从 `main.py` 和所有配置文件（config.json、scenes.json、characters/*.json）中剥离全部 emoji 字符
- 原因：Kivy 不支持 BMP 以外字符渲染，Android 上显示为方块
- 共清理 19 个 emoji 字符 + 批量处理所有 profile 的 JSON 文件

#### v0.6.5：全部按钮圆角化（RoundedButton 系统）

**新增类架构**：
```
RoundedButton(Button)              # 圆角按钮基类 — Canvas RoundedRectangle
├── set_bg_color(color)            # 运行时动态改色（支持 hex 字符串或 rgba 元组）
│
└── ColoredButton(RoundedButton)   # 继承 + 按下变深效果
    ├── _on_press_state()          # 按下时颜色 ×0.75，松开恢复
    ├── set_btn_color(color)       # 改正常色 + 自动计算按下色
    └── _darken(hex, factor)       # 颜色加深工具函数
```

**覆盖范围**：

| 位置 | 组件 | 类 | 圆角半径 |
|------|------|-----|----------|
| 底部控制栏 | 开始/暂停/停止/重置 | ColoredButton | `dp(8)` |
| 底部控制栏 | 回底按钮 | RoundedButton | `dp(8)` |
| 顶部工具栏 | 轮流/随机切换 | ColoredButton | `dp(8)` |
| 顶部工具栏 | 设置按钮 | RoundedButton | `dp(6)` |
| 模式栏 | 导演模式/用户模式 | RoundedButton | `dp(6)` |
| 设置弹窗 | 场景/角色/API/设置 tab | RoundedButton | `dp(4)` |
| 输入栏 | 发送/跳过 | RoundedButton | `dp(6)` |
| 速度选择 | Spinner | 保持不变 | — |

所有原来写 `self.xxx.background_color = hex_to_rgba(...)` 的地方全部改为 `set_bg_color(...)` 或 `set_btn_color(...)`，确保 Canvas 背景和逻辑代码同步更新。Spinner（速度选择器）因其内部下拉箭头结构特殊，不纳入圆角化范围。

#### v0.6.5：Android 打包适配

- **buildozer.spec**：
  - `source.include_patterns = profiles/**/*.json`（确保所有剧本 JSON 文件打入 APK）
  - `title = DormLife`（APK 显示名）
  - 虽 `json` 已在 `source.include_exts`，加 `include_patterns` 为双保险
- **init 时机修正**：`_setup_workspace()` 及 `_migrate_if_needed()` / `load_profile()` 从 `__init__` 移到 `build()` 开头。原因：Android 上 `user_data_dir` 在 Kivy App 初始化完成后才就绪，`__init__` 阶段调用过早
- **平台检测精准化**：`sys.platform in ('android', 'ios')` 判断，桌面端不会误切换到 `user_data_dir`

#### v0.6.5：最终打磨

- 回底按钮高度统一为 `dp(36)`（之前无 `size_hint_y=None`，自动拉伸过高）
- 设置按钮从普通 `Button` 改为 `RoundedButton`，风格统一
- 删除剧本功能完善：至少保留一个剧本，确认弹窗后 `shutil.rmtree()` 删除整个 profile 文件夹，若删除的是当前激活剧本则自动切换到第一个可用剧本

### 4.11 第八日：6月24日（周三）— AI 全流程辅助系统 & v0.7.x

今日是项目诞生以来功能增长最密集的一天，主程序从 3014 行膨胀到 3973 行（+959 行），完成了从 v0.7.0 到 v0.7.3 四个大版本的迭代。核心主题是：**让 AI 来帮助用户创作内容**。

#### 会话一：场景地点字段（v0.7.0，黄昏 19:45—19:50）

- **用户需求**：在场景设置中「时间」与「氛围」之间加入「地点」输入栏
- **修改范围**：
  - 4 个 scenes.json 文件（根 + 3 个 profile）新增 `"location"` 字段，手动为 26 个场景填写合理地点值
  - main.py 8 处修改：UI 布局 / `_load_scene_fields` / `_save_scene` / `_add_scene` / `_update_scene_label` / 兜底数据 / 新建模板 / `_get_scene_text`
- **设计决策**：地点字段地位与时间、氛围平等——可随时修改、保存、AI 切换，场景横幅显示格式改为 `时间 | 地点 — 氛围 ：描述`

#### 会话二：AI 场景/角色补全与生成（v0.7.0，黄昏 20:00—20:44）

这是今天最大的功能集群，涉及 **400+ 行新代码**：

**通用 JSON 清洗函数 `extract_json()`**：
```python
def extract_json(text: str) -> (dict|None, error_msg|None):
    # Step 1: 提取 markdown 代码块 (```json ... ```)
    # Step 2: 找最外层 { ... } 或 [ ... ]
    # Step 3: json.loads() 直接解析
    # Step 4: 修复尾部多余逗号后重试
```
- 设计考量：支持 4 层回退（代码块→花括号→直接解析→修复重试）
- 后续 v0.7.3 新增数组 `[...]$` 正则回退
- 后续 v0.7.3 新增 `import shutil` 按需内联（避免全局导入污染）

**场景 AI**：
- `_build_scene_ai_prompt(fill_mode, user_input, world_override)`：双模式提示词构建器
  - 补全模式：读取当前表单字段 → AI 补全/优化 → 立即填充 UI
  - 生成模式：弹窗输入一句话 → AI 生成完整场景 → 添加为新条目
- 场景 tab 新增 `[AI补全]` `[AI生成]` 两个按钮

**角色 AI**：
- `_build_char_ai_prompt(fill_mode, user_input, world_override)`：双模式提示词构建器
  - 补全模式：读取当前 7 个字段 → AI 补全/优化 → 立即填充 UI
  - 生成模式：弹窗输入一句话 → AI 生成完整角色（含 200-400 字 system_prompt）→ 创建新角色文件
- 角色 tab 新增 `[AI补全]` `[AI生成]` 两个按钮
- **icon 字段清理**：发现 icon 在整个 main.py 中只有 1 处引用（新建模板），属于废弃代码。一次清理了 19 个角色 JSON 文件中的 `"icon": ""` 字段

**AI 调用基础设施**：
- `_do_ai_call(prompt, on_done, show_loading=True)`：后台线程调 API，自动弹加载窗
- `_show_ai_raw_popup(title, raw_text)`：JSON 解析失败时弹窗显示原始返回
- 所有方法复用已有的 `extract_json()` + `_do_ai_call()` 基础设施

**踩坑记录**：
1. **角色删除按钮在保存前面**：`_build_chars_tab` 中 `_del_btn` 被先 `add_widget`，UI 顺序为 [删除][保存][添加]，修正为 [保存][添加][删除]
2. **弹窗标题与内容间大空档**：多次出现。根因是 `size_hint_y` 默认为 1 导致 content 拉伸填满 popup。**正确修复**（参考自定义模型弹窗）：在 content 末尾加 `Widget(size_hint_y=1)` 弹性空间推开内容，而非 `size_hint_y=None` 减小 popup
3. **`_do_ai_call` 的 show_loading 参数演进**：最初所有调用都弹加载窗，但 AI 一键创建剧本时有 10 路并行——每个线程都弹加载窗导致 UI 堆叠崩溃。后续 v0.7.2 新增 `show_loading=False` 参数

#### 会话三：世界观/大背景系统（v0.7.1，晚间 21:12—21:25）

**用户洞察**：现有的场景/角色 AI 只看到当前表单的字段，缺少跨所有 AI 操作的共享锚点。例如在星际飞船剧本中，AI 可能生成「爱去图书馆的文艺少女」——完全跑偏。

**解决方案**：在每个 Profile 的 `config.json` 中新增 `world.setting` 字段：
```json
{
  "world": {
    "setting": "近未来科幻背景。探索号是一艘深空探索飞船..."
  }
}
```

**实现细节**：
- 设置页新增世界观多行输入框 + 「AI推断」按钮
- 「AI推断」：读取当前所有场景描述 + 角色设定 → AI 生成 50-150 字世界观
- 新增 `[AI补全设置]` `[AI生成设置]` 两个按钮（标题/欢迎文字）
- `_get_world_context()`：统一读取入口，返回空字符串则 AI 退化为无锚点模式
- **场景 AI / 角色 AI 共 4 个 prompt builder 全部加 `【世界观】` 前置段落**
- 向后兼容：世界观为空时 AI 行为不变（从已填字段推断），不影响现有功能
- 3 个现有 Profile 的 `config.json` 预填合理默认世界观
- 新建剧本模板自动包含 `"world": {"setting": ""}`

**技术要点**：
- 世界观是「所有 AI 操作的共享锚点」——场景 AI、角色 AI、设置 AI 都经同一入口读取
- `world_override` 参数设计：UI 模式读 `_get_world_context()`，自动化模式直接传入世界观字符串

#### 会话四：AI 一键创建剧本（v0.7.2，晚间 21:25—21:48）

今天的皇冠功能。用户输入一句话 → AI 生成完整剧本（世界观 + 4 场景 + 4-5 角色 + 应用设置）。

**架构设计（两段式 + 并行复用）**：

```
调用1（规划）：用户一句话 → world + scenes_hints + char_hints + app + you_hint + turn_order
   ↓
调用2（10路并行）：每个 hint 送入已有的 prompt builder → 生成完整 JSON
   ├── app_brief     → _build_app_settings_prompt()  → API → 应用设置
   ├── scene_hint[0] → _build_scene_ai_prompt(False) → API → 完整场景
   ├── scene_hint[1] → ...（共4场景）
   ├── char_hint[0]  → _build_char_ai_prompt(False)  → API → 完整角色
   ├── char_hint[1]  → ...（共4角色）
   └── you_hint      → _build_char_ai_prompt(False)  → API → You 角色
```

**关键设计决策**：
1. **复用而非重写**：10 路并行全部调用已有的 `_build_*_ai_prompt(fill_mode=False, hint, world)`，共享相同的输出格式、字段说明、JSON 规范
2. **延缓分派**（v0.7.3）：最初所有请求同时发出，DeepSeek 直接 429 拒绝。改为 `Clock.schedule_once` 间隔 350ms 逐次派发，10 个任务在 ~3.5 秒内完成
3. **独立容错**：任何一路失败不影响其他——进度追踪用 `done_count` 计数器，全部完成后统一弹窗列出失败项
4. **写入前验证**：生成的 JSON 经过 `extract_json()` 清洗，无效字段用兜底值

**新增/修改方法**：
| 方法 | 作用 |
|---|---|
| `_build_app_settings_prompt(brief, world)` | 应用设置 AI 提示词（自动化专用） |
| `_ai_create_profile()` | 弹窗入口 |
| `_run_ai_create_profile(user_input)` | 流程编排（规划→并行→写入） |
| `_write_ai_created_profile(results, errors)` | 写目录、config.json、scenes.json、characters/ |
| 剧本管理行新增「AI创建」按钮（`size_hint_x=0.16`，调整其他按钮 & Spinner 宽度） |
| `_do_ai_call` 新增 `show_loading` 参数 |

**踩坑记录**：
- **双弹窗**：`_do_ai_call` 的加载窗堆在进度弹窗上面 → `show_loading=False` 解决
- **短暂黑屏**：10 个弹窗快速叠加/关闭导致渲染闪烁 → 同上根因
- **切换失败**：`_write_ai_created_profile` 只改了 `config` 没调用 `switch_profile()` → 改为完整切换流程
- **错误提示溢出**：失败消息含 long API error text → 改用简短名称（「场景2」） + TextInput 滚动换行

#### 会话五：深层 Bug 修复（v0.7.3，晚间 21:48—22:09）

用户引用了外部 AI 的代码审查建议，确认并修复了 5 个真实 bug：

| # | Bug | 严重度 | 发现方式 | 修复 |
|---|-----|--------|---------|------|
| 1 | **BubbleLabel 内存泄漏**：Widget 从树移除后 `Window.bind(on_resize=...)` 仍持有引用 | 🔴 严重 | 外部代码审查 | 新增 `_on_bubble_parent` 方法，`parent=None` 时 `Window.unbind` |
| 2 | **429 限流**：10 个 HTTP POST 瞬间并发 | 🔴 严重 | 外部代码审查 | `tasks` 队列 + `Clock.schedule_once` 350ms 间隔 |
| 3 | **文件夹命名不一致**：`_write_ai_created_profile` 用简单 `replace` 而非 `_make_safe_folder_name` | 🟡 中等 | 外部代码审查 | 替换为 `self._make_safe_folder_name(display_name)` |
| 4 | **turn_order 改名只改第一个**：`.index()` 只返回首次出现 | 🟡 中等 | 外部代码审查 | 改为列表推导 `[new_name if n==old else n for n in turn_order]` |
| 5 | **extract_json 不支持数组**：AI 偶尔返回根级 `[{...}]` | 🟢 低 | 外部代码审查 | 新增 `[...]$` 回退正则 |

#### 今日代码统计

| 指标 | 数值 |
|---|---|
| 新增代码行 | +959 行（3014→3973） |
| 新增方法 | 17 个（`extract_json` / `_get_world_context` / 8 个 AI 方法 / 4 个 prompt builder / `_write_ai_created_profile` / `_make_safe_folder_name` 等） |
| 新增 UI 按钮 | 10 个（场景×2 + 角色×2 + 设置×2 + 世界观×1 + 剧本×1 + 推断×1 + 加载弹窗×1） |
| 新增 JSON 字段 | 3 个（`location`, `world.setting`, `max_tokens` 调整） |
| 修改配置文件 | 7 个（4×scenes.json + 3×config.json） |
| Bug 修复 | 9 个（今日内发现并修复 4 个 + 外部审查 5 个） |
| 代码备份 | 3 个（`main_backup_before_ai_features` / `_before_world_feature` / `_before_ai_create_profile`） |

#### 今日设计经验

1. **AI 提示词要在通用性和具体性之间平衡**：第一版角色提示词包含「女生寝室」「15岁」「截瘫」等具体设定，被用户指出不适用于所有剧本 → 改为纯结构模板，AI 根据已填字段自行推断世界观

2. **一段 JSON 的隐患等于一段崩溃**：AI 返回的 system_prompt（200-400 字，含 `*`、`\n`、`"`）是 JSON 解析的头号杀手。三重防线：提示词强制要求单行转义 → `extract_json()` 四层清洗 → 解析失败弹窗手动复制

3. **复用好于重写**：v0.7.2 的一键创建剧本完全复用 v0.7.0 的单场景/单角色 prompt builder，10 路并行共享同一套经过验证的输出格式。如果每个分支单独写 prompt，维护成本指数级上升

4. **延缓比并发更可靠**：10 个 http 请求瞬间发出 → 全部 429 → 重试风暴。350ms 间隔 → 全部成功。在 LLM API 场景下，「慢而稳」优于「快而崩」

5. **外部代码审查是宝藏**：v0.7.3 的 5 个 bug 中有 4 个是已被忽视的真正隐患（内存泄漏、429 限流、命名不一致），在持续运行数小时后才会暴露。第三方视角比作者自审更敏锐

### 4.12 第九日：6月26日（周五）— UI 重构 & 对话存档系统

今日是项目诞生以来功能架构变化最大的一天，完成了设置页 UI 重构和完整的对话存档系统。主程序从约 4000 行膨胀到约 4650 行（+650 行），新增 15 个方法。

#### 会话一：设置页 Tab 重组（v0.7.5，上午 11:30—12:00）

**用户洞察**：设置 Tab 内容过于拥挤——剧本套件切换、应用标题、欢迎标题/文字、世界观、发言顺序、AI 补全/生成/推断按钮、保存设置、重置对话、导出日志等 10+ 个控件全塞在一个滚动页里，视觉重点不突出，逻辑分类混乱。

**解决方案**：新增「剧本」Tab，置于「场景」之前。

**重新编排**：
```
原来：[场景] [角色] [API] [设置]
改为：[剧本] [场景] [角色] [API] [设置]
```

**「剧本」Tab 内容**（从「设置」Tab 迁移）：
- 应用标题 / 欢迎标题 / 欢迎文字
- 世界观/大背景 + [AI推断] 按钮
- 发言顺序
- [AI补全设置] [AI生成设置]
- [保存] 按钮

**「设置」Tab 瘦身后**：
- 剧本套件切换（保持不变）
- [保存对话日志] [复制全部对话]

**设计细节**：
- Tab 按钮复用 RoundedButton，圆角 dp(4)
- 「剧本」Tab 默认作为打开设置时的初始页（替代原来的「场景」）
- 「设置」Tab 的保存和重置按钮移除（为后续功能留空间）
- 发言顺序输入框复用 v0.5.3 的 TextInput 修复方案：空初始化 + `Clock.schedule_once` 延迟注入

**改动量**：净增约 60 行（+110 行新 Tab 方法 / -50 行从「设置」移除）

#### 会话二：对话存档系统设计讨论（上午 11:50—12:20）

在动手实现之前，与用户进行了约 30 分钟的系统设计讨论。

**存储方案**：
```
profiles/<profile>/chats/
├── chat_20260626_113000.json
├── chat_20260625_200000.json
└── _autosave.json（自动存档）
```

- 文件名：`chat_YYYYMMDD_HHMMSS.json`（纯英文，可排序）
- 内容：`{title, created_at, updated_at, message_count, scene_idx, turn_idx, turn_count, history: [...]}`
- 自动存档文件以下划线前缀标识特殊用途

**标题生成策略**：
- 点击保存 → 弹窗「正在保存…AI 正在生成对话标题…」
- 后台线程调 AI 取最近 4-6 条对话生成 5-15 字标题
- 成功后弹窗更新「保存成功\n标题：宿舍夜话」
- AI 失败时备选：「{剧本名} - {场景时间} - {HH:MM}」（如「女生寝室 - 夜晚 - 23:15」）
- 每次保存新建文件（不覆盖），用户自行管理版本

**Android 自动存档**：
- `on_pause()` 触发 → 有新消息才写（对比 `_last_autosave_len`）
- 静默存档，不调 AI（Android 有 5 秒时间窗口限制）
- 标题用备选方案 + " - 自动存档"
- 用户手动保存后自动删除 `_autosave.json`

**启动恢复**：
- 检测 `_autosave.json` 存在且非空 → 弹窗「检测到上次未保存的对话\n是否恢复？」
- [恢复]：加载历史 + 重建 chat_view → 暂停状态
- [放弃]：删除 autosave → 正常欢迎页

**破坏性操作提醒**：
- 停止 / 切换剧本时，若 30 秒内未手动保存且有消息 → 三选一弹窗
- 空闲对话（0 条）→ 不提醒，直接执行

**设置 Tab UI 设计**：
```
┌──────────────────────────────┐
│  剧本套件 [下拉▼] [新][删][AI]│
│                              │
│  对话记录                      │
│  [宿舍夜话 06-26 (42条) ▼]    │
│  [读取] [删除]                │
│                              │
│  [保存当前对话] [复制全部对话]  │
└──────────────────────────────┘
```

#### 会话三：对话存档系统实现（v0.8.0，中午 12:20—12:35）

共新增 15 个 DormApp 方法，覆盖完整的 CRUD + 自动存档 + 生命周期：

**基础方法（7 个）**：
| 方法 | 作用 |
|------|------|
| `chats_dir` (property) | 当前剧本的 chats/ 路径 |
| `_ensure_chats_dir()` | 确保目录存在 |
| `_list_chat_files()` | 按时间倒序列出 chat_*.json |
| `_read_chat_meta(fp)` | 读取文件元信息（title, message_count, created_at） |
| `_save_chat_to_file(fp, title)` | 写完整对话 JSON |
| `_generate_chat_title(callback)` | 后台线程调 AI 生成标题 |
| `_fallback_chat_title()` | 备选标题「剧本名 - 场景 - 时间」 |

**核心操作（3 个）**：
| 方法 | 作用 |
|------|------|
| `save_current_chat(show_popup)` | 保存流程：快照→写临时标题→AI标题→回写→弹窗反馈 |
| `load_chat(filepath)` | 停止当前→恢复 history/turn→重建 chat_view |
| `delete_chat(filepath)` | 删文件 |

**自动存档（3 个）**：
| 方法 | 作用 |
|------|------|
| `_auto_save()` | on_pause 时静默写 _autosave.json |
| `_clear_autosave()` | 手动保存后删除 _autosave.json |
| `check_autosave_on_start()` | 启动时检测并弹窗恢复 |

**生命周期（1 个）**：
| 方法 | 作用 |
|------|------|
| `on_pause()` | Android 切后台 → `_auto_save()` → `return True` |

**SettingsPopup 新增方法（4 个）**：
| 方法 | 作用 |
|------|------|
| `_save_chat_from_settings()` | 保存按钮回调 |
| `_load_selected_chat()` | 读取按钮回调（含确认弹窗） |
| `_delete_selected_chat()` | 删除按钮回调（含确认弹窗） |
| `_refresh_chat_list()` | 刷新下拉列表（v0.8.1 新增） |

**修改的 UI 组件**：
- `build()`：启动后 0.8s 调用 `check_autosave_on_start()`
- `_build_app_tab()`：新增对话管理 UI（Spinner + 读取/删除/保存按钮）
- `_confirm_stop()`：有未保存对话时三选一（保存并停止 / 直接停止 / 取消）
- `_on_profile_selected()`：有未保存对话时新增 [保存并切换]
- 新建剧本（手动/AI 两处）：自动创建 `chats/` 目录
- `load_profile()`：自动创建 `chats/` 目录

#### 会话四：Bug 修复连环战（v0.8.1—v0.8.5，中午 12:33—13:05）

**v0.8.1：保存后列表不刷新**
- 问题：保存对话后，设置 Tab 的下拉列表不更新，需退出重进
- 修复：新增 `_refresh_chat_list()`，保存后 3.5 秒延迟刷新（等 AI 标题回写完成）

**v0.8.2：UI 清理**
- 删除主界面「重置」按钮（停止按钮已覆盖全部功能）
- 移除全部 Kivy 不支持的符号（emoji + 方框标记），改为纯文本

**v0.8.3：保存并停止→0 条记录 —— 核心 bug**
- 症状：点击 [保存并停止] 后生成的文件 `message_count = 0`
- 根因追踪：
  ```
  save_current_chat()
    ├─ _save_chat_to_file() → 读 self.history → ✅ 有数据
    ├─ _generate_chat_title() → 后台线程等 AI…
    ├─ _do_reset() → self.history.clear() 💀
    └─ _on_title_ready() → _save_chat_to_file() → 读 self.history → 空！
  ```
- 修复：保存时拍快照 `saved_data = {history: list(self.history), ...}`，回调时用快照而非活引用
- 影响范围：所有「保存后紧接操作」的路径（停止/切换剧本）

**v0.8.4：消息类型兼容性验证**
- 用户问：导演模式/用户模式消息能否正确保存读取？
- 完整链路追踪验证：三种消息类型（导演 `type:"director"`、用户 `name:"You"` 默认 `type:"normal"`、角色 `name:"Kate"` 默认 `type:"normal"`）均通过 `ChatMessageRow` 的 `is_right` 逻辑正确对齐和着色

**v0.8.5：AI 标题生成修复 —— 三重改进**
- **问题一（核心）**：`max_tokens=50` 太小。DeepSeek R1 等模型输出前会加 `<think>...</think>` 思考过程或 "好的，这是生成的JSON：" 等前言，50 个 token 瞬间耗尽 → 输出截断 → JSON 残缺 → 解析失败
- **问题二**：手写的基于正则的 JSON 提取逻辑脆弱，不处理 `<think>` 标签、代码块等多种变形
- **问题三**：`except Exception: pass` 静默吞噬错误，无法诊断
- **修复**：
  1. `max_tokens: 50 → 300`
  2. 替换为已有的健壮全局函数 `extract_json()`（处理 `<think>` 标签 + markdown 代码块剥离 + 尾逗号修复 + json5 回退等 5 步清洗）
  3. 添加 `print(f"[AI标题生成] ...")` 错误日志

#### 今日技术要点

1. **快照模式防竞态**：异步回调中不要读可变状态（`self.history`），应在操作发起时拍快照（`list(self.history)`）存入闭包。这是 JavaScript Promise 的常见模式，在 Python 异步回调中同样适用

2. **LLM 的 token 预算陷阱**：有推理过程的模型（DeepSeek R1）会在输出前消耗 token 做内部思考。给小任务的 `max_tokens` 必须留足余量——标题生成 50 不够，300 足矣

3. **复用健壮的全局函数**：文件顶部已有经过 8 次迭代打磨的 `extract_json()`，处理了 `<think>`、markdown 代码块、尾部逗号等多种情况。在写新功能时先检查是否有现成的工具，比重新实现更可靠

4. **Android 生命周期不等于桌面行为**：`on_pause()` 在 Windows 上不会触发，只在 Android 切后台时调用。桌面端测试自动存档需要区分平台行为

#### 会话五：Spinner 下拉文字溢出修复（v0.8.6，下午 13:23—13:27）

**问题**：Android 上两个 Spinner（剧本套件 + 对话记录）的下拉选项文字一长就超出框边界，原因是 Kivy Spinner 默认的 `option_cls` 是原生 Button，无 `text_size` 约束。

**解决方案**：新增 `FitSpinnerOption(Button)` 自定义类（16 行）：

```python
class FitSpinnerOption(Button):
    """下拉选项：文本过长时自动换行，自适应高度"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.halign = 'left'
        self.valign = 'middle'
        self.font_size = dp(11)
        self.padding = [dp(10), dp(8)]
        self.size_hint_y = None
        self.bind(parent=self._on_parent)

    def _on_parent(self, widget, parent):
        """加入下拉框后，绑定宽度以触发自动换行"""
        if parent is not None:
            parent.bind(width=self._update_text_size)

    def _update_text_size(self, dropdown, width):
        self.text_size = (max(0, width - dp(20)), None)
        self.height = self.texture_size[1] + dp(16)
```

**关键设计**：
- `on_parent` → 检测选项被加入 DropDown 的时机 → 绑定父容器 `width`
- `_update_text_size` → 下拉框宽度变化时自动更新 `text_size` → Kivy Label 引擎自动换行
- `height` 根据 `texture_size` 自适应 → 多行文本不被裁剪

**接入范围**：
- 剧本套件 Spinner → `option_cls=FitSpinnerOption`
- 对话记录 Spinner → `option_cls=FitSpinnerOption`（两处：`_build_app_tab` 初始 + `_refresh_chat_list` 刷新）

#### 会话六：v0.8.7 保存系统大修 & 设置页 UX 优化（晚间 19:00—21:00）

这是项目诞生以来 UX 打磨最密集的一个晚间，完成了 8 个功能改进和 3 个 Bug 修复。

**1. 设置自动暂停改为即时生效**
- 问题：`_open_settings` 走队列发送 `("pause", None)`，有 0.1~3 秒延迟
- 修复：`_open_settings` 和 `SettingsPopup._on_close` 直接设置 `self.paused` + 即时更新 UI，零延迟

**2. 暂停时自动存档 + 覆盖逻辑**
- `_auto_save()` 去掉了长度检查和"自动存档"后缀，每次暂停必定保存到 `_autosave.json`
- `_open_settings`（打开设置暂停）和 `_handle_cmd("pause")`（暂停按钮）都触发自动存档
- 用户继续聊天 → 再次暂停 → 覆盖 `_autosave.json`
- 显式保存（带 AI 标题）→ 清除 `_autosave.json`

**3. 加载对话后覆盖原文件**
- 新增 `_loaded_chat_path` 属性跟踪
- `load_chat()` 设置路径 → `save_current_chat()` 检测到已加载路径 → 覆盖原文件而非另存
- `_do_reset()` 清除路径

**4. 暂停时底部显示「保存」按钮**
- 底部控制栏新增紫色 `[保存]` 按钮（`ColoredButton`，`#ab47bc`）
- 暂停时显示（`_toggle_save_btn(True)`），运行时/停止时隐藏（`_toggle_save_btn(False)`）
- 点击 → `save_current_chat(show_popup=True)` → AI 生成标题 + 弹窗确认

**5. 读取对话/切换剧本/停止时统一的「未保存」提醒**
- 三处破坏性操作使用相同的 `has_unsaved` 检测 + 三选一弹窗
- 读取对话：`[取消] [保存并读取] [读取]`
- 切换剧本：`[取消] [保存并切换] [确定切换]`
- 停止对话：`[取消] [保存并停止] [直接停止]`
- 所有 `show_popup` 统一为 `True`（之前切换和读取用的是 `False`）

**6. PC 端关窗也能触发恢复（`on_stop`）**
- 新增 `on_stop()` 方法 → 关闭时调用 `_auto_save()`
- 之前 `on_pause` 只在 Android 切后台触发，PC 关窗无任何存档
- 如果 history 为空（已停止），不产生垃圾文件

**7. 对话记录重命名功能**
- 设置 Tab 对话记录行新增 `[重命名]` 按钮（`#42a5f5`）
- 弹窗预填原标题，修改 → 确认 → 更新文件 `title` + `updated_at` → 刷新列表

**8. 剧本管理重新排版 + 重命名 + 切换按钮**
- 剧本选择不再自动弹窗 → 新增独立的 `[切换]` `[重命名]` 按钮
- 布局从一行改为两行：
  - 第一行：Spinner（选剧本）+ `[切换]` + `[重命名]`
  - 第二行：`[新建]` `[删除]` `[AI创建]`
- 重命名剧本：修改 `config.json` 的 `display_name`，同步更新标题栏
- 删除剧本功能不受影响

**Bug 修复：**
- `_save_app_settings` 保存时覆盖 `display_name` → 改为保留旧值
- `_save_app_settings` 重复 save_json 和 title 赋值 → 删除重复代码
- `_reset_chat` 意外被删除 → 恢复

**9. Spinner 全套升级（文字截断 + 排序 + 滚动）**
- 新增 `FitSpinner(Spinner)`：直接在 `self` 上设 `shorten=True` + `text_size` 动态适配，长文本自动 `...` 省略号
- 新增 `ScrollDropdown(DropDown)`：`max_height=dp(300)`，选项多时自动滚动
- 全部 6 个 Spinner 升级（场景/角色/API模型/剧本/对话记录/速度）
- 剧本排序从字母序 → `config.json` 修改时间倒序（新的在前）
- 对话排序从 `st_mtime` → 文件名时间戳排序（兼容安卓 `st_mtime` 不准）
- 对话标题显示恢复 `[:20]`（有了 FitSpinner 的 shorten，不再硬截断）

**10. 代码模块化分析**
- 主程序 ~5145 行，提出 4 文件拆分方案（`utils.py` / `widgets.py` / `settings_popup.py` / `dorm_app.py` + `main.py` 入口）
- 确认无循环依赖，待用户批准后执行

---


## 五、技术难点与解决方案汇总

### 5.1 Android 交叉编译（共 16 项问题）

| # | 类别 | 问题 | 解决方案 |
|---|------|------|----------|
| 1 | 环境 | `libtinfo5` 找不到 | 改用 `libncurses-dev` |
| 2 | 环境 | pip 拒绝系统级安装 | 创建独立 venv |
| 3 | 环境 | Kivy 编译失败 | 安装 SDL2/GL 系统库 |
| 4 | 网络 | GitHub 超时/SSL | ghproxy 镜像全局替换 |
| 5 | 网络 | v2ray WSL 不通 | 重启 v2rayN + ghproxy |
| 6 | 网络 | 11 个源码包逐个卡 | Windows 端代理预下载 + `.mark-` 标记 |
| 7 | 网络 | googlesource 子模块 | 删除 `.gitmodules` 引用 |
| 8 | 编译 | NDK + glibc 冲突 | 卸载宿主 SDL2 开发包 |
| 9 | 代码 | `BASE_DIR` 未定义闪退 | 字体注册移到变量定义后 |
| 10 | 代码 | JSON 文件被清空 | 改 PowerShell 为 Python 清理 |
| 11 | 代码 | `color=` 参数重复 | 手动逐一删除 |
| 12 | 字体 | 中文全方块 | 注册系统 CJK 字体为 "Roboto" |
| 13 | 字体 | 切标签页字体消失 | `_switch_tab` 后重新注入 |
| 14 | 字体 | Emoji 方块 | 清理所有配置 emoji |
| 15 | UI | 场景横幅太小 | 自适应高度 |
| 16 | UI | 设置页空档/输入栏颜色 | `size_hint_y=None` + 深色背景 |

### 5.2 KivyMD 2.0 依赖链（共 5 项新增依赖）

| 依赖 | 作用 | 发现方式 |
|------|------|----------|
| `materialyoucolor>=2.0.7` | Material You 动态取色 | KivyMD 2.0 的直接依赖 |
| `materialshapes>=0.3` | Material 形状组件 | KivyMD 2.0 的直接依赖 |
| `asynckivy>=0.6` | 异步 Kivy 事件 | KivyMD 2.0 的直接依赖 |
| `asyncgui` | asynckivy 的依赖 | Crash log 追踪 → ModuleNotFoundError |
| `pycairo` | materialshapes 的依赖（系统级 cairo 绑定） | 依赖树分析 + p4a recipe 确认 |

### 5.3 版本回退决策

项目中发生了**两次关键回退**，每次都挽救了项目进度：

#### 回退一：v0.5.1 → v0.3.10（6月20日）

- **原因**：v0.5.1 新增 572 行代码（线程安全重构、幽灵消息修复、竞态修复等），在桌面端正常但在 Android 端闪退
- **策略**：回到已验证工作的 v0.3.10，仅施加最小必要修复（字体名、关键 bug fix）
- **教训**：移动端与桌面端的兼容性差异比预期更大；大规模功能改动应在每个平台独立验证后再合并

#### 回退二：KivyMD 2.0 → 纯 Kivy 原生 Button（6月22日）

- **背景**：之前为美化 UI 引入了 KivyMD 2.0.1.dev0，但在 Android 上经历了：
  1. KivyMD 1.2.0 与 2.0 版本共存冲突
  2. 缺失依赖 `materialyoucolor`
  3. 缺失依赖 `asyncgui`（asynckivy 的传递依赖）
  4. 缺失依赖 `pycairo`（materialshapes 的传递依赖）
  5. 补全后仍可能有更多隐藏依赖
- **决策依据**：
  - 每解决一个依赖问题，又暴露下一个依赖问题
  - KivyMD 2.0 引入 5 个新包，每个都可能有自己的 Android 兼容性问题
  - 纯 Kivy 的 `Button` 控件在功能上完全够用，只是少了一些 Material Design 动画效果
  - APK 体积从 ~58MB 暴降到 ~25MB 以下
- **最终决定**：彻底放弃 KivyMD，回退到纯 Kivy + 原生 `kivy.uix.button.Button`
- **教训**：
  - UI 框架升级的收益需要与风险权衡。KivyMD 2.0 在桌面端没有问题，但 Android 交叉编译的依赖链复杂度被低估了
  - 「简单即稳定」——原生 Button 虽然缺少悬停动画 / Material You 取色，但零依赖、零兼容性问题
  - 在跨平台项目中，最小化第三方依赖数量是降低维护成本的有效策略

---

## 六、项目数据统计

### 6.1 版本迭代

| 指标 | 数值 |
|------|------|
| 总版本数 | 40+ (v1.0 → v0.8.7) |
| 单日最高迭代 | 10 个版本（6月17日）、4 个大版本（6月24日 v0.7.0→v0.7.3）、6 个子版本（6月26日 v0.7.5→v0.8.5）+ 1 个大版本（6月26日 v0.8.6 动态发言三次迭代）+ 1 个大版本（6月26日 v0.8.7 保存系统大修 + UX优化） |
| 单日最大代码增长 | +959 行（6月24日）、+650 行（6月26日） |
| 版本回退次数 | 2 次（v0.5.1 → v0.3.10、KivyMD 2.0 → 纯 Kivy 原生 Button） |
| 并行开发分支 | 3 个（dorm-life / dorm-life-clean / dorm-clean） |
| 最新版本 | v0.9.1（拖拽排序发言顺序 + 角色池管理） |

### 6.2 技术指标

| 指标 | 数值 |
|------|------|
| 总开发天数 | 12 天 |
| 主程序当前行数 | 2024 行（main.py 仅 DormApp） |
| 活跃 session 数 | 约 20 个主 session |
| 踩坑总数（Android 编译） | 16 项 |
| 依赖项分析（KivyMD 2.0） | 5 项新增 |
| 新增方法（今日 v0.8.x） | 15 个（DormApp）+ 4 个（SettingsPopup） |
| 调试方法 | crash log 追踪 + 语法验证 + 文件对比 + dry-run 依赖分析 |
| 桌面版最终大小 | 33.6 MB（含完整 Python 运行时） |

### 6.3 角色阵容演变

| 阶段 | 阵容 | 用途 |
|------|------|------|
| 初始 | 莉莉/ 简/ 吉尔/ 凯特 | v1.0—v0.5.1 Android 版 |
| 最终 | 小雪 / 小梅 / 小林 / 小瑞 | 桌面版 + Android 版（配置已统一） |
| 备份 | 莉莉/简/吉尔/凯特 | `characters_backup_v0.5.1/` |

---

## 七、动态发言顺序系统设计（v0.8.6）

### 7.1 问题背景

ChatRoom 原有的发言顺序只有两种模式：
- **轮流**（round-robin）：`effective_order[turn_idx % len]`，无视对话内容
- **随机**（random）：`random.choice(effective_order)`，完全无视上下文

两种模式的核心缺陷相同——**不感知剧情**。即使上一句 Jill 直接问 Jane 问题，下一秒也可能轮到 Kate，她必须假装没听见去接话。

### 7.2 三次架构迭代

#### 迭代一：独立 AI 导演（已废弃）

方案：每轮额外调一次 API，让一个"隐形导演"判断下一个发言人。

```
_run_loop() → _pick_next_speaker() → 导演 API（独立 HTTP 请求）
                                        → extract_json(raw)
                                        → 返回 {"next": "Jane"}
```

**失败原因**：
| 问题 | 详情 |
|------|------|
| JSON 解析失败率 ~50% | 模型输出格式不稳定（`<think>` 标签、多余文字、空返回） |
| 缓存命中率 ~0% | 每轮上下文不同，API 永远 fresh call |
| 成本翻倍 | 每轮多一次 API 调用 |
| 位置偏差 | prompt 里角色列表 = turn_order，LLM 顺列表选 |
| 纯名字输出更差 | 去掉 JSON 后失败率升至 ~100%（`<think>` 标签未处理） |

**结论**：成本高 + 不可靠 → 废弃。

#### 迭代二：纯规则引擎（保留为兜底）

方案：不依赖 API，纯 Python 计算。四条规则的加权随机：

```
A. 沉默惩罚：w += min(silence_turns, 10) × 0.25
B. 直接点名：上一句出现角色英文名 → w × 3.0
C. 反自说自话：刚说过话的人 → w × 0.1
D. [NEXT] 提示：上一轮角色主动点名 → w × 5.0

加权随机 → 选人
```

**优点**：零成本、零延迟、永不失败。**缺点**：不理解语义——"这个话题更适合谁的性格"这类判断无法实现。

#### 迭代三：角色嵌入点名 + 规则兜底（最终方案）

核心思路：**把导演职责还给角色自己**——"你刚说完，你最清楚该谁接"。

```
┌─ _build_prompt("Jill")
│   └─ if mode == "dynamic": 追加:
│       "On the very last line of your reply ONLY, add [NEXT:Name]
│        to suggest who should speak next. Pick from: Jane, Kate, Lily.
│        Do NOT include [NEXT] inside your dialogue or actions."
│
├─ LLM 返回: "对话正文...\n*开心地笑了*\n[NEXT:Kate]"
│
├─ _handle_cmd("msg")
│   ├─ re.search(r'\\[NEXT:([^\\]]+)\\]', text) → "Kate"
│   ├─ val["text"] = re.sub(r'\\s*\\[NEXT:[^\\]]+\\]\\s*$', '', text)
│   │   └─ UI 永远看不到 [NEXT:Kate]
│   ├─ self._suggested_next = "Kate"
│   └─ self.history.append(val)  ← 干净版
│
├─ _pick_next_speaker_rules()
│   ├─ Kate: w ×5.0（hint 权重）→ ~65%
│   ├─ Lily: w ×3.0（被点名）   → ~20%
│   └─ 加权随机 → 大概率 Kate，小概率其他人
└─ 若 [NEXT] 提取失败 → _suggested_next=None → 规则 B/C/D 兜底
```

### 7.3 关键设计细节

#### 提示词注入（仅动态模式）

`_build_next_hint(current_speaker)` 仅在 `self.mode == "dynamic"` 时返回非空字符串，拼接到 `_build_prompt` 末尾。轮流/随机模式下 `_build_prompt` 完全不变。

可用名单排除说话者自己（`others = [n for n in effective_order if n != current_speaker]`），避免角色建议"下一个还是我"。

#### [NEXT] 剥离

- 正则用 `$` 锚定行尾，只砍最后一行
- 先提取再剥离再存 history，确保 UI/存档/后续 AI 上下文中都不含此标记
- 提取失败 → `_suggested_next = None`，规则 B/D 完全不受影响

#### 沉默追踪（_char_last_turn）

| 时机 | 操作 |
|------|------|
| 角色发言 | `_char_last_turn[name] = turn_count` |
| 切换剧本 | `_do_reset()` → `.clear()` |
| 加载存档 | 遍历 history 重建 |
| 硬兜底 | silence >= 15 → 直接返回，跳过规则引擎 |

#### 权重设计

| 因子 | 效果 | 设计意图 |
|------|------|----------|
| 沉默 +0.25×turn | 10轮沉默=+2.5 | 渐进式公平，不是突然插队 |
| 点名 ×3.0 | 被 @ 的人大概率回应 | 模拟真实对话 |
| 自罚 ×0.1 | 刚说过话几乎不可能再说 | 禁止独白 |
| hint ×5.0 | ~65% 命中率 | 角色判断力优先，但保留意外 |
| 硬兜底 15轮 | 100% 插入 | 防止角色被永远遗忘 |

### 7.4 成本对比

| | 独立导演 | 角色嵌入+规则 |
|------|----------|--------------|
| 每轮额外 API | 1 次 | 0 |
| 月成本 | ×2 | 不变 |
| 延迟 | +10s（超时） | ~0.01ms（纯 Python） |
| 成功率 | ~50% | ~100%（hint失败→规则兜底） |
| 动态感 | 有（但被失败率掩盖） | 有（hint命中≈65%+规则变化） |

### 7.5 教训

1. **不要为简单判断调用 AI**：选下一个发言人本质上是一个加权多选问题，规则引擎比 LLM 更可靠、更便宜。
2. **角色嵌入比独立导演更自然**：角色知道自己在跟谁说话，让 ta 点名比外部观察者判断更准确。
3. **[NEXT] 作为软提示而非硬约束**：×5.0 而非 100%，保留戏剧性的意外插话空间。
4. **先看日志再下结论**：调试日志暴露了"hint 成功但导演仍然选别人"其实是加权随机的设计行为，而非 bug。

---

## 七、经验总结与最佳实践

### 7.1 技术经验

1. **跨平台 GUI 框架选择**：tkinter 适合快速桌面原型和分发（零依赖），Kivy 适合需要移动端支持的项目，两者可共享业务逻辑层。

2. **Android 交叉编译的网络挑战**：国内环境下，Buildozer + p4a 的下载环节是最大瓶颈。可靠方案包括：ghproxy 镜像、Windows 端代理预下载、清华 PyPI 镜像、软链接复用已下载资源。

3. **字体处理**：在 Kivy 中，替换默认字体（`LabelBase.register(name="Roboto", ...)`）远比逐控件设置 `font_name` 高效，可以覆盖弹窗、下拉菜单等动态创建的控件。

4. **移动端兼容性验证**：大型功能改动应在桌面端和移动端分别验证后再合并到主线。

### 7.2 工程经验

5. **版本回退是正常操作**：v0.5.1 → v0.3.10 和 KivyMD 2.0 → 纯 Kivy 的两次回退虽然痛苦，但避免了在错误方向上继续投入。先跑起来再迭代。

6. **缩短反馈循环**：能在 Windows 上 `pip install kivy && python main.py` 预览的，就不要每次编译 APK（耗时 15-30 分钟）。

7. **依赖管理要彻底，更要克制**：KivyMD 从 1.2 升级到 2.0 时引入 6 层依赖链（materialyoucolor → materialshapes → asynckivy → asyncgui → pycairo），每个都可能在 Android 上有兼容性问题。最终选择放弃 KivyMD、用原生 Button 替代，APK 体积反降 50%+。**最简单的方案往往是最稳定的方案。**

8. **自动化的边界**：某些操作（如 v2ray 重启、NDK 断点续传）超出了 AI 助手的自动化能力，明确交给用户执行比强求自动化更高效。

### 7.3 协作经验

9. **人机协作模式**：用户定义需求和高层决策（角色阵容、版本回退），AI 负责执行（代码修改、文件操作、诊断分析）。在关键节点（如编译指令），用户主动要求"给我指令，让我自己来"，这是一种务实的分工。

10. **「说一句」类功能要谨慎设计**：手动单步发言涉及 `running` 状态和消息队列的复杂交互——（1）消息消费检查 `self.running` 但手动发言在暂停态，消息被丢弃；（2）防抖锁 `_is_stepping` 忘记在 `finally` 复位。简单删除比修复更安全。

11. **Kivy TextInput 零宽度 Bug 是经典陷阱**：`clear_widgets()` + 立即 `add_widget` + 赋长文本 → `scroll_x` 在宽度=0 时错位锁死。四步修复：空初始化、对称 padding、延迟注入、`scroll_x=0`。仅靠重新赋值 `text` 不够——需主动复位视口偏移。

12. **Canvas RoundedRectangle 是轻量聊天气泡的最佳方案**：纯 GPU 渲染圆角背景，零纹理图片，`texture_size` 自适应宽高。比 KivyMD 的九宫格纹理或图片背景更省内存、更丝滑。

13. **多剧本架构的关键是数据驱动**：将硬编码设定（如"室友"）移到配置文件（`prompt_hint` 字段），代码只负责读取和拼装。一个字段的改变就能让同一个 `You` 角色在不同剧本中拥有完全不同的叙事身份。

14. **批量重构时善用 Python 脚本**：v0.6.5 涉及 400+ 行代码的跨文件改动（全局变量→App 属性、SettingsPopup 全适配），手工逐行编辑易出错。用 Python 脚本做文本替换 + 语法校验的组合拳，效率高且安全。

15. **文件夹名用英文，显示名用中文**：Android 文件系统对中文路径兼容性不确定，通过 `display_name` 字段在 UI 层映射中文，底层始终使用安全的英文文件夹名（`dorm_girls`/`profile_md5hash`）。

16. **圆角按钮的 Canvas 替换要同步修改所有动态改色代码**：将 `background_color` 改为 `set_bg_color()` 后，必须全量搜索项目中所有直接赋值 `background_color` 的地方，否则部分按钮的颜色切换会失效。

17. **快照模式防竞态**：异步回调中不要读可变状态（`self.history`），应在操作发起时拍快照（`list(self.history)`）存入闭包。保存→AI标题→回写 的三段式流程中，若回写时再读 `self.history`，可能在竞态窗口内被其他操作（reset/switch）清空。

18. **LLM 的 token 预算陷阱**：有推理过程的模型（如 DeepSeek R1 的 `<think>` 标签）会在输出正文前消耗 token 做内部思考。给小任务设 `max_tokens` 必须留足余量——标题生成 50 不够，300 足矣。

19. **复用健壮的全局函数优于重写**：文件顶部已有经过多轮迭代打磨的 `extract_json()`，新功能应先检查是否有现成工具，比从头实现更可靠。

20. **Android 生命周期与桌面行为的差异**：`on_pause()` 在 Windows 上不触发（仅在 Android 切后台时调用），桌面端测试自动存档需要用其他方式模拟。设计跨平台功能时要标注平台差异。

---

## 八、当前状态与待办事项

### 8.1 已完成 ✅

- [x] Windows 桌面版：v0.5.1 完整功能，PyInstaller 打包可分发的 .exe
- [x] 配置文件外部化与统一（桌面版/移动版一致）
- [x] 角色阵容切换（正常室友/小雪阵容）
- [x] 导演模式 + 用户模式双开关
- [x] API key 清空，首次配置向导
- [x] Android 编译问题诊断报告（16 项）
- [x] KivyMD 2.0 完整依赖树分析（6 层依赖链）
- [x] 放弃 KivyMD 2.0，回退纯 Kivy（APK 体积从 ~58MB → ~25MB）
- [x] 清华 PyPI 镜像配置
- [x] buildozer.spec 瘦身（删除 7 个无用包 + 排除无关目录/备份文件）
- [x] v0.5.3 聊天气泡系统（Canvas RoundedRectangle + 弹簧对齐）
- [x] v0.5.3 API 模型下拉选择 + 持久化缓存
- [x] v0.5.3 Markdown 转 Kivy Markup（`**粗体**` / `*动作*`）
- [x] v0.5.3 TextInput 零宽度渲染 Bug 彻底修复（6 个输入框）
- [x] v0.5.3 发言顺序 You 可视化 + 保存过滤
- [x] v0.5.3 工具栏三按钮宽高字体统一
- [x] v0.5.3 删除「说一句」功能（含死锁 bug 一并消除）
- [x] **v0.6.5 多剧本/多配置组系统（profiles/ 目录隔离）**
- [x] **v0.6.5 剧本切换 + 新建 + 删除（中文名→英文文件夹名）**
- [x] **v0.6.5 You 角色硬编码→数据驱动 prompt_hint**
- [x] **v0.6.5 全局变量→App 动态属性（SCENES/CHARACTERS 等全部迁移）**
- [x] **v0.6.5 首次启动自动迁移旧数据**
- [x] **v0.6.5 5 个隐藏 Bug 修复（Android 路径/气泡宽度/标题引用/僵尸线程/发言校验）**
- [x] **v0.6.5 Emoji 全面清理（Kivy 不支持）**
- [x] **v0.6.5 全部按钮圆角化（RoundedButton + ColoredButton 按下变深）**
- [x] **v0.6.5 Android 打包适配（buildozer.spec + init 时机修正）**
- [x] **v0.6.5 回底按钮等高 / 设置按钮圆角 / 删除剧本功能**
- [x] **v0.7.0 场景地点字段（time→location→mood 完整信息链）**
- [x] **v0.7.0 AI 场景/角色补全 + 生成（`extract_json` + `_do_ai_call` 基础设施）**
- [x] **v0.7.0 角色管理按钮顺序修正 + 弹窗空档修复**
- [x] **v0.7.0 icon 字段全量清理（19 个 JSON 文件）**
- [x] **v0.7.1 世界观/大背景系统（`world.setting` + AI 推断/补全/生成设置）**
- [x] **v0.7.1 场景/角色 AI 提示词全部接入世界观锚点**
- [x] **v0.7.2 AI 一键创建完整剧本（规划→10路延缓并行→写入）**
- [x] **v0.7.2 错误提示简化 + TextInput 可滚动换行**
- [x] **v0.7.3 BubbleLabel Window.unbind 内存泄漏修复**
- [x] **v0.7.3 API 429 限流防护（350ms 延缓分派）**
- [x] **v0.7.3 文件夹命名统一 `_make_safe_folder_name()`**
- [x] **v0.7.3 turn_order 改名全量替换（列表推导）**
- [x] **v0.7.3 extract_json 数组回退正则**
- [x] **v0.7.5 设置页 Tab 重组：新增「剧本」Tab（世界观集中管理）**
- [x] **v0.7.5 发言顺序输入框显示修复（复用 v0.5.3 方案）**
- [x] **v0.8.0 对话存档系统（保存/读取/删除 + AI标题 + 设置Tab UI）**
- [x] **v0.8.0 Android 自动存档（on_pause）+ 启动恢复**
- [x] **v0.8.0 破坏性操作保存提醒（停止/切换剧本）**
- [x] **v0.8.0 新建剧本自动创建 chats/ 目录**
- [x] **v0.8.1 保存后对话列表自动刷新**
- [x] **v0.8.2 删除多余重置按钮 + 移除 Kivy 不支持符号**
- [x] **v0.8.3 保存并停止→0条记录 Bug（快照修复）**
- [x] **v0.8.4 导演/用户模式消息保存读取兼容性验证**
- [x] **v0.8.5 AI 标题生成修复（max_tokens 50→300 + extract_json + 错误日志）**
- [x] **v0.8.6 Spinner 下拉文字溢出修复（FitSpinnerOption 自动换行类）**
- [x] **v0.8.7 保存系统大修（暂停自动存档/覆盖 + 加载后覆盖原文件 + 保存按钮）**
- [x] **v0.8.7 设置页 UX 优化（统一未保存提醒/重命名/剧本管理重排版）**
- [x] **v0.8.7 Spinner 全套升级（FitSpinner + ScrollDropdown + 排序修复）**
- [x] **v0.8.7 PC 关窗自动存档（on_stop）**
- [x] **v0.8.7 3 个 Bug 修复（display_name 覆盖/重复保存/_reset_chat 恢复）**
- [x] v0.8.7 代码模块化分析（4 文件拆分方案，待执行）
- [x] v0.9.0 ★ 代码模块化拆分完成（6步展开为 8个独立模块文件）
- [x] v0.9.0 main.py 瘦身 61%（5185→2024行）
- [x] v0.9.0 Bug Fix: 动态模式用户权重修复（0.6× + 12轮硬沉默）
- [x] v0.9.0 Bug Fix: AI创建剧本后对话残留（switch_profile顺序）
- [x] v0.9.0 Bug Fix: 删除/重命名弹窗下拉框回弹
- [x] v0.9.0 Bug Fix: 重命名弹窗大空档
- [x] 本过程报告（更新至 v0.9.1）
- [x] **v0.9.1 发言顺序拖拽排序 + 角色池管理（活跃/待命双区）**

### 8.2 进行中 🔧

- 暂无

### 8.3 已知 Bug 与设计决策 ℹ️

- **设置弹窗关闭后不自动恢复对话（Bug #2）**：`_handle_cmd` 中未定义 `"resume"` 命令字，但**此为刻意设计**——让用户手动点击"继续"，避免意外恢复
- **文件写入非原子级（Bug #4）**：`json.dump` 使用 `"w"` 模式直接打开，杀进程/断电可能导致 0 字节文件。建议未来改为临时文件 + `os.replace` 原子写入
- **角色保存后 Spinner 重置（Bug #3）**：`_refresh_char_spinner` 强行重置为 `display_names[0]`，保存后跳回第一个角色。可传入 `current_text` 参数修正
- 旧版 KivyMD 代码已备份为 `main_backup_v0.5.2_kivymd.py`
- v0.6.5 重构后根目录的旧 `scenes.json` 和 `characters/` 仍有备份保留（可选删除）

### 8.4 未来可能方向 💡

- [ ] 角色市场 / 分享机制（导入导出角色 JSON + 剧本打包分享）
- [ ] iOS 移植（Kivy 理论上支持，但需 macOS + Xcode）
- [ ] 多语言支持
- [ ] 云端部署（WebSocket 版本复活？）
- [ ] 剧本模板库（社区贡献各种设定：武侠/科幻/校园/奇幻...）
- [ ] 桌面版同步升级到 v0.7.5 多剧本 + AI 辅助架构
- [ ] AI 一键创建剧本的 you_hint 后处理优化（确保 You 角色身份与剧本主题一致）

---


---

## 十、v0.9.0：代码模块化拆分 & Bug 修复（6月26日 晚间 22:00—23:36）

### 10.1 背景

v0.8.7 结束时，main.py 已膨胀至 5185 行。所有代码——全局配置、工具函数、6 个自定义控件、聊天 UI、2650 行的设置弹窗、2020 行的 DormApp——全塞在一个文件里。Git 合并极易冲突，改一个 Button 样式要翻 3000 行定位，替换 ScrollView 为 RecycleView 更是在巨无霸文件里牵一发动全身。

按照"高内聚、低耦合"原则，执行了 6 步渐进式拆分，每步完成后运行测试确认无报错。

### 10.2 拆分方案

| 步骤 | 风险 | 新建文件 | 行数 | 内容 |
|------|------|----------|------|------|
| Step 1 | 🟢 低 | `config.py` + `utils.py` | 47 + 86 | 全局配置 / 工具函数 |
| Step 2 | 🟢 低 | `ui/base_widgets.py` | 162 | 6 个基础控件 |
| Step 3 | 🟡 中 | `ui/chat_widgets.py` | 199 | 聊天 UI |
| Step 4 | 🔴 高 | `ui/settings_popup.py` | 2641 | 设置弹窗（152 处 self.app 跨文件调用） |
| Step 5 | 🟡 中 | `api_service.py` | 190 | LLM HTTP 请求封装 |
| Step 6 | 🟢 低 | — | — | 清理 main.py 入口 + 去冗余 import |

### 10.3 拆分后结构

```
dorm-clean/
├── main.py                  ← 2024 行 (DormApp + 入口，-61%)
├── config.py                ← 47 行 (BASE_DIR/API_KEY/MODEL…)
├── utils.py                 ← 86 行 (load_json/save_json/hex_to_rgba/extract_json)
├── api_service.py           ← 190 行 (call_chat_completion/fetch_models/APIError)
├── ui/
│   ├── __init__.py
│   ├── base_widgets.py      ← 162 行 (StatusDot/RoundedButton/ColoredButton/FitSpinner)
│   ├── chat_widgets.py      ← 199 行 (BubbleLabel/ChatMessageRow/ChatView)
│   └── settings_popup.py    ← 2641 行 (SettingsPopup 全部逻辑)
├── config.json / scenes.json
├── buildozer.spec
├── backup/step1~6_*/        ← 每步独立备份
└── profiles/ / characters/ / bin/
```

### 10.4 关键设计决策

**1. `config.py` 完全消灭 `global`**
- 所有全局变量（API_KEY/BASE_DIR/ACTIVE_PROFILE 等）改为 `config.xxx` 模块属性
- 修改时代码写 `config.API_KEY = ***`，跨文件自动生效
- JSON 字典重命名为 `config.app_config`，避免和模块名冲突
- 5 个 `global` 声明全部移除

**2. SettingsPopup 通过引用解耦**
- 接收 `app_instance` 参数，152 处 `self.app` 调用无需修改 DormApp 导入
- 消除了 SettingsPopup ↔ DormApp 的循环依赖风险

**3. api_service.py 统一 API 层**
- 3 处重复的 `httpx.Client.post(...)` → 一个 `call_chat_completion()`
- `_parse_api_error()` 移入 `api_service._parse_error()`
- `import httpx` 从 main.py 和 settings_popup.py 中移除
- 未来加流式输出只需改这一个文件

**4. 拆分过程中踩的坑**
- `config.setdefault(...)` 漏替换 → AttributeError（第一步遗漏，测试时捕捉）
- `import config` 被插到文件深处 → 内联 `from kivy.graphics import` 干扰搜索
- `FitSpinnerOption` 未加入 import 列表 → NameError（第 2 步遗漏）
- `config.get(...)` → `config.app_config.get(...)` 双重前缀 → 手动修复 15 处

### 10.5 同期 Bug 修复

**Bug #1: 动态模式用户发言权重**
- 问题：`_pick_next_speaker_rules()` 中 `if name == "You": continue` 跳过了用户的沉默加成，导致用户在动态模式下几乎被选中
- 修复：删除 `continue`，用户享受 0.6× 衰减沉默加成 + 12 轮硬沉默上限（角色为 15 轮）

**Bug #2: AI 创建剧本后对话残留**
- 问题：`switch_profile()` 先 `_do_reset()`（用旧数据展示 welcome）→ 再 `load_profile()`（加载新数据），顺序反了
- 修复：`switch_profile()` 改为先加载 → 再清空展示

**Bug #3: 删除/重命名取消后下拉框不回弹**
- 问题：下拉框选了 B（未切换），点删除→取消，下拉框仍显示 B
- 修复：弹窗 `on_dismiss` 回调重置下拉框到操作前状态（剧本→激活剧本，对话→操作前选项）

**Bug #4: 重命名弹窗大空档**
- 问题：Popu…ize_hint 比例过大 + 内容未推顶
- 修复：添加 `Widget(size_hint_y=1)` 弹性空间 + `size_hint` 收紧到 0.28（参照 `_show_custom_model_dialog` 的做法）

### 10.6 重构收益总结

| 维度 | 之前 | 之后 |
|------|------|------|
| main.py 行数 | 5185 | 2024 (-61%) |
| 模块文件数 | 1 | 8 |
| global 声明 | 5（跨文件失效） | 0 |
| httpx 重复调用 | 3 处独立实现 | 1 处统一封装 |
| RecycleView 替换 | 找 30 分钟 | 直接打开 chat_widgets.py |
| Git 冲突概率 | 极高 | 低 |

---


## 九、致谢

本项目的开发得到了以下技术与服务的支持：

- **DeepSeek API**：提供大语言模型对话能力
- **Kivy**：跨平台 GUI 框架（纯原生，零 KivyMD 依赖）
- **httpx**：HTTP 客户端（AI API 调用 + 并行请求）
- **Buildozer / python-for-android**：Android APK 打包工具链
- **PyInstaller**：Windows 可执行文件打包
- **ghproxy / 清华 PyPI 镜像**：国内网络加速

---

> *本报告基于开发者与 AI 助手（莉莉）的完整对话记录（session transcript），以及项目文件的 CHANGELOG.md、dorm-life-android-bug-report.md 等技术文档综合整理。*
>
> *报告生成时间：2026年6月26日 21:30 CST（含 v0.5.1 至 v0.8.7 全部版本记录）*

---

## 十一、第十日：6月27日（周六）— GitHub 开源发布

今日是项目从私有开发转向公开发布的关键一天。完成了 GitHub 仓库搭建、代码清理、Release 发布和文档撰写。

### 11.1 GitHub 仓库搭建（下午 15:00—15:30）

#### 初始化

- 在 GitHub 创建公开仓库 `bowenzhang01/ChatRoom`
- WSL 中 `git init`，创建 `.gitignore` 排除敏感/无关文件
- 创建 `config.example.json` 模板文件，API key 占位
- 初始提交：86 个文件，8689 行代码

#### .gitignore 排除清单

```
config.json          # 含 API Key
__pycache__/         # Python 缓存
backup/              # 开发备份
.buildozer/          # Buildozer 构建缓存
bin/                 # 编译产物（APK 通过 Release 分发）
*.ttf                # 字体文件（需自行下载，约 10MB）
characters/          # 自用角色备份
profiles/dorm_girls/ # 自用剧本
profiles/profile_*   # 试验剧本
build_with_mirror.sh # 镜像脚本
diag.py              # 测试脚本
```

#### 网络挑战

- WSL 无法直连 GitHub → 配置 Windows 端 git 代理（`http://127.0.0.1:10809`）
- Push 使用 Personal Access Token 认证
- 推送后清理 remote URL 中的 token（先 remove 再 add）

### 11.2 发布前清理（下午 15:30—15:50）

#### 移除个人数据

- 4 个个人/试验剧本移入 `backup/`：`dorm_girls`、`profile_32d948ea`、`profile_9b958ae8`、`profile_9cf52dbd`
- 自用角色备份 `characters/` 移入 `backup/`
- 镜像构建脚本 `build_with_mirror.sh` 和测试脚本 `diag.py` 移入 `backup/`
- Buildozer 已配置 `source.exclude_dirs = backup`，打包时自动排除

#### 配置文件清理

- `config.json`：API key 替换为 `***`，`active_profile` 改为 `dorm_life`
- `config.example.json`：同步更新，作为公开模板
- `config.py` 支持环境变量 `DEEPSEEK_API_KEY` fallback

#### Commit 历史整理

- 使用 `git filter-branch` 修改 initial commit message：
  - 旧：`Dorm Life v0.9.0 - 女生寝室AI角色扮演聊天室`
  - 新：`ChatRoom v0.9.0 - AI角色扮演聊天室`
- 原因：项目不止女生寝室一个场景，应用名已是 ChatRoom
- 修复作者信息（Windows git 全局 config 误用了 Arona 身份）

### 11.3 v0.9.0 Release（下午 16:30—16:47）

- 打 tag `v0.9.0` 并推送
- APK 编译完成：`chatroom-0.1-arm64-v8a_armeabi-v7a-debug.apk`（47MB）
- 通过 GitHub 网页端创建 Release，上传 APK

### 11.4 README 与文档（下午 16:47—17:00）

- 撰写完整 `README.md`：项目介绍、功能特色、安装指南、使用教程、构建指南、项目结构
- 更新本过程报告（新增第十一日章节）

### 11.5 今日数据统计

| 指标 | 数值 |
|------|------|
| Git commits | 3（initial + cleanup + bugfix） |
| 排除文件/目录 | 12 个 |
| README 字数 | ~600 字（中英混合） |
| 报告新增字数 | ~500 字 |
| APK 体积 | 47MB |

---

## 十二、第十二日：6月28日（周六）— 发言顺序拖拽排序 & 角色池管理

### 12.1 问题背景

此前发言顺序管理存在严重的 UX 缺陷：

- **纯文本输入框**：用户手动输入逗号分隔的角色英文名（如 `Yuki,Mei,Lin,Rui`），打错一个字母就静默过滤掉，顺序丢失
- **角色池混乱**：所有角色都在 `turn.order` 里，无法区分「参与对话」和「仅保存不用」的角色
- **增减自动追加**：新建角色 → 追加到末尾；删除角色 → 直接从顺序移除。用户无法控制插入位置
- **移动端体验差**：在手机上编辑逗号分隔的英文名简直是灾难

### 12.2 解决方案：活跃角色 + 可选角色双区

**核心架构**：

```
┌──────────────────────────────────────┐
│  发言顺序 Tab                        │
│                                      │
│  ▼ 活跃角色（参与对话）               │
│  ┌──────────────────────────────────┐│
│  │  ≡  ● Yuki  (雪纪)         [✕] ││  ← 长按≡拖拽排序 / [✕]移回待命区
│  │  ≡  ● Mei   (芽衣)         [✕] ││
│  │  ≡  ● Lin   (林)           [✕] ││
│  │  ≡  ● Rui   (瑞)           [✕] ││
│  └──────────────────────────────────┘│
│                                      │
│  ▼ 待命角色（点击加入对话）            │
│  ┌──────────────────────────────────┐│
│  │  [+] Haru  [+] Aiko  [+] Sora   ││  ← 点+号加入活跃列表
│  └──────────────────────────────────┘│
│                                      │
│  🔒 You（用户模式自动追加）            │
└──────────────────────────────────────┘
```

**数据模型不变**：`turn.order` 仍然是一个 JSON 数组，只需把「在 order 里」和「不在 order 里」的角色在 UI 层分开显示即可。

### 12.3 技术实现

#### 新增文件

| 文件 | 行数 | 作用 |
|------|------|------|
| `ui/widgets/_drag_list.py` | ~420 行 | 可拖拽排序的列表组件（核心） |
| `ui/settings_tabs/_speak.py` | ~210 行 | 「发言」Tab（活跃/可选双区 UI） |

#### 核心组件：ReorderableList

自定义 Kivy 组件，实现长按拖拽排序：

- **`DragListItem`**：单行，含 ≡ 拖拽手柄 + 角色色点 + 显示名 + [移除] 按钮，Canvas 圆角卡片 + 阴影
- **`ReorderableList`**：垂直排列的排序列表，触摸事件处理
  - `on_touch_down`：检测 ≡ 手柄，300ms 长按进入拖拽模式，`touch.grab(self)` 阻止 ScrollView 滚动
  - `on_touch_move`：检测手指位置 → 调用 `_get_item_at_y` 确定目标位置 → `_swap_items` 交换
  - 拖拽中的「漂浮」效果：被拖行半透明 + 绿色手柄，阴影加强
  - 插入指示线：Canvas 绘制 accent 色水平线指示落点
- **`ReorderableListScroll`**：滚动容器，拖拽时锁定自身滚动，支持边缘自动滚动

#### 边缘自动滚动

手指拖到列表顶部/底部 20dp 范围时，自动向该方向滚动。经过多次迭代修复了坐标系混乱问题：

- **难点**：`touch.grab(self)` 后 `on_touch_move` 不再经过 ScrollView 的坐标变换，导致 `touch.pos` 可能处于窗口坐标、ScrollView 本地坐标或内容本地坐标——取决于 Kivy 内部派发路径
- **最终方案**：使用 `ws.to_widget(touch.x, touch.y)`（不带 `relative=True`）将窗口坐标穿过完整 widget 树变换为 ScrollView 本地坐标，然后与 ScrollView 的固定边界（底部=0、顶部=height）比较

#### 待命角色区

横向排列的角色卡片，每个显示角色色点 + 显示名 + [+] 按钮。点击将角色名追加到 `turn.order` 末尾并刷新 UI。角色一旦加入活跃列表，就从待命区消失。

### 12.4 UI 集成

#### 设置弹窗新增「发言」Tab

```
原： [剧本] [场景] [角色] [API] [设置]
新： [剧本] [场景] [角色] [发言] [API] [设置]
```

- `SpeakTabMixin` 类：`_build_speak_tab()` / `_refresh_speak_tab()` / `_add_optional_to_order()` 等
- `SettingsPopup` 的 `__init__` 新增 `SpeakTabMixin` 继承
- 「剧本」Tab 的发言顺序输入框改为只读摘要标签（引导用户到「发言」Tab 编辑）

#### 角色管理联动

- 新建角色时：从 `_chars.py` 移除自动 `turn_order.append(base)` 逻辑（改为由用户在「发言」Tab 手动添加）
- 删除角色时：保留自动从 `turn_order` 移除（防止引用不存在的角色名）
- You 角色的特殊处理：用户模式下在活跃列表中显示但锁定（不可移除、灰色手柄）

### 12.5 改动量统计

| 类型 | 文件 | 说明 |
|------|------|------|
| 新增 | `ui/widgets/__init__.py` | 包初始化 |
| 新增 | `ui/widgets/_drag_list.py` | 拖拽列表核心组件 (~420行) |
| 新增 | `ui/settings_tabs/_speak.py` | 发言 Tab UI (~210行) |
| 修改 | `ui/settings_popup.py` | 加入 SpeakTabMixin + 「发言」Tab 注册 |
| 修改 | `ui/settings_tabs/_world.py` | 发言顺序输入框→只读标签 |
| 修改 | `ui/settings_tabs/_chars.py` | 移除新建角色时自动追加 turn_order |
| 修改 | `ui/settings_tabs/_app.py` | 移除 `_refresh_app_inputs` 中书序输入框逻辑 |
| 修改 | `core/data_manager.py` | 数据层微调 |
| 修改 | `profiles/dorm_life/` | 角色及场景配置更新 |

### 12.6 设计经验

1. **数据模型不变，只改 UI 层**：`turn.order` 始终是 JSON 数组，活跃/待命的分离纯属 UI 呈现。新增角色不再自动加 order，给用户完全控制权
2. **Kivy 触摸事件坐标体系是拖拽最大的坑**：`touch.grab()` 导致后续 move 事件绕过 ScrollView 的 `apply_transform_2d`，使坐标处于意料之外的坐标系。反复测试、打日志是比较可靠的调试手段
3. **长按+拖拽比纯拖拽更适合移动端**：300ms 长按进入拖拽模式，避免短触和滚动手势歧义
4. **拖拽手柄 ≡ 是重要的 affordance**：不用文档解释，用户看到 ≡ 就知道可以拖

---

## 十三、最终交付物清单

| 产物 | 平台 | 位置 | 状态 |
|------|------|------|------|
| ChatRoom APK v0.9.1 | Android | [GitHub Releases](https://github.com/bowenzhang01/ChatRoom/releases/tag/v0.9.1) | ✅ 已发布 |
| 源代码 | 跨平台 | [GitHub 仓库](https://github.com/bowenzhang01/ChatRoom) | ✅ 已开源 |
| README.md | — | 仓库根目录 | ✅ 已撰写 |
| 项目过程报告 | — | 本地 workspace | ✅ 已更新 |
| config.example.json | — | 仓库根目录 | ✅ 模板 |
| chatroom-0.1-arm64-v8a_armeabi-v7a-debug.apk | Android | `bin/` | ✅ 编译完成 (47MB) |

---

> *报告最后更新时间：2026年6月28日 18:00 CST（含 v0.5.1 至 v0.9.1 全部版本记录）*
