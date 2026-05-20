from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
PDF_EXTS = {".pdf"}


@dataclass
class ImagePayload:
    """送入 VLM 的单张图片。"""
    data_url: str          # data:image/png;base64,xxxx
    page_index: int        # 0 起；非 PDF 固定为 0
    mime: str = "image/png"
    width: int = 0
    height: int = 0


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS | PDF_EXTS


def encode_image_file(path: Path, max_side: int = 1280) -> ImagePayload:
    """读取图片文件、可选缩放、转为 data URL。"""
    import cv2
    import numpy as np

    # 使用 np.fromfile + cv2.imdecode 处理中文路径
    img_array = np.fromfile(str(path), dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"无法读取图片文件: {path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    scale = min(1.0, max_side / float(max(w, h)))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)
    is_success, buf = cv2.imencode(".png", img)
    if not is_success:
        raise ValueError("无法编码图片为 PNG")
    b64 = base64.b64encode(buf).decode("ascii")
    return ImagePayload(
        data_url=f"data:image/png;base64,{b64}",
        page_index=0,
        mime="image/png",
        width=img.shape[1],
        height=img.shape[0],
    )


def render_pdf_to_images(path: Path, dpi: int = 150, max_side: int = 1280, max_pages: int = 6) -> List[ImagePayload]:
    """扫描型 PDF 直接渲染为图片页，交给远程 VLM 解析。"""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("缺少依赖 PyMuPDF，请 pip install pymupdf") from exc

    import cv2
    import numpy as np

    images: List[ImagePayload] = []
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(str(path)) as doc:
        for page_idx, page in enumerate(doc):
            if page_idx >= max_pages:
                break
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            # PyMuPDF 返回 RGB 字节，转为 numpy 数组再用 cv2 编码
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            # cv2 需要 BGR，转回 RGB
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            h, w = img.shape[:2]
            scale = min(1.0, max_side / float(max(w, h)))
            if scale < 1.0:
                img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LANCZOS4)
            is_success, buf = cv2.imencode(".png", img)
            if not is_success:
                raise ValueError("无法编码 PDF 页面为 PNG")
            b64 = base64.b64encode(buf).decode("ascii")
            images.append(
                ImagePayload(
                    data_url=f"data:image/png;base64,{b64}",
                    page_index=page_idx,
                    mime="image/png",
                    width=img.shape[1],
                    height=img.shape[0],
                )
            )
    return images


def file_to_images(path: Path) -> List[ImagePayload]:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return [encode_image_file(path)]
    if suffix in PDF_EXTS:
        return render_pdf_to_images(path)
    raise ValueError(f"不支持的文件类型: {suffix}")
