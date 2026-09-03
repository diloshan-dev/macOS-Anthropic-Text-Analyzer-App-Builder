
<div align="center">

# 🍎 macOS Anthropic Text Analyzer — App Builder

**A standalone macOS dark-themed GUI application built with Python & CustomTkinter,
that analyzes `.txt` files using the Anthropic Claude API.**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-2CC985?style=for-the-badge)
![Anthropic](https://img.shields.io/badge/API-Claude-D97757?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-macOS-000000?style=for-the-badge&logo=apple&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</div>

---

## 📖 Table of Contents

- [About](#-about)
- [Key Features](#-key-features)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start Guide](#-quick-start-guide)
- [Building a Standalone macOS App](#-building-a-standalone-macos-app)
- [License](#-license)

---

## 📝 About

This app packages a working Python + Claude API text-analysis script into a
simple, double-clickable desktop tool — no terminal or code editing required
to use it. Users enter their own Anthropic API key, pick a `.txt` file, and
get an instant AI-generated analysis.

<div align="center">
  <img src="image.png" alt="App Preview" width="600"/>
</div>

---

## ✨ Key Features

| | Feature | Description |
|---|---|---|
| 🔑 | **In-App API Key Entry** | Enter your Anthropic API key directly in a masked input field — nothing hardcoded. |
| 📄 | **Simple File Picker** | Select any `.txt` file through a native macOS file dialog. |
| 🤖 | **Claude-Powered Analysis** | Sends file content to the Claude API and returns a concise analysis. |
| ⚡ | **Non-Blocking UI** | API calls run on a background thread with a progress indicator, so the app never freezes. |
| 🎨 | **Dark Mode UI** | Clean, modern dark interface built with `CustomTkinter`. |
| 🛡️ | **Friendly Error Handling** | Clear messages for missing keys, bad files, invalid keys, or connection issues. |

---

## 🛠️ Tech Stack

| Component | Technology / Library |
| :--- | :--- |
| **Language** | Python 3.x |
| **GUI Framework** | `CustomTkinter` |
| **AI Provider** | Anthropic Claude API (`anthropic` SDK) |
| **Packaging** | `PyInstaller` |

---

## 📂 Project Structure

```text
macOS-Anthropic-Text-Analyzer-App-Builder/
├── app.py              # Main application code (GUI & logic)
├── Requirements.txt    # Required Python packages
├── image.png           # Application GUI Preview
└── README.md           # Project documentation
---

## 🚀 Quick Start Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/diloshan-dev/macOS-Anthropic-Text-Analyzer-App-Builder.git
cd macOS-Anthropic-Text-Analyzer-App-Builder
```

### 2️⃣ Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Application
```bash
python app.py
```

### 4️⃣ Use It
1. Paste your **Anthropic API key** into the key field.
2. Click **Select Text File** and choose a `.txt` file.
3. Click **Analyze Text** and wait for the result.

---

## 📦 Building a Standalone macOS App

To package this into a double-clickable `.app` with no terminal needed:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "TextAnalyzer" app.py
```

The finished app will be in `dist/TextAnalyzer/`. Copy `TextAnalyzer.app` into
your `Applications` folder to run it like any other Mac app.

> ⚠️ Users still need to enter their **own** Anthropic API key on first launch — no key is bundled with the app.

---

## 📜 License

This project is open-source and available under the **MIT License**.

---

<div align="center">

Made with ❤️ using Python & CustomTkinter

</div>
