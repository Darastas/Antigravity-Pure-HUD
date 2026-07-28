# Antigravity-Pure-HUD

[English](README.md) | [简体中文](README.zh-CN.md)

一个专为 **Google Antigravity CLI (`agy`)** 打造的零依赖、高兼容、无乱码轻量级状态栏 HUD 插件。

不同于其他依赖第三方 Nerd Fonts 特殊图标（在 Windows CMD / PowerShell 下极易出现乱码）的插件，**Antigravity-Pure-HUD** 采用全平台高兼容的文本与通用进度条格式，提供极致流畅且无报错的终端体验。

---

## 效果预览

![Antigravity Pure HUD Preview](preview.png)

---

## 核心特性

- **零依赖与零乱码**：使用通用 Unicode 块（`█` 与 `░`），无需安装任何第三方 Nerd 字体，彻底杜绝终端乱码。
- **0 延迟秒刷 (Min-Quota 仲裁)**：结合本地守护进程 HTTP 直连与 `stdin` 动态比对，自动抓取并展示最新配额，杜绝官方后端缓存延迟。
- **多模型配额池独立监控**：
  - **Gemini 池**：实时追踪 Gemini 全系模型的剩余百分比与重置倒计时。
  - **Claude / GPT (3P) 池**：独立监控第三方高级模型的合并共享配额。
- **响应式液态排版**：根据终端实际宽度自动伸缩进度条长度（10 / 8 / 6 / 4 格），并在窄屏下自动缩写标签，永不乱行或越界。
- **全平台兼容**：完美支持 Windows (PowerShell / CMD)、macOS 与 Linux。

---

## 安装指南

### 1. 克隆仓库
```bash
git clone https://github.com/Darastas/Antigravity-Pure-HUD.git
```

### 2. 在 AGY CLI 中注册插件
```bash
agy plugin install ./Antigravity-Pure-HUD
```

### 3. 在 AGY CLI 中激活状态栏

在已打开的 `agy` CLI 交互界面中运行对应平台的激活指令：

#### Windows (PowerShell / CMD)
```text
/statusline <仓库路径>/hooks/status-line.bat
```

#### macOS / Linux / Git Bash
```text
/statusline <仓库路径>/hooks/status-line.sh
```

---

## 常用管理命令

- **关闭状态栏**：
  ```text
  /statusline off
  ```
- **查看已安装插件**：
  ```bash
  agy plugin list
  ```

---

## 开源协议

MIT © [Darastas](https://github.com/Darastas)
