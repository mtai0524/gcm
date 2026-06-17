#!/usr/bin/env bash
# Cài đặt gcm chỉ với 1 lệnh: ./install.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/gcm"

echo "==> Cài đặt gcm"

# Phát hiện hệ điều hành
OS="$(uname -s)"
mkdir -p "$BIN_DIR"
chmod +x "$SCRIPT_DIR/gcm" 2>/dev/null || true

case "$OS" in
  MINGW*|MSYS*|CYGWIN*)
    # Windows (Git Bash): symlink hay kẹt, dùng wrapper gọi python trực tiếp
    # Ưu tiên 'py' (Windows Python launcher) vì không bị alias Store chen vào
    PY=""
    for cand in py python python3; do
      if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
    done
    if [ -z "$PY" ]; then
      echo "  [LỖI] chưa cài Python cho Windows."
      echo "        Cài: winget install Python.Python.3.12  (rồi mở lại Git Bash)"
      echo "        Và tắt App execution aliases python.exe/python3.exe trong Windows Settings."
      exit 1
    fi
    cat > "$BIN_DIR/gcm" <<EOF
#!/usr/bin/env bash
exec $PY "$SCRIPT_DIR/gcm" "\$@"
EOF
    chmod +x "$BIN_DIR/gcm"
    echo "  [ok] wrapper: $BIN_DIR/gcm  (dùng '$PY')"
    ;;
  *)
    # Linux / macOS: copy thang file vao PATH (standalone, khong phu thuoc repo)
    rm -f "$BIN_DIR/gcm"
    cp "$SCRIPT_DIR/gcm" "$BIN_DIR/gcm"
    chmod +x "$BIN_DIR/gcm"
    echo "  [ok] da copy: $BIN_DIR/gcm (ban standalone)"
    ;;
esac

# 2. Đảm bảo ~/.local/bin trong PATH
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
  SHELL_RC="$HOME/.bashrc"
  [ -n "$ZSH_VERSION" ] && SHELL_RC="$HOME/.zshrc"
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
  echo "  [ok] đã thêm ~/.local/bin vào PATH ($SHELL_RC) — mở terminal mới hoặc: source $SHELL_RC"
else
  echo "  [ok] ~/.local/bin đã có trong PATH"
fi

# 3. Cấu hình API key
mkdir -p "$CONFIG_DIR"

# Copy file mẫu để người dùng dễ cấu hình (không đè file đang dùng)
for ex in config.example system_prompt.example.md; do
  if [ -f "$SCRIPT_DIR/$ex" ]; then
    cp -f "$SCRIPT_DIR/$ex" "$CONFIG_DIR/$ex"
  fi
done
echo "  [ok] file mẫu: $CONFIG_DIR/config.example, $CONFIG_DIR/system_prompt.example.md"

if [ -n "$GROQ_API_KEY" ] || [ -s "$CONFIG_DIR/config" ]; then
  echo "  [ok] API key đã có (env hoặc $CONFIG_DIR/config)"
else
  echo
  echo "  Cần Groq API key (free). Lấy tại: https://console.groq.com/keys"
  read -rp "  Dán API key vào đây (Enter để bỏ qua, cấu hình sau): " key
  if [ -n "$key" ]; then
    echo "$key" > "$CONFIG_DIR/config"
    chmod 600 "$CONFIG_DIR/config"
    echo "  [ok] đã lưu key vào $CONFIG_DIR/config"
  else
    echo "  [skip] chưa cấu hình key. Sau này: echo 'gsk_...' > $CONFIG_DIR/config"
  fi
fi

echo
echo "==> Xong! Dùng: git add . && gcm   (gcm --vi cho tiếng Việt, gcm -h xem trợ giúp)"
