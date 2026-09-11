# codex-switch

<p align="center">
  <pre align="center">
       ▄▄██████▄▄       
    ▄████▀▀  ▀▀████▄      <b>CODEX-SWITCH</b>  v1.0.0
  ▄███▀   ▄██▄   ▀███▄    Multi-account manager for OpenAI Codex CLI
 ▄███    ██████    ███▄   ─────────────────────────────────────────
 ███   ▄████████▄   ███   ▸ <b>shared /resume</b>  ✔ all accounts access sessions
 ███  █████  █████  ███   ▸ <b>version</b>        1.0.0 #stable
 ███   ▀████████▀   ███   ▸ <b>repo</b>           https://github.com/Kyaa-A/codex-switch
 ▀███    ██████    ███▀   ▸ <b>status</b>         ● ready
  ▀███▄   ▀██▀   ▄███▀    ─────────────────────────────────────────
    ▀████▄▄  ▄▄████▀      Zero logout · Shared /resume · Pure bash
       ▀▀██████▀▀       
  </pre>
</p>

<p align="center">
  <b>Switch between multiple OpenAI Codex CLI accounts without logging out — with 100% shared <code>/resume</code> session history across every account. Zero dependencies. Pure bash.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/openai-10A37F?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI">
  <img src="https://img.shields.io/badge/bash-pure-4EAA25?style=for-the-badge&logo=gnu-bash&logoColor=white" alt="Pure Bash">
  <img src="https://img.shields.io/badge/shared%20resume-supported-brightgreen?style=for-the-badge" alt="Shared Resume">
  <img src="https://img.shields.io/badge/dependencies-zero-blue?style=for-the-badge" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="MIT License">
</p>

---

## 🎯 The Problem

When using OpenAI Codex CLI with multiple accounts (e.g. personal, work, different teams or client accounts), you often need to switch between them.

Currently, you have to run `codex logout` and then `codex login` every single time:
- It interrupts your flow with web browser popups.
- If you were working on a session on Account 1 and ran out of usage or needed to switch to Account 2, logging out and logging in feels clunky and risky.
- Full profile isolation tools often separate directories completely, meaning you **lose access to previous sessions** in your `/resume` picker.

## ⚡ The Solution: Shared `/resume` Across All Accounts

`codex-switch` solves this with an intelligent snapshot approach:

1. **Only authentication credentials (`~/.codex/auth.json`) are swapped.**
2. **Local thread histories, database logs, and sessions (`~/.codex/sessions/`, `history.jsonl`, `thread_history_1.sqlite`) remain untouched and shared.**
3. **You can start a task on Account A, switch to Account B, and immediately run `codex resume` or `/resume` to continue the exact same conversation seamlessly!**
4. **No `/logout` ever happens** — your tokens stay cached and ready to swap instantly.

---

## 🖥️ Terminal UI Preview

### Main Banner (`codex-switch help`)

```
       ▄▄██████▄▄       
    ▄████▀▀  ▀▀████▄      CODEX-SWITCH  v1.0.0
  ▄███▀   ▄██▄   ▀███▄    Multi-account manager for OpenAI Codex CLI
 ▄███    ██████    ███▄   ─────────────────────────────────────────
 ███   ▄████████▄   ███   ▸ shared /resume  ✔ all accounts access sessions
 ███  █████  █████  ███   ▸ version        1.0.0 #stable
 ███   ▀████████▀   ███   ▸ repo           https://github.com/Kyaa-A/codex-switch
 ▀███    ██████    ███▀   ▸ status         ● ready
  ▀███▄   ▀██▀   ▄███▀    ─────────────────────────────────────────
    ▀████▄▄  ▄▄████▀      Zero logout · Shared /resume · Pure bash
       ▀▀██████▀▀       

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  USAGE
    codex-switch [command] [options]

  COMMANDS

    save <name>          Save current login as a named profile
    use [name]           Switch to a saved profile (interactive if omitted)
    list                List all saved profiles with details
    rename [old] [new]   Rename a saved profile
    status              Show active profile + live verification
    login               Login to a new account and save it
    delete [name]        Delete a saved profile (interactive if omitted)
    help                Show this help message

  QUICK START

    # Step 1: Save current login under any name you want
    $ codex-switch save <name>

    # Step 2: Login to another account
    $ codex-switch login

    # Step 3: Switch between them anytime
    $ codex-switch use <name>

    # All sessions are shared — run anytime:
    $ codex resume
```

### Profile Cards with Live Usage & Shared Sessions (`codex-switch list`)

```
     ▄████▄   codex-switch v1.1.0
    ███  ███  Multi-account manager for OpenAI Codex CLI
     ▀████▀   Shared /resume · https://github.com/Kyaa-A/codex-switch

  🔑 Saved Codex Profiles (2 total)

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  work  ⚡ ACTIVE  🔒 248d remaining                                       │
  │  ├─ email  alex@company.com        │ 5h [░░░░░░░░░░]   0% · in 5h 0m     │
  │  └─ plan   team                    │ wk [████████░░]  82% · in 3d 19h    │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  personal  🔒 18d remaining                                               │
  │  ├─ email  alex@gmail.com          │ 5h [░░░░░░░░░░]   0% · in 4h 59m    │
  │  └─ plan   plus                    │ wk [░░░░░░░░░░]   0% · in 6d 23h    │
  └──────────────────────────────────────────────────────────────────────────┘

  💬 Shared Sessions: 838 conversations available to codex resume
```

### Interactive Switcher (`codex-switch use`)

```
     ▄████▄   codex-switch v1.1.0
    ███  ███  Multi-account manager for OpenAI Codex CLI
     ▀████▀   Shared /resume · https://github.com/Kyaa-A/codex-switch

  ⇄ Select Codex account to switch to:
  Use ↑↓ arrows (or j/k) to navigate, Enter to select, q to cancel

  ❯ work        alex@company.com  [chatgpt]  (active)
    personal    alex@gmail.com    [chatgpt]
    api-tier    Key: sk-proj...   [api_key]
```

---

## 🚀 Quick Install

### One-line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/Kyaa-A/codex-switch/main/install.sh | bash
```

### Or Manual Install

```bash
git clone https://github.com/Kyaa-A/codex-switch.git
cd codex-switch
chmod +x codex-switch
cp codex-switch ~/.local/bin/
```

---

## 📖 3-Step Setup Guide

### 1. Save your current account
```bash
codex-switch save [name]
```
*Creates a snapshot of your current credentials.*

### 2. Login to your secondary account
```bash
codex-switch login
```
*Auto-saves your current session first, launches the browser login flow, and prompts you for a profile name (`[name]`).*

### 3. Switch anytime — and `/resume` any session!
```bash
codex-switch use [name]       # switch directly by name
codex-switch use              # or launch the interactive arrow-key picker!
codex resume                  # continue any session across any account!
```

---

## 🛠️ Commands Reference

| Command | Shorthand | Description |
|---|---|---|
| `codex-switch` | | Open the interactive main menu |
| `codex-switch save <name>` | | Save current credentials as a named profile |
| `codex-switch use [name]` | `switch` | Switch to a profile (interactive picker if omitted) |
| `codex-switch list` | `ls` | List all profiles and show shared session pool count |
| `codex-switch rename [old] [new]` | `mv` | Rename an existing profile to any new name |
| `codex-switch status` | `whoami` | Show active profile and verify token against Codex CLI |
| `codex-switch login` | `add` | Safely login to a new account without losing current one |
| `codex-switch delete [name]` | `rm` | Delete a profile (interactive picker if omitted) |
| `codex-switch help` | `-h`, `--help`| Display ASCII banner and help reference |

---

## 🔬 How Shared `/resume` Works

OpenAI Codex CLI stores its state in `~/.codex/`:
```
~/.codex/
├── auth.json                  ← Active credentials (what codex-switch swaps)
├── sessions/                  ← ALL session conversations (NEVER touched)
├── session_index.jsonl        ← Session index (NEVER touched)
├── thread_history_1.sqlite    ← Thread history (NEVER touched)
└── .profiles/                 ← Where codex-switch stores auth snapshots
    ├── .active
    ├── work/
    │   └── auth.json
    └── personal/
        └── auth.json
```

Because `codex-switch` **only swaps `auth.json`**, your session database is 100% preserved and shared. 

You can start a session on `work`, switch to `personal` when daily quota is reached, and continue right where you left off with `codex resume --last`.

---

## ❓ Frequently Asked Questions

#### Will switching log out my accounts?
**No.** `codex-switch` never runs `codex logout`. It copies and swaps the credentials files locally.

#### Can I switch in the middle of a project and `/resume`?
**Yes!** That is the primary design feature of `codex-switch`. All past conversations are available in `codex resume` regardless of which account is active.

#### Does it support both ChatGPT OAuth and OpenAI API keys?
**Yes.** Whether you logged in with ChatGPT or via API key (`codex login --with-api-key`), `codex-switch` handles both.

#### Are any dependencies required?
**None.** It's 100% pure bash. Works on macOS and Linux out-of-the-box.

---

## 📄 License

MIT © [Kyaa-A](https://github.com/Kyaa-A)
