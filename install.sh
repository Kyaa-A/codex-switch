#!/usr/bin/env bash
# ── codex-switch installer ────────────────────────────────────
# curl -fsSL https://raw.githubusercontent.com/Kyaa-A/codex-switch/main/install.sh | bash

set -euo pipefail

GREEN='\033[32m'
CYAN='\033[36m'
BOLD='\033[1m'
DIM='\033[2m'
RST='\033[0m'
CODEX_GREEN='\033[38;2;16;163;127m'

REPO_URL="https://raw.githubusercontent.com/Kyaa-A/codex-switch/main/codex-switch"
INSTALL_DIR="${HOME}/.local/bin"
INSTALL_PATH="${INSTALL_DIR}/codex-switch"

echo ""
echo -e "    ${CODEX_GREEN}${BOLD} ▄████▄ ${RST}  ${CODEX_GREEN}${BOLD}codex-switch${RST} ${DIM}installer${RST}"
echo -e "    ${CODEX_GREEN}${BOLD}███  ███${RST}  ${DIM}Multi-account manager for OpenAI Codex CLI${RST}"
echo -e "    ${CODEX_GREEN}${BOLD} ▀████▀ ${RST}  ${CYAN}${DIM}https://github.com/Kyaa-A/codex-switch${RST}"
echo ""

mkdir -p "$INSTALL_DIR"

if command -v curl &>/dev/null; then
    curl -fsSL "$REPO_URL" -o "$INSTALL_PATH"
elif command -v wget &>/dev/null; then
    wget -qO "$INSTALL_PATH" "$REPO_URL"
else
    echo "  Error: curl or wget required"
    exit 1
fi

chmod +x "$INSTALL_PATH"

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "  ${DIM}Adding ~/.local/bin to PATH...${RST}"

    SHELL_NAME=$(basename "$SHELL")
    RC_FILE=""
    case "$SHELL_NAME" in
        bash) RC_FILE="$HOME/.bashrc" ;;
        zsh)  RC_FILE="$HOME/.zshrc" ;;
        fish) RC_FILE="$HOME/.config/fish/config.fish" ;;
    esac

    if [[ -n "$RC_FILE" ]]; then
        if [[ "$SHELL_NAME" == "fish" ]]; then
            echo "set -gx PATH \$HOME/.local/bin \$PATH" >> "$RC_FILE"
        else
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
        fi
        echo -e "  ${DIM}Added to ${RC_FILE}${RST}"
    fi
fi

echo -e "  ${GREEN}✔${RST}  Installed to ${BOLD}${INSTALL_PATH}${RST}"
echo ""
echo -e "  ${BOLD}Get started:${RST}"
echo -e "    ${CYAN}codex-switch save <name>${RST}   ${DIM}# save current account under any name${RST}"
echo -e "    ${CYAN}codex-switch login${RST}         ${DIM}# login to another account${RST}"
echo -e "    ${CYAN}codex-switch use [name]${RST}    ${DIM}# switch anytime (or interactive)${RST}"
echo ""
