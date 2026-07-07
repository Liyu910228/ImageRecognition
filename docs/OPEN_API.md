# 开放接口说明

## 鉴权

业务系统调用开放接口时，需要在请求头中携带 Bearer Token。

```http
Authorization: Bearer <OPEN_API_TOKEN>
```

## 单图识别

```http
POST /api/open/recognitions
Content-Type: application/json
Authorization: Bearer <OPEN_API_TOKEN>
```

请求体：

```json
{
  "image_url": "https://example.com/image.jpg",
  "trace_id": "BUSINESS-TRACE-001",
  "hints": "",
  "model_profile": "default"
}
```

`model_profile` 支持：

| 值 | 说明 |
| --- | --- |
| `default` | 使用管理员页面配置的默认任务模型策略 |
| `high_accuracy` | 高准确率模式：同一模型分三轮识别品牌/包装、文字 OCR、最终判断，再融合结果 |
| `qwen3-vl-plus` | 直接指定某个 DashScope 兼容视觉模型 |
| `qwen3-vl-plus|备用模型名` | 主模型 10 秒无结果或报错时，自动切备用模型 |
| `high_accuracy:模型A,模型B,模型C` | 多模型复核：A 识别品牌/包装，B 做文字 OCR，C 做最终判断 |

模型名支持平台前缀：

| 写法 | 含义 |
| --- | --- |
| `aliyun:qwen3-vl-plus` | 使用阿里 DashScope 平台模型 |
| `volc:ep-xxx` | 使用火山 Ark 平台模型或接入点 ID |
| `qwen3-vl-plus` | 不写前缀时使用管理员页面配置的默认模型平台 |

返回体：

```json
{
  "trace_id": "BUSINESS-TRACE-001",
  "status": "命中",
  "product_code": "31010030047000000",
  "product_name": "雪花清爽10度500ml听6*2塑膜六连包无纺布提手纸箱",
  "package_type": "箱",
  "score": 0.904,
  "template_image_url": "/template-images/example.jpg",
  "matched_snow_brands": ["雪花"],
  "matched_competitor_brands": [],
  "review_required": false,
  "model_profile": "default",
  "raw": {}
}
```

## 状态检查

```http
GET /api/open/status
```

返回开放接口 Token 是否配置，仅展示脱敏 Token。

## 批量任务

创建批量任务：

```http
POST /api/open/batch-jobs
Content-Type: application/json
Authorization: Bearer <OPEN_API_TOKEN>
```

请求体：

```json
{
  "items": [
    {
      "image_url": "https://example.com/1.jpg",
      "trace_id": "CRM-ROW-000001"
    }
  ],
  "hints": "",
  "model_profile": "default"
}
```

批量任务同样支持上述 `model_profile` 规则。每条识别结果和管理员日志会记录 `model_calls`，包含每个模型角色、模型名、耗时、状态和输出摘要。

业务员页面不展示模型选择，默认使用管理员页面的“默认任务模型策略”。管理员可以在“多模型配置”中维护策略名，例如：

```text
high_accuracy=aliyun:qwen3-vl-plus,volc:ep-xxx,aliyun:qwen3-vl-plus
fallback=aliyun:qwen3-vl-plus|volc:ep-xxx
```

也可以使用 `image_urls` 快速传纯链接数组：

```json
{
  "image_urls": [
    "https://example.com/1.jpg",
    "https://example.com/2.jpg"
  ]
}
```

返回：

```json
{
  "job_id": "JOB20260522101010-ABCDEF12",
  "status": "pending",
  "total": 2,
  "processed": 0,
  "success": 0,
  "no_match": 0,
  "failed": 0,
  "progress": 0
}
```

查询任务进度：

```http
GET /api/open/batch-jobs/{job_id}
Authorization: Bearer <OPEN_API_TOKEN>
```

分页查询结果：

```http
GET /api/open/batch-jobs/{job_id}/items?page=1&pageSize=100&status=all&q=
Authorization: Bearer <OPEN_API_TOKEN>
```

`status` 支持：`all`、`命中`、`未命中`、`失败`。

## 上传 Excel 创建批量任务

如果业务系统已经有一份包含“照片链接”列的 `.xlsx`，可以直接上传表格创建任务。

```http
POST /api/open/batch-jobs/workbook
Authorization: Bearer <OPEN_API_TOKEN>
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| file | 是 | `.xlsx` 文件，系统会自动查找“照片链接”列 |
| hints | 否 | 人工提示关键词 |
| model_profile | 否 | 模型配置名，默认 `default` |
| callback_url | 否 | 回调地址，第一版暂存字段，后续启用 |

curl 示例：

```bash
curl -X POST "http://8.160.163.200:18086/api/open/batch-jobs/workbook" \
  -H "Authorization: Bearer <OPEN_API_TOKEN>" \
  -F "file=@CRM系统拜访照片.xlsx" \
  -F "model_profile=default"
```

返回与普通批量任务一致，并额外返回源文件名和识别到的链接字段：

```json
{
  "job_id": "JOB20260522101010-ABCDEF12",
  "status": "pending",
  "total": 100000,
  "processed": 0,
  "source_filename": "CRM系统拜访照片.xlsx",
  "source_field": "照片链接"
}
```

上传表格创建的任务会自动把每张图的 `trace_id` 设置为 `Sheet1-第2行` 这类格式，方便和原表格对账。
