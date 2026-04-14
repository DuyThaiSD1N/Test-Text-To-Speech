# Fix lỗi "Failed to fetch repository files" trên Railway

## Nguyên nhân:
- Railway không có quyền truy cập GitHub repo
- Repo là private nhưng chưa authorize
- GitHub App permissions bị lỗi

## Giải pháp:

### 1. Revoke và reconnect GitHub

1. Vào Railway Dashboard: https://railway.app/account
2. Click **"Account Settings"**
3. Tìm phần **"Connected Accounts"**
4. Click **"Disconnect"** GitHub
5. Click **"Connect GitHub"** lại
6. Authorize tất cả permissions

### 2. Đảm bảo repo là Public

Nếu repo là private:
1. Vào GitHub repo settings
2. Scroll xuống **"Danger Zone"**
3. Click **"Change visibility"** → **"Make public"**

### 3. Reinstall Railway GitHub App

1. Vào: https://github.com/settings/installations
2. Tìm **"Railway"**
3. Click **"Configure"**
4. Chọn **"All repositories"** hoặc chọn repo cụ thể
5. Click **"Save"**

### 4. Thử deploy từ template

1. Vào Railway Dashboard
2. Click **"New Project"**
3. Chọn **"Empty Project"**
4. Sau đó vào Settings → **"Connect Repo"**
5. Chọn repo của bạn

### 5. Kiểm tra .git folder

Đảm bảo folder `.git` tồn tại trong project:

```bash
# Kiểm tra
ls -la .git

# Nếu không có, init lại
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/username/repo.git
git push -u origin main
```

### 6. Thử deploy từ branch khác

Nếu đang dùng `master`, thử đổi sang `main`:

```bash
git checkout -b main
git push origin main
```

Rồi chọn branch `main` trong Railway settings.

## Nếu vẫn không được:

### ➡️ Dùng Railway CLI (Khuyến nghị nhất)

Xem file `DEPLOY_RAILWAY_CLI.md` để deploy trực tiếp từ local, bỏ qua GitHub hoàn toàn.

```bash
# Cài Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### ➡️ Hoặc thử Render.com

Render có UI đơn giản hơn và ít lỗi GitHub hơn:

1. Vào: https://render.com/
2. Sign up với GitHub
3. New → Web Service
4. Connect repository
5. Chọn Docker
6. Deploy

Nhưng lưu ý: Render có thể bị lỗi "proxies" nếu dùng langchain (project này đã remove langchain rồi nên OK).
