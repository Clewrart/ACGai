# ACG 同人二创作者 AI 鉴定与作品权益试水系统

这是一个本地可运行的 Flask MVP，用于 ACG 同人图、同人文、漫画页、约稿稿件的：

1. 作品登记存证
2. 图片近似重复检测
3. 文本相似/洗稿预警
4. AI 疑似度辅助复核

注意：本项目不能作为法律定责工具，也不能把 AI 疑似度当成“定罪证据”。它更适合作为创作者自用的早期预警、存证与人工复核入口。

## 启动

```bash
cd acg_ai_rights_web
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

浏览器打开：

```text
http://127.0.0.1:5000
```

## 页面

- `/` 首页
- `/register` 登记作品
- `/check` 鉴定/核验
- `/works` 已登记作品库

## 数据位置

- 上传文件：`uploads/`
- SQLite 数据库：`data/acg_rights.db`

## 适合场景

- 同人图被搬运、重绘、滤镜处理后的相似核验
- 同人文被改写、洗稿后的相似预警
- 约稿稿件交付后，登记作品指纹
- AI 生成/AI 辅助痕迹作为“人工复核提示”

## 生产化改造方向

- 登录注册、创作者身份认证
- 作品时间戳与第三方可信存证
- C2PA / Content Credentials 元数据读取
- CLIP / DINOv2 图像语义相似度
- OCR 后漫画页台词相似度
- MinHash / 向量数据库批量检索
- 管理员人工复核工作台
