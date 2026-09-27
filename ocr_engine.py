"""Local OCR adapter with a stable interface for future optimized backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class OCRResult:
    """Text recognized in an image and its bounding rectangle in pixels."""

    text: str
    bbox: tuple[int, int, int, int]
    confidence: float


class OCREngine:
    """EasyOCR-backed implementation of the local OCR interface.

    Reader initialization is lazy so the application can display useful errors
    instead of failing at import time when a model cannot be initialized.
    """

    def __init__(self) -> None:
        self._reader: Any | None = None
        self._initialization_error: Exception | None = None

    def _get_reader(self) -> Any:
        if self._reader is not None:
            return self._reader
        if self._initialization_error is not None:
            raise RuntimeError(f"OCR could not initialize: {self._initialization_error}") from self._initialization_error
        try:
            import easyocr

            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            return self._reader
        except Exception as exc:
            self._initialization_error = exc
            raise RuntimeError(f"OCR could not initialize: {exc}") from exc

    def extract_text(self, image: Image.Image | np.ndarray) -> list[OCRResult]:
        """Extract text, axis-aligned bounding boxes, and confidence locally."""
        if isinstance(image, Image.Image):
            image_array = np.asarray(image.convert("RGB"))
        else:
            image_array = np.asarray(image)
        if image_array.size == 0 or image_array.ndim not in (2, 3):
            raise ValueError("The image is empty or has an unsupported shape.")

        raw_results = self._get_reader().readtext(image_array, detail=1, paragraph=False)
        results: list[OCRResult] = []
        for item in raw_results:
            try:
                points, text, confidence = item
                coordinates = np.asarray(points, dtype=float).reshape(-1, 2)
                if coordinates.size == 0 or not text or not str(text).strip():
                    continue
                left = max(0, int(np.floor(coordinates[:, 0].min())))
                top = max(0, int(np.floor(coordinates[:, 1].min())))
                right = int(np.ceil(coordinates[:, 0].max()))
                bottom = int(np.ceil(coordinates[:, 1].max()))
                if right <= left or bottom <= top:
                    continue
                results.append(
                    OCRResult(
                        text=str(text).strip(),
                        bbox=(left, top, right, bottom),
                        confidence=max(0.0, min(1.0, float(confidence))),
                    )
                )
            except (TypeError, ValueError, IndexError):
                continue
        return results
