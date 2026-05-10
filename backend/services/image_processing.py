"""
OpenCV pipeline: grayscale, denoise, threshold, perspective correction, enhancement.
"""
from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def _imread_path(path: Path) -> np.ndarray | None:
    """
    Read BGR image. Uses bytes from disk (Unicode-safe on Windows; np.fromfile/cv2.imread are not).
    Falls back to Pillow if OpenCV's decoder rejects the file (e.g. some JPEG/EXIF variants).
    """
    data = path.read_bytes()
    if not data:
        return None
    arr = np.frombuffer(data, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is not None:
        return bgr
    try:
        with Image.open(BytesIO(data)) as img:
            rgb = np.asarray(img.convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as exc:
        logger.warning("Could not decode image (OpenCV + Pillow): %s — %s", path, exc)
        return None


def _imwrite_path(path: Path, img: np.ndarray) -> bool:
    """Write image; avoids cv2.imwrite so non-ASCII paths work on Windows."""
    suffix = path.suffix.lower() or ".png"
    ok, buf = cv2.imencode(suffix, img)
    if not ok or buf is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.tobytes())
    return True


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = _order_points(pts)
    (tl, tr, br, bl) = rect
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = int(max(width_a, width_b))
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = int(max(height_a, height_b))
    if max_width < 10 or max_height < 10:
        return image
    dst = np.array(
        [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
        dtype="float32",
    )
    m = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, m, (max_width, max_height))


def _try_perspective_correction(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    h, w = gray.shape[:2]
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            area = cv2.contourArea(approx)
            if area > 0.2 * w * h:
                pts = approx.reshape(4, 2).astype("float32")
                return _four_point_transform(gray, pts)
    return gray


def process_image_file(input_path: Path, output_path: Path | None = None) -> Path:
    """
    Read image from disk, run pipeline, write processed image.
    Returns path to processed image (output_path or alongside input with _processed suffix).
    """
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    bgr = _imread_path(path)
    if bgr is None:
        raise ValueError(f"OpenCV could not read image: {path}")

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    gray = _try_perspective_correction(gray)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    out = output_path or path.with_name(f"{path.stem}_processed{path.suffix}")
    if not _imwrite_path(out, thresh):
        raise ValueError(f"OpenCV could not write image: {out}")
    logger.info("Image processed: %s -> %s", path, out)
    return out
