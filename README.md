# 🎭 ChatRoom - AI 角色扮演聊天室

> 基于 Kivy 的多剧本 AI 角色扮演 Android 应用 · v0.9.0

ChatRoom 是一个 AI 驱动的多人角色对话模拟器。创建虚拟角色，设定世界观，让大语言模型驱动角色间的自动对话。支持导演模式（干预对话走向）和用户模式（以角色身份参与对话）。

---

## ✨ 功能特色

- 🎭 **多剧本支持** — 一键切换不同世界观（寝室日常、星际飞船……），每个剧本拥有独立角色、场景和对话记录
- 🤖 **AI 驱动对话** — 大语言模型驱动多角色自动对话，支持轮流/随机/动态三种发言模式
- 🎬 **导演模式** — 实时以导演身份介入对话，引导剧情走向
- 👤 **用户模式** — 扮演任意角色参与 AI 对话
- 💬 **对话存档** — 保存/读取/删除完整对话历史，AI 自动生成对话标题
- 🔄 **自动恢复** — 意外退出后自动存档，下次启动询问恢复
- 🧠 **AI 内容创作** — AI 一键创建剧本（世界观+场景+角色），AI 补全/生成场景和角色
- 🌍 **世界观系统** — 跨 AI 操作的共享背景锚点，确保角色行为一致性
- 📱 **纯原生 Kivy** — 零 KivyMD 依赖，APK 体积小，兼容 Android 5.0+

---

## 📱 安装

### 从 Release 下载（推荐）

前往 [Releases](https://github.com/bowenzhang01/ChatRoom/releases) 下载最新 APK，在 Android 设备上安装即可。

### 桌面预览

```bash
pip install kivy httpx
python main.py
```

> ⚠️ 桌面端主要用于开发预览，部分功能（自动存档）仅在 Android 上触发。

---

## ⚙️ 配置

### 获取 API Key

ChatRoom 支持**兼容 OpenAI 接口格式**的大语言模型 API，包括但不限于：

- [DeepSeek](https://platform.deepseek.com)（默认配置）
- [OpenAI](https://platform.openai.com)
- [Groq](https://console.groq.com)
- [硅基流动](https://siliconflow.cn)
- 任何自部署的 vLLM / Ollama 等兼容服务

注册你选择的服务商，获取 API Key（通常格式为 `sk-xxxxxxxx`）。

### 应用内配置

首次启动后：
1. 点击底部 **「设置」** 按钮
2. 切换到 **「API」** Tab
3. 填入 API Key 和 API Base URL（不同服务商地址不同）
4. 点击 **「测试 API」** 验证连接
5. 成功后自动获取可用模型列表

> 也可直接编辑 `config.json`，将 `api_key` 和 `api_base` 字段替换为你的配置。参考 [`config.example.json`](config.example.json)。

---

## 🎮 使用指南

### 基本操作

| 按钮 | 功能 |
|------|------|
| **开始** | 启动 AI 自动对话 |
| **暂停** | 暂停对话（自动存档） |
| **停止** | 结束本轮对话 |
| **设置** | 打开设置页面 |
| **保存** | 保存当前对话（AI 生成标题） |

### 发言模式

- **轮流** — 角色按固定顺序依次发言
- **随机** — 随机选择下一个发言人
- **动态** — AI 根据对话内容智能决定发言顺序

### 导演模式 vs 用户模式

- **导演模式**：你以旁白身份输入指令，AI 角色响应
- **用户模式**：你以 You 角色身份参与对话，AI 角色与你互动

### 创建剧本

1. 打开设置 → **「设置」** Tab
2. 点击 **「新建」** 或 **「AI创建」**
3. 「AI创建」：输入一句话（如 "魔法学院的四个学生"），AI 自动生成完整剧本

---

## 🏗️ 从源码构建 APK

### 环境要求

- Ubuntu 22.04+ (WSL2 亦可)
- Python 3.x
- Buildozer

### 构建步骤

```bash
# 1. 安装 Buildozer
pip install buildozer

# 2. 克隆仓库
git clone https://github.com/bowenzhang01/ChatRoom.git
cd ChatRoom

# 3. 配置 API Key（可选，也可在应用内配置）
cp config.example.json config.json
# 编辑 config.json，填入你的 API Key 和 Base URL

# 4. 构建 APK（首次耗时较长，需下载 SDK/NDK）
buildozer android debug

# 5. APK 位于 bin/ 目录下
```

> 国内用户可能需要配置代理或使用镜像。参见 `buildozer.spec` 中的网络配置。

---

## 📁 项目结构

```
ChatRoom/
├── main.py                  # 主入口（DormApp，~2000 行）
├── config.py                # 全局配置与路径常量
├── config.example.json      # 配置文件模板（不含 API Key）
├── utils.py                 # 工具函数（JSON 读写、颜色转换）
├── api_service.py           # LLM API 调用封装
├── buildozer.spec           # Buildozer Android 打包配置
├── scenes.json              # 默认全局场景
├── core/                    # 核心业务逻辑
│   ├── ai_engine.py         # AI 引擎（提示词构建）
│   ├── chat_manager.py      # 聊天管理（发言顺序、存档）
│   └── data_manager.py      # 数据管理
├── ui/                      # 用户界面组件
│   ├── base_widgets.py      # 基础控件（圆角按钮、下拉框）
│   ├── chat_widgets.py      # 聊天气泡系统
│   ├── settings_popup.py    # 设置弹窗
│   ├── settings_tabs/       # 设置页各 Tab
│   ├── animations.py        # 动画
│   └── theme.py             # 主题
├── profiles/                # 剧本目录（每个剧本独立文件夹）
│   ├── dorm_life/           # 剧本：寝室日常
│   │   ├── config.json      # 剧本设置
│   │   ├── scenes.json      # 剧本场景
│   │   ├── characters/      # 剧本角色
│   │   └── chats/           # 对话存档
│   └── starship/            # 剧本：星际飞船
│       └── ...
└── backup/                  # 开发备份（buildozer 自动排除）
```

---

## 📝 项目历程

ChatRoom 从 2026 年 6 月 17 日启动，经历了 40+ 个版本的快速迭代：

- v1.0~v2.0：CLI 原型 → FastAPI Web 版
- v0.3.x：tkinter 桌面版 → PyInstaller 打包
- v0.5.x：Kivy 移动版 → Android APK
- v0.6.5：多剧本/多配置组架构
- v0.7.x：AI 全流程辅助（场景/角色/剧本创作）
- v0.8.x：对话存档系统 + 动态发言顺序 + 保存系统
- v0.9.0：代码模块化拆分（1 文件 → 8 模块）

详见 [项目过程报告](ChatRoom-项目过程报告.md)。

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Kivy（纯原生，零 KivyMD 依赖） |
| AI | OpenAI 兼容 API（DeepSeek / OpenAI / Groq / 硅基流动 等） |
| HTTP | httpx |
| 打包 | Buildozer + python-for-android |
| 语言 | Python 3.x |
| 平台 | Android / Windows（桌面预览） |

---

## 📄 许可

MIT License

---

> 💡 首次使用建议：先测试 API 连接 → 选择「寝室日常」剧本熟悉操作 → 再用「AI 创建」功能打造你自己的剧本！
