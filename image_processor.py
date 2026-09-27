"""Image annotation, privacy masking, and PNG export helpers."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw


def _bbox(detection: Any) -> tuple[int, int, int, int] | None:
    value = detection.get("bbox") if isinstance(detection, dict) else getattr(detection, "bbox", None)
    try:
        if len(value) == 4 and all(isinstance(point, (list, tuple)) for point in value):
            xs = [int(float(point[0])) for point in value]
            ys = [int(float(point[1])) for point in value]
            box = min(xs), min(ys), max(xs), max(ys)
        elif len(value) == 4:
            box = tuple(int(float(point)) for point in value)
        else:
            return None
        return box if box[2] > box[0] and box[3] > box[1] else None
    except (TypeError, ValueError, IndexError):
        return None


def draw_bounding_boxes(image: Image.Image, detections: Iterable[Any]) -> Image.Image:
    """Return a copy with valid detection boxes highlighted."""
    preview = image.convert("RGB").copy()
    draw = ImageDraw.Draw(preview)
    for detection in detections:
        box = _bbox(detection)
        if box is None:
            continue
        left, top, right, bottom = box
        left, top = max(0, left), max(0, top)
        right, bottom = min(preview.width - 1, right), min(preview.height - 1, bottom)
        if right <= left or bottom <= top:
            continue
        draw.rectangle((left, top, right, bottom), outline=(230, 72, 61), width=max(2, preview.width // 500))
    return preview


def create_detection_preview(image: Image.Image, detections: Iterable[Any]) -> Image.Image:
    """Alias for the sensitive-region visualization used by the UI."""
    return draw_bounding_boxes(image, detections)


def mask_regions(
    image: Image.Image,
    detections: Iterable[Any],
    method: str = "Black",
    color: tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    """Mask complete detection rectangles with opaque black or pixelation."""
    protected = image.convert("RGB").copy()
    for detection in detections:
        box = _bbox(detection)
        if box is None:
            continue
        left, top, right, bottom = box
        left, top = max(0, left), max(0, top)
        right, bottom = min(protected.width, right), min(protected.height, bottom)
        if right <= left or bottom <= top:
            continue
        if method.lower() == "pixelated":
            region = protected.crop((left, top, right, bottom))
            tiny_size = (max(1, region.width // 12), max(1, region.height // 12))
            reduced = cv2.resize(np.asarray(region), tiny_size, interpolation=cv2.INTER_AREA)
            enlarged = cv2.resize(reduced, region.size, interpolation=cv2.INTER_NEAREST)
            protected.paste(Image.fromarray(enlarged), (left, top))
        else:
            ImageDraw.Draw(protected).rectangle((left, top, right - 1, bottom - 1), fill=color)
    return protected


def create_privacy_preview(
    image: Image.Image, detections: Iterable[Any], method: str = "Black"
) -> Image.Image:
    """Create the protected preview; kept distinct for UI intent clarity."""
    return mask_regions(image, detections, method=method)


def export_png(image: Image.Image) -> bytes:
    """Encode an image as downloadable PNG bytes."""
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
