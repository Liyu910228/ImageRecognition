# 验收清单

## 自动验证

在项目根目录运行：

```powershell
& 'C:\Users\liyu1\AppData\Local\Programs\Python\Python311\python.exe' -m compileall backend\app scripts tools
& 'C:\Users\liyu1\AppData\Local\Programs\Python\Python311\python.exe' scripts\quality_check.py
cd frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
```

期望结果：

- Python 编译无错误。
- 质量门禁显示 `Quality check passed`。
- 前端 typecheck、lint、build 全部通过。

## 管理员验收

登录：

- 账号：`admin`
- 密码：`admin`

检查项：

- 管理员只看到模板库和模型设置。
- 模板库可上传多个 `.xlsx` 文件，上传后显示“已构建完成”。
- 模板库单个文件可删除，删除后会自动重建剩余模板索引。
- 模型设置可修改向量模型、多模态模型、Top 候选数量、模型超时时间、图片提示词。
- 图片提示词为空时，后端自动使用雪花品牌专用默认提示词。
- 前端临时 Key 不保存到后端；保存到后端的 Key 留空时保持原后端 Key 不变。

## 业务员验收

登录：

- 账号：`root`
- 密码：`2345`

检查项：

- 业务员只看到上传识别工作台。
- 单张图片上传后可预览，点击开始识别后显示最佳结果和 Top 5 候选。
- 粘贴图片链接后点击链接识别，可正常展示结果。
- 选择文件夹可弹出文件夹选择，自动过滤 JPG、PNG、WebP，并逐张识别。
- 表格批量上传链接可读取 `.xlsx` 的“照片链接”字段，并生成链接批量队列。
- 批量结果表显示文件、状态、产品编码、产品名称、瓶/听/箱、相似度、操作。
- 单条“重试”可重新识别该行。
- “批量重试”只重试失败和未命中的记录。
- “导出Excel”可导出批量结果，导出列只有：来源、状态、产品编码、产品名称、瓶/听/箱、相似度。

## 边界场景

- 未配置 Key 时，识别来源应显示已退回本地视觉。
- Qwen 超过管理员设置的超时时间时，应显示 Qwen 超时并退回本地视觉。
- 低相似度结果应提示人工复核。
- 表格没有“照片链接”字段时，应提示读取失败。
- 图片链接无法下载、超过大小限制或不是图片时，应提示失败。

