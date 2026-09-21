# 说车三岁 API

这是车辆档案的 FastAPI 后端。开发时可以使用 SQLite 和本地文件；部署时将 `DATABASE_URL` 指向 PostgreSQL，并将图片存储配置为 Cloudflare R2 或其他 S3 兼容对象存储。

## 本地运行

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：`http://127.0.0.1:8000/health`

## 部署前环境变量

- `DATABASE_URL`：PostgreSQL 连接串；不要在 Render 上使用默认 SQLite 保存正式数据。
- `PUBLIC_BASE_URL`：后端对外访问地址，例如 `https://你的服务.onrender.com`。
- `R2_ENDPOINT`、`R2_BUCKET`、`R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`：R2 S3 API 配置。
- `R2_PUBLIC_BASE_URL`：R2 公共访问域名；留空时由后端生成临时访问地址。

## Render

项目根目录里的 `render.yaml` 已经准备好基础服务定义。连接代码仓库后使用 Blueprint 创建服务，并在 Render 控制台填写上述环境变量。

### 从 GitHub 部署

1. 将项目根目录上传到 GitHub 仓库，确保根目录的 `render.yaml` 一起提交。
2. 打开 Render Dashboard，选择 `New` → `Blueprint`，连接这个 GitHub 仓库。
3. Render 会读取根目录的 `render.yaml`，创建名为 `shuoche-sansui-api` 的 Python Web Service。
4. 在服务的 `Environment` 中填写 `DATABASE_URL`、`PUBLIC_BASE_URL` 和 R2 相关变量，然后重新部署。
5. 打开 `https://你的服务.onrender.com/health`，返回 `{"ok":true,...}` 后，说明后端已上线。
6. 将小程序 `app.js` 的 `API_BASE_URL` 改成 `https://你的服务.onrender.com/api`，再在微信开发者工具中重新编译。

Render 的本地磁盘不适合保存正式数据，因此正式环境必须使用 PostgreSQL 保存车辆记录，并使用 R2 保存图片；不要把 `backend/data/` 里的 SQLite 文件或上传目录提交到仓库。
