"""Conservative, offline detection of potentially sensitive OCR text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SensitiveDetection:
    """A potentially private OCR region and the reason it was flagged."""

    category: str
    text: str
    confidence: float
    bbox: tuple[int, int, int, int]
    reason: str


_EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+(?![\w.-])", re.IGNORECASE)
_URL_RE = re.compile(r"(?i)(?<![@\w.-])(?:https?://|www\.)?[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}(?::\d{1,5})?(?:/[^\s<>]*)?")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d{1,3}[\s().-]?)?(?:\(?\d{3,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}(?!\w)")
_LONG_NUMBER_RE = re.compile(r"(?<!\d)(?:\d[ -]?){11,17}\d(?!\d)")
_ADDRESS_RE = re.compile(r"\b\d{1,6}\s+[\w.'-]+(?:\s+[\w.'-]+){0,4}\s+(?:street|st\.?|road|rd\.?|avenue|ave\.?|boulevard|blvd\.?|lane|ln\.?|drive|dr\.?|court|ct\.?|way)\b", re.IGNORECASE)
_NAME_CONTEXT_RE = re.compile(r"\b(?:name|contact|patient|employee|account holder)\s*[:=-]\s*([A-Z][a-z]{1,30}(?:\s+[A-Z][a-z]{1,30}){1,3})\b")


def _field(result: Any, name: str, default: Any = None) -> Any:
    if isinstance(result, dict):
        aliases = {"text": "detected_text", "bbox": "bounding_box"}
        return result.get(name, result.get(aliases.get(name, ""), default))
    return getattr(result, name, default)


def _valid_bbox(value: Any) -> tuple[int, int, int, int] | None:
    try:
        if len(value) == 4 and all(isinstance(point, (list, tuple)) for point in value):
            xs = [float(point[0]) for point in value]
            ys = [float(point[1]) for point in value]
            box = (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
        elif len(value) == 4:
            box = tuple(int(float(point)) for point in value)
        else:
            return None
        return box if box[2] > box[0] and box[3] > box[1] else None
    except (TypeError, ValueError, IndexError):
        return None


def detect_sensitive_information(ocr_results: list[Any]) -> list[SensitiveDetection]:
    """Classify OCR regions using patterns and cautious contextual heuristics.

    OCR confidence is used as a floor: regions below 0.25 are ignored. The
    returned confidence combines OCR certainty with a category-specific score;
    it is not a calibrated probability.
    """
    detections: list[SensitiveDetection] = []
    if not ocr_results:
        return detections

    for result in ocr_results:
        text_value = _field(result, "text", "")
        text = str(text_value).strip() if text_value is not None else ""
        try:
            ocr_confidence = float(_field(result, "confidence", 1.0))
        except (TypeError, ValueError):
            continue
        bbox = _valid_bbox(_field(result, "bbox"))
        if not text or bbox is None or ocr_confidence < 0.25:
            continue
        ocr_confidence = min(1.0, max(0.0, ocr_confidence))

        candidates: list[tuple[str, str, float]] = []
        if _EMAIL_RE.search(text):
            candidates.append(("EMAIL", "Text matches a standard email-address pattern.", 0.98))
        if _URL_RE.search(text):
            candidates.append(("URL", "Text contains an HTTP(S) or www web address.", 0.95))

        for match in _PHONE_RE.finditer(text):
            digits = re.sub(r"\D", "", match.group())
            explicit_country_code = match.group().lstrip().startswith("+")
            if (len(digits) == 10 or (explicit_country_code and 11 <= len(digits) <= 13)) and len(set(digits)) > 2:
                candidates.append(("PHONE", "Number has a common 10-13 digit phone format.", 0.82))
                break

        if not any(category == "PHONE" for category, _, _ in candidates):
            for match in _LONG_NUMBER_RE.finditer(text):
                digits = re.sub(r"\D", "", match.group())
                if 12 <= len(digits) <= 18 and len(set(digits)) > 3:
                    candidates.append(("ID_NUMBER", "Long numeric sequence may be an identifier; verify before sharing.", 0.72))
                    break

        if _ADDRESS_RE.search(text):
            candidates.append(("ADDRESS", "Street number and street-type wording suggest an address; not verified.", 0.68))

        if _NAME_CONTEXT_RE.search(text) and ocr_confidence >= 0.70:
            candidates.append(("NAME", "A name follows an explicit identity label; verify this contextual match.", 0.70))

        for category, reason, category_confidence in candidates:
            detections.append(
                SensitiveDetection(
                    category=category,
                    text=text,
                    confidence=round(min(ocr_confidence, category_confidence), 3),
                    bbox=bbox,
                    reason=reason,
                )
            )
    return detections
