from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash

from modules.db import init_db, insert_work, list_works
from modules.image_analyzer import analyze_image
from modules.text_analyzer import analyze_text
from modules.similarity import compare_image_to_registry, compare_text_to_registry
from modules.utils import (
    ensure_dirs, safe_save_upload, is_image_path, is_text_path,
    read_text_file, sha256_text, sha256_file
)

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"


@app.before_request
def boot():
    ensure_dirs()
    init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/works")
def works():
    rows = list_works(limit=200)
    return render_template("works.html", works=rows)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    title = request.form.get("title", "").strip()
    creator_alias = request.form.get("creator_alias", "").strip()
    work_type = request.form.get("work_type", "image").strip()
    platform_url = request.form.get("platform_url", "").strip()
    tags = request.form.get("tags", "").strip()
    declaration = request.form.get("declaration", "").strip()
    text_content = request.form.get("text_content", "").strip()
    file = request.files.get("file")

    if not title or not creator_alias:
        flash("标题和创作者昵称必填。", "error")
        return redirect(url_for("register"))

    saved_path = safe_save_upload(file)
    features = {}
    phash_hex = None
    simhash_hex = None
    text_sample = None
    sha256 = None
    file_name = None

    if saved_path:
        file_name = Path(saved_path).name
        if is_image_path(saved_path):
            features = analyze_image(saved_path)
            phash_hex = features.get("phash_hex")
            sha256 = features.get("file_sha256")
            work_type = "image"
        elif is_text_path(saved_path):
            text_content = read_text_file(saved_path)
            features = analyze_text(text_content)
            simhash_hex = features.get("simhash_hex")
            sha256 = features.get("text_sha256")
            text_sample = text_content[:10000]
            work_type = "text"
        else:
            sha256 = sha256_file(saved_path)
            features = {"kind": "file", "note": "暂不支持该文件类型的 AI 疑似度分析，但已保存 SHA256。"}
    elif text_content:
        features = analyze_text(text_content)
        simhash_hex = features.get("simhash_hex")
        sha256 = features.get("text_sha256")
        text_sample = text_content[:10000]
        work_type = "text"
    else:
        flash("请上传图片/文本文件，或粘贴同人文本。", "error")
        return redirect(url_for("register"))

    work_id = insert_work({
        "title": title,
        "creator_alias": creator_alias,
        "work_type": work_type,
        "platform_url": platform_url,
        "tags": tags,
        "declaration": declaration,
        "file_path": saved_path,
        "file_name": file_name,
        "sha256": sha256,
        "phash_hex": phash_hex,
        "simhash_hex": simhash_hex,
        "text_sample": text_sample,
        "features": features,
    })

    flash(f"登记成功，作品编号 #{work_id}。", "success")
    return redirect(url_for("works"))


@app.route("/check", methods=["GET", "POST"])
def check():
    if request.method == "GET":
        return render_template("check.html")

    text_content = request.form.get("text_content", "").strip()
    file = request.files.get("file")
    saved_path = safe_save_upload(file)

    image_report = None
    text_report = None
    image_matches = []
    text_matches = []

    if saved_path and is_image_path(saved_path):
        image_report = analyze_image(saved_path)
        image_matches = compare_image_to_registry(image_report.get("phash_hex"), top_k=10)

    elif saved_path and is_text_path(saved_path):
        text_content = read_text_file(saved_path)
        text_report = analyze_text(text_content)
        text_matches = compare_text_to_registry(text_report.get("simhash_hex"), text_content, top_k=10)

    elif text_content:
        text_report = analyze_text(text_content)
        text_matches = compare_text_to_registry(text_report.get("simhash_hex"), text_content, top_k=10)

    else:
        flash("请上传图片/文本文件，或粘贴需要核验的文本。", "error")
        return redirect(url_for("check"))

    return render_template(
        "result.html",
        image_report=image_report,
        text_report=text_report,
        image_matches=image_matches,
        text_matches=text_matches,
    )


if __name__ == "__main__":
    ensure_dirs()
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
