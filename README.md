# gcm — Git Commit Message generator

Tool CLI sinh git commit message tự động từ thay đổi đã `git add`, dùng Groq API (free).
Python thuần (chỉ stdlib, không cần `pip install`).

## Cài đặt (1 lệnh)

```bash
./install.sh
```

Script tự lo: symlink vào `~/.local/bin`, thêm PATH nếu thiếu, và hỏi/lưu Groq API key.
Lấy key free tại https://console.groq.com/keys.

> Cài thủ công nếu muốn: `ln -sf "$(pwd)/gcm" ~/.local/bin/gcm` rồi
> `echo "gsk_..." > ~/.config/gcm/config && chmod 600 ~/.config/gcm/config`.

## Cách dùng

```bash
git add .     # stage thay đổi
gcm           # message tiếng Anh (Conventional Commits) + hỏi commit
gcm --vi      # message tiếng Việt
gcm -a        # tự git add -A rồi sinh
gcm -p        # chỉ in message, không hỏi (tiện copy / nối lệnh)
gcm -h        # trợ giúp
```

Sau khi sinh, tool hỏi: `[Enter]` commit luôn / `[e]` mở editor sửa / `[n]` hủy.

## Ghi chú kỹ thuật

- Endpoint: Groq `/openai/v1/chat/completions`, model `llama-3.3-70b-versatile`.
- Request bắt buộc có header `User-Agent`, nếu thiếu Cloudflare chặn 403 (error 1010).
- Diff > 12000 ký tự sẽ bị cắt bớt trước khi gửi.
