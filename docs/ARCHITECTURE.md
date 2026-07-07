# 产品图片 AI 识别系统架构

## 技术栈

- 前端：React + Vite + TypeScript
- UI：Tailwind CSS + lucide-react
- 后端：Python FastAPI
- AI 调用：阿里百炼 / DashScope 兼容接口
- 向量模型：`qwen3-vl-embedding`
- 多模态模型：`qwen3-vl-plus`
- 图片处理：Pillow
- 数据库：SQLite
- 后台任务：FastAPI 内置 worker + asyncio 队列
- 向量索引：本地文件 / SQLite + numpy 相似度计算
- 部署：nginx + systemd

## 总体结构

```text
浏览器前端
  ├─ 单张识别页面
  ├─ 批量任务页面
  ├─ 模板库状态
  └─ 模型设置
        │
        ▼
FastAPI 后端
  ├─ API 路由层
  ├─ 识别服务
  ├─ 批量任务服务
  ├─ 模板库服务
  ├─ 模型配置服务
  └─ AI 网关服务
        │
        ├─ SQLite
        ├─ 本地模板图片
        ├─ 本地向量索引
        └─ 阿里 DashScope / Qwen VL
```

## 目录结构

```text
ImageRecognition/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  │  ├─ health.py
│  │  │  ├─ status.py
│  │  │  ├─ recognition.py
│  │  │  ├─ jobs.py
│  │  │  ├─ settings.py
│  │  │  └─ admin.py
│  │  ├─ core/
│  │  │  ├─ config.py
│  │  │  ├─ database.py
│  │  │  ├─ errors.py
│  │  │  └─ security.py
│  │  ├─ features/
│  │  │  ├─ templates/
│  │  │  ├─ recognition/
│  │  │  ├─ jobs/
│  │  │  └─ settings/
│  │  ├─ services/
│  │  │  ├─ qwen_client.py
│  │  │  ├─ image_store.py
│  │  │  └─ vector_store.py
│  │  └─ main.py
│  ├─ data/
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  │  ├─ features/
│  │  │  ├─ recognition/
│  │  │  ├─ jobs/
│  │  │  ├─ status/
│  │  │  └─ settings/
│  │  ├─ shared/
│  │  ├─ App.tsx
│  │  └─ main.tsx
│  └─ package.json
├─ tools/
├─ docs/
└─ deploy/
```

## 数据目录

```text
backend/data/
├─ app.db
├─ uploads/
├─ template_images/
├─ product_templates/
│  ├─ manifest.json
│  └─ manifest.csv
└─ vector_index.json
```

## SQLite 表

### jobs

- `id`
- `status`
- `total`
- `completed`
- `failed`
- `created_at`
- `updated_at`

### job_items

- `id`
- `job_id`
- `filename`
- `upload_path`
- `status`
- `result_json`
- `error_message`
- `created_at`
- `updated_at`

### model_settings

- `id`
- `embedding_model`
- `vl_model`
- `enable_vl_rerank`
- `low_confidence_threshold`
- `updated_at`

## API 草稿

- `GET /api/health`
- `GET /api/status`
- `POST /api/recognize`
- `POST /api/jobs`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/results`
- `GET /api/jobs/{job_id}/export`
- `GET /api/settings/models`
- `PUT /api/settings/models`
- `POST /api/settings/models/reset`
- `POST /api/admin/rebuild-index`

## 核心数据流

### 单张识别

```text
上传图片
→ 保存到 uploads
→ 读取当前模型配置
→ 调用 qwen3-vl-embedding 生成图片向量
→ 与模板向量索引计算相似度
→ Top K 结果
→ 低置信度时调用 qwen3-vl-plus 复核
→ 返回结果
```

### 文件夹批量识别

```text
选择文件夹
→ 前端批量上传图片
→ 后端创建 job 和 job_items
→ worker 后台逐张处理
→ 每张图写入识别结果
→ 前端轮询 job 状态
→ 完成后导出 CSV / Excel
```

### 模型设置

```text
前端修改模型名
→ 写入 SQLite model_settings
→ 新任务读取新配置
→ 如果 embedding 模型变化，提示重建索引
```

## 架构约束

- 前端不接触 API Key。
- AI 调用只通过 `services/qwen_client.py`。
- 批量识别不直接在请求线程里跑，必须进入 worker。
- 模板抽取、向量索引、在线识别分离。
- 第一版 worker 单进程单机运行，后续可替换为 Celery/RQ。
- 每个功能保持在 `src/features` 或 `backend/app/features` 对应边界内。

