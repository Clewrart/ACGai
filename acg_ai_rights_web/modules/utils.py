import hashlib
from pathlib import Path
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_TEXT_EXT = {".txt", ".md"}


def ensure_dirs():
    Path("uploads").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def safe_save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    original = file_storage.filename
    name = secure_filename(original)
    if not name:
        name = "upload.bin"

    suffix = Path(name).suffix.lower()
    target_dir = Path("uploads")
    target_dir.mkdir(exist_ok=True)

    base = Path(name).stem[:80]
    candidate = target_dir / name
    i = 1
    while candidate.exists():
        candidate = target_dir / f"{base}_{i}{suffix}"
        i += 1

    file_storage.save(candidate)
    return str(candidate)


def is_image_path(path):
    return Path(path).suffix.lower() in ALLOWED_IMAGE_EXT


def is_text_path(path):
    return Path(path).suffix.lower() in ALLOWED_TEXT_EXT


def read_text_file(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")
