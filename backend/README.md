# 说车三岁 API

这是车辆档案的 FastAPI 后端。开发时可以使用 SQLite 和本地文件；正式环境使用 PostgreSQL 和私有 S3 兼容对象存储。本次部署使用 Supabase 保存数据库和图片，Render 运行 Python API。

## 当前部署

- 公网服务：`https://shuoche-sansui-api.onrender.com`。
- 健康检查：`https://shuoche-sansui-api.onrender.com/health`，正常返回 `{"ok":true,"storage":"s3"}`。
- 小程序 `app.js` 已切换为公网 API；本地调试时可改回 `http://127.0.0.1:8000/api`。
- 公网后端上线不等于小程序已发布；微信公众平台的服务器域名配置和真机验证需另行完成。

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

- `APP_ENV=production`：正式环境禁止缺少配置时回退到本地存储。
- `DATABASE_URL`：Supabase 的 Session pooler PostgreSQL 连接串，密码需进行 URL 编码，附加 `?sslmode=require`。后端会自动选择已安装的 `psycopg` 驱动。
- `API_AUTH_REQUIRED`：是否要求小程序用户输入访问口令；当前产品为 `false`，用户可以直接录入。
- `API_ACCESS_TOKEN`：仅存于部署平台的服务器内部密钥，用于生成图片临时链接；不写入源码，也不需要提供给小程序用户。
- `PUBLIC_BASE_URL`：后端 HTTPS 地址；在 Render 可以留空，自动使用平台的 `RENDER_EXTERNAL_URL`。
- `R2_ENDPOINT`、`R2_BUCKET`、`R2_ACCESS_KEY_ID`、`R2_SECRET_ACCESS_KEY`：兼容原 R2 变量名，也可以填写 Supabase S3 配置。密钥仅供后端使用。
- `R2_REGION`：Supabase 使用控制台显示的区域；本项目为 `ap-southeast-1`。Cloudflare R2 使用 `auto`。
- `R2_PUBLIC_BASE_URL`：正式部署留空，图片桶保持私有。后端返回限时图片链接，不在 URL 中暴露访问口令。

当 `API_AUTH_REQUIRED=true` 时，车辆资料和图片的读写需要访问口令；当前关闭用户口令后，车辆资料接口可以直接使用，图片仍通过服务端生成临时链接。`/health` 无需口令，可用于部署健康检查。图片每张最多 10 MB。

## Render

项目根目录里的 `render.yaml` 已经准备好基础服务定义。连接代码仓库后使用 Blueprint 创建服务，并在 Render 控制台填写上述环境变量。

### 从 GitHub 部署

1. 将项目根目录上传到 GitHub 仓库，确保根目录的 `render.yaml` 一起提交。
2. 打开 Render Dashboard，选择 `New` → `Blueprint`，连接这个 GitHub 仓库。
3. Render 会读取根目录的 `render.yaml`，创建名为 `shuoche-sansui-api` 的 Python Web Service。
4. 在服务的 `Environment` 中填写数据库、私有 S3 存储和服务器内部密钥。将 `API_AUTH_REQUIRED` 设为 `false`。实例选择 Free，区域选择 Singapore，健康检查路径填写 `/health`。
5. 打开 `https://你的服务.onrender.com/health`，返回 `{"ok":true,...}` 后，说明后端已上线。
6. 将小程序 `app.js` 的 `API_BASE_URL` 改成 `https://你的服务.onrender.com/api`，再在微信开发者工具中重新编译。

Render 的本地磁盘不适合保存正式数据，因此正式环境必须使用 PostgreSQL 保存车辆记录，并使用私有对象存储保存图片；不要把 `backend/data/` 里的 SQLite 文件或上传目录提交到仓库。

## 查看已收集的资料

- Supabase 项目：`phcnncsnpcxjzwmsjmxo`，组织「说车三岁」，项目 `shuoche-sansui`。
- 文案与车辆档案：项目的 Table Editor → `public.vehicle_records`；`selling_points` 是卖点文案，`vehicle_photos` 保存九宫格位置和图片 ID。
- 照片：Storage → Files → `vehicle-images` → `vehicles/车辆ID/`。这是私有桶，没有公开读写策略。
- 数据库已关闭 Data API，启用新表自动 RLS；小程序通过 FastAPI 访问，不直接使用 Supabase 数据库密钥。
- 本机部署密钥位于 `~/.config/shuoche-sansui/deploy-secrets.json`，不在 Git 仓库和小程序包中。不要上传或分享该文件。

公网 API 上线与微信小程序发布是两个步骤。切换 HTTPS 地址后，还需在微信公众平台配置允许的服务器域名并进行真机验证，不能把开发者工具里关闭域名校验当作正式发布配置。
