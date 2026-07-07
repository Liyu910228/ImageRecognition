# 产品图片识别模板库

这个项目现在包含两步流程：

1. 从 Excel 产品 6 面图中抽取模板库。
2. 用户上传图片后，匹配出对应的产品编码、产品名称、瓶/听/箱和图片视角。

## 生成模板库

```powershell
& 'C:\Users\liyu1\AppData\Local\Programs\Python\Python311\python.exe' tools\extract_excel_templates.py --output outputs\product_templates
```

输出：

- `outputs/product_templates/manifest.json`：程序使用的结构化模板库
- `outputs/product_templates/manifest.csv`：方便人工检查的明细表
- `outputs/product_templates/images/`：从 Excel 抽取出的模板图片

当前两份 Excel 已抽取出 112 个产品记录、731 张模板图。

## 匹配上传图片

```powershell
& 'C:\Users\liyu1\AppData\Local\Programs\Python\Python311\python.exe' tools\match_uploaded_image.py "你的上传图片.jpeg" --top-k 5
```

返回字段：

- `score`：相似度分数，越接近 1 越像
- `product_code`：产品编码
- `product_name`：产品名称
- `package_type`：瓶、听、箱
- `view`：正面图、背面图、侧面图、顶图、底图或立体图
- `image_path`：命中的模板图片

## AI 版本建议

当前 `match_uploaded_image.py` 是本地可运行的基线：感知哈希 + 颜色直方图。它适合先验证 Excel 模板库是否抽取正确。

正式上线建议替换为多模态 embedding 检索：

- 离线：对 `manifest.json` 里的每张模板图生成图像向量，存入向量库。
- 在线：用户上传图片后生成图像向量，检索 Top K 模板。
- 输出：命中模板所属行就是产品编码、产品名称、瓶/听/箱；命中列就是正面/背面/侧面/顶/底/立体图。
- 兜底：如果 Top 1 分数低或 Top K 接近，返回“疑似”并要求人工确认。

如果图片里产品编码或名称很清楚，可以再加 OCR/视觉大模型先读文字，然后用产品编码、名称过滤候选集，再做图片相似度匹配，准确率会更稳。
