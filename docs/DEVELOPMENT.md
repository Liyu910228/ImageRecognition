# 开发规范

## 基本原则

- 需求、PRD、架构、状态文档要和代码同步更新。
- 每次开发只推进一个可验证的小切片。
- 功能代码放在对应 feature 边界内，避免跨功能直接引用内部实现。
- API Key、Token、服务器密码等敏感信息只放环境变量，不写入代码、文档样例真实值或日志。
- 复杂逻辑先写清楚输入、输出和边界，再实现。

## 后端规范

### 语言与框架

- Python 3.11+
- FastAPI
- SQLite
- Pillow / numpy 用于图片和向量处理

### 目录边界

- `backend/app/api/`：只放 HTTP 路由和请求响应组装。
- `backend/app/core/`：配置、数据库、安全、通用错误。
- `backend/app/features/templates/`：模板库抽取、manifest 管理。
- `backend/app/features/recognition/`：单张识别、匹配逻辑。
- `backend/app/features/jobs/`：批量任务、worker、结果导出。
- `backend/app/features/settings/`：模型配置。
- `backend/app/services/`：外部服务和基础设施适配，如 Qwen、图片存储、向量索引。

### 命名

- Python 文件名使用 `snake_case.py`。
- 函数、变量使用 `snake_case`。
- 类名使用 `PascalCase`。
- API schema 使用明确后缀：`RecognizeRequest`、`RecognizeResponse`。

### 注释

- 只在复杂流程、外部 API 兼容、非显然安全约束处写注释。
- 不写“给变量赋值”这类无信息量注释。

### 错误处理

- 上传格式错误返回 400。
- 模板索引缺失返回 409，并提示重建索引。
- 模型 Key 缺失返回 500/配置错误，并隐藏 Key。
- 模型接口失败返回可读错误和请求追踪信息，不泄露敏感信息。

## 前端规范

### 技术

- React + Vite + TypeScript
- Tailwind CSS
- lucide-react 图标

### 目录边界

- `frontend/src/features/recognition/`：单张识别 UI 和逻辑。
- `frontend/src/features/jobs/`：批量任务 UI 和轮询逻辑。
- `frontend/src/features/status/`：模板库状态。
- `frontend/src/features/settings/`：模型设置。
- `frontend/src/shared/`：通用 API client、组件、类型、工具。

### 设计约束

- 第一屏直接是工作台，不做营销落地页。
- 业务工具风格：信息清晰、操作密度适中、状态明确。
- 图片上传、任务进度、候选结果必须有清楚的 loading / success / error 状态。
- 不在页面显示模型 Key。

### 命名

- React 组件使用 `PascalCase.tsx`。
- hooks 使用 `useXxx.ts`。
- 类型放在 feature 内 `types.ts`，跨功能类型放 `shared/types/`。

## API 约定

- 成功响应使用 JSON。
- 错误响应统一包含：

```json
{
  "error": "可读错误信息",
  "code": "ERROR_CODE"
}
```

- 批量任务状态值：
  - `pending`
  - `running`
  - `completed`
  - `failed`
  - `partial_failed`

## 环境变量

服务端从 `.env` 或系统环境读取：

```env
DASHSCOPE_API_KEY=
QWEN_EMBEDDING_MODEL=qwen3-vl-embedding
QWEN_VL_MODEL=qwen3-vl-plus
UPLOAD_MAX_MB=10
WORKER_CONCURRENCY=1
ADMIN_TOKEN=
```

`.env` 不提交版本记录。仓库只保留 `.env.example`。

## 质量检查

后端建议命令：

```powershell
cd backend
python -m compileall app
python -m pytest
```

前端建议命令：

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
```

部署前检查：

```powershell
git status --short
```

## AI 协作约束

- 改动超过 3 个文件时，先说明原因。
- 遇到同类编译、类型或 lint 错误，两次修复失败后停止猜测，进入根因分析。
- 每完成一个功能切片，必须提供自动检查、人工验证步骤和改动摘要。

