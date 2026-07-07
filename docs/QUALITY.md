# 质量门禁

## 当前阶段检查

在可运行骨架创建前，项目质量门禁先覆盖：

- Python 脚本语法检查。
- 文档和配置文件 UTF-8 读取检查。
- `.env` 等本地敏感配置文件误提交风险检查。
- 已暴露过的模型 Key 字符串扫描。

运行：

```powershell
& 'C:\Users\liyu1\AppData\Local\Programs\Python\Python311\python.exe' scripts\quality_check.py
```

## 后续骨架完成后补充

后端：

```powershell
cd backend
python -m compileall app
python -m pytest
```

前端：

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
```

## 提交前检查

```powershell
git status --short
& 'C:\Users\liyu1\AppData\Local\Programs\Python\Python311\python.exe' scripts\quality_check.py
```

