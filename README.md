# Antigravity-Pure-HUD

[English](README.md) | [简体中文](README.zh-CN.md)

A lightweight, zero-dependency, ASCII-safe Status Line HUD plugin for **Google Antigravity CLI (`agy`)**.

Unlike other HUD plugins that rely on specialized Nerd Fonts (which often cause glyph rendering issues on Windows Command Prompt / PowerShell), **Antigravity-Pure-HUD** renders high-compatibility progress bars and status telemetry natively across all operating systems.

---

## Preview

![Antigravity Pure HUD Preview](preview.png)

---

## Features

- **Zero Dependency & Zero Font Issues**: Uses standard ASCII and cross-platform Unicode blocks that render cleanly without Nerd Fonts or encoding glitches.
- **Near-Zero Latency (~10ms)**: Parses raw JSON directly from stdin provided by Antigravity CLI without making external network requests.
- **Dual Directional Indicators**:
  - **Context Window**: Forward progress (`used %`) indicating memory consumption in the current session.
  - **Usage / 5-Hour Quota**: Reverse progress (`left %`) indicating remaining rate limit quota with live countdown reset timer.
- **Multi-Platform Support**: Built for Windows (PowerShell / CMD), macOS, and Linux.

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Darastas/Antigravity-Pure-HUD.git
```

### 2. Register the Plugin with AGY CLI
```bash
agy plugin install ./Antigravity-Pure-HUD
```

### 3. Activate the Status Line in AGY CLI

Inside your interactive `agy` CLI shell, run:

#### Windows (PowerShell / CMD)
```text
/statusline <path-to-repo>/hooks/status-line.bat
```

#### macOS / Linux / Git Bash
```text
/statusline <path-to-repo>/hooks/status-line.sh
```

---

## Configuration & Management

- **Disable Statusline**:
  ```text
  /statusline off
  ```
- **List Installed Plugins**:
  ```bash
  agy plugin list
  ```

---

## License

MIT © [Darastas](https://github.com/Darastas)
