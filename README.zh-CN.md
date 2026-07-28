# Antigravity-Pure-HUD

[English](README.md) | [简体中文](README.zh-CN.md)

一个专为 **Google Antigravity CLI (`agy`)** 打造的零依赖、高兼容、无乱码轻量级状态栏 HUD 插件。

不同于其他依赖第三方 Nerd Fonts 特殊图标（在 Windows CMD / PowerShell 下极易出现乱码）的插件，**Antigravity-Pure-HUD** 采用全平台高兼容的文本与通用进度条格式，提供极致流畅且无报错的终端体验。

---

## 效果预览

![Antigravity Pure HUD Preview](preview.png)

---

## 核心特性

- **零依赖与零乱码**：使用通用 Unicode 块，无需安装任何第三方 Nerd 字体，彻底杜绝乱码问题。
- **极致性能 (~10ms)**：直接通过 `stdin` 读取并解析 AGY CLI 内存传输的 JSON 数据，零网络请求与延迟。
- **双向逻辑指示器**：
  - **Context (上下文窗口)**：正向计算 (`used %`)，直观显示当前 Session 已消耗的记忆比例。
  - **Usage (5小时配额)**：反向计算 (`left %`)，清晰展示剩余血量与精确的重置倒计时。
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
