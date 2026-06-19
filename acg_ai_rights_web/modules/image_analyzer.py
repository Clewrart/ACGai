import math
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image, ImageFilter

from .utils import sha256_file


def _normalize_score(x, lo, hi):
    if hi <= lo:
        return 0
    return max(0, min(100, int((x - lo) / (hi - lo) * 100)))


def analyze_image(path):
    """
    面向 ACG 插画/漫画页的轻量图片分析。
    这里的 ai_risk_score 只是“技术复核提示”，不是定责结论。
    """
    path = Path(path)

    with Image.open(path) as img:
        img = img.convert("RGB")
        width, height = img.size

        phash_hex = str(imagehash.phash(img, hash_size=16))
        avg_hash_hex = str(imagehash.average_hash(img, hash_size=16))
        dhash_hex = str(imagehash.dhash(img, hash_size=16))

        entropy = float(img.entropy())

        gray = img.convert("L").resize((512, 512))
        arr = np.asarray(gray).astype(np.float32) / 255.0

        # 高频能量占比：AI 图、过度锐化图、压缩图都可能异常，但不是绝对证据
        fft = np.fft.fftshift(np.fft.fft2(arr))
        mag = np.abs(fft)
        h, w = mag.shape
        cy, cx = h // 2, w // 2
        yy, xx = np.ogrid[:h, :w]
        dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        high_mask = dist > min(h, w) * 0.28
        high_freq_ratio = float(mag[high_mask].sum() / (mag.sum() + 1e-8))

        # 边缘密度：漫画线稿、厚涂、AI 图都会影响它，所以只做辅助特征
        edge = gray.filter(ImageFilter.FIND_EDGES)
        edge_arr = np.asarray(edge).astype(np.float32) / 255.0
        edge_density = float((edge_arr > 0.18).mean())

        # 色彩复杂度
        small = img.resize((128, 128))
        colors = small.getcolors(maxcolors=128 * 128)
        color_count = len(colors) if colors else 128 * 128
        color_complexity = color_count / (128 * 128)

        exif = {}
        try:
            exif = img.getexif() or {}
        except Exception:
            exif = {}

        info_keys = list(getattr(img, "info", {}).keys())

    # 轻量启发式评分：为了试水，不做“百分百 AI”判断
    risk = 0
    reasons = []

    if len(exif) == 0:
        risk += 10
        reasons.append("未发现 EXIF 信息；对同人图不罕见，只能作为弱提示")

    if high_freq_ratio > 0.42:
        risk += 22
        reasons.append("高频能量偏高，可能存在生成纹理、锐化或压缩痕迹")
    elif high_freq_ratio < 0.18:
        risk += 10
        reasons.append("高频细节偏低，可能经过强降噪、缩放或平滑处理")

    if 0.20 <= edge_density <= 0.38:
        risk += 10
        reasons.append("边缘密度处于需要复核区间，建议人工查看线条和细节一致性")

    if entropy > 7.6:
        risk += 10
        reasons.append("图像熵较高，可能存在复杂噪声或纹理混杂")
    elif entropy < 4.2:
        risk += 8
        reasons.append("图像熵较低，可能是大面积平滑或简单色块")

    if color_complexity > 0.75:
        risk += 8
        reasons.append("颜色复杂度较高，建议检查背景纹理和局部细节")

    risk = max(0, min(100, risk))

    if risk < 30:
        level = "低"
    elif risk < 60:
        level = "中"
    else:
        level = "高"

    return {
        "kind": "image",
        "file_sha256": sha256_file(path),
        "phash_hex": phash_hex,
        "avg_hash_hex": avg_hash_hex,
        "dhash_hex": dhash_hex,
        "width": width,
        "height": height,
        "entropy": round(entropy, 4),
        "high_freq_ratio": round(high_freq_ratio, 4),
        "edge_density": round(edge_density, 4),
        "color_complexity": round(color_complexity, 4),
        "exif_count": len(exif),
        "metadata_keys": info_keys,
        "ai_risk_score": risk,
        "ai_risk_level": level,
        "risk_reasons": reasons,
    }


def hamming_hex(a, b):
    if not a or not b:
        return None
    try:
        ia = int(a, 16)
        ib = int(b, 16)
    except ValueError:
        return None
    return (ia ^ ib).bit_count()


def image_match_label(distance):
    if distance is None:
        return "无法比较"
    if distance <= 8:
        return "高度相似，可能是同图、裁切、压缩、调色或轻微改图"
    if distance <= 18:
        return "较相似，建议人工复核构图、角色姿态、背景元素"
    if distance <= 32:
        return "有一定相似，可能只是风格或构图接近"
    return "相似度低"
