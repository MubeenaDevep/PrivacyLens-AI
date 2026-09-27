"""Streamlit interface for local OCR-based privacy protection."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

from image_processor import create_detection_preview, export_png, mask_regions
from ocr_engine import OCREngine
from privacy_detector import SensitiveDetection, detect_sensitive_information


st.set_page_config(page_title="PrivacyLens AI", page_icon="🔎", layout="wide")


@st.cache_resource(show_spinner=False)
def get_ocr_engine() -> OCREngine:
    """Reuse the local OCR reader across Streamlit reruns."""
    return OCREngine()


def _detection_value(detection: SensitiveDetection, field: str) -> Any:
    return getattr(detection, field)


def main() -> None:
    st.title("PrivacyLens AI")
    st.subheader("Detect. Protect. Share safely.")
    st.caption("Local OCR and privacy detection for screenshots, photographs, and scanned documents.")

    st.header("1. Upload Image")
    uploaded_file = st.file_uploader(
        "Choose a JPG, JPEG, or PNG image",
        type=["jpg", "jpeg", "png"],
        help="Images are analyzed locally in this application session.",
    )
    st.info("Images are processed locally and are not sent to external cloud APIs.")

    if uploaded_file is None:
        st.markdown("### Original Image\nUpload an image to begin the privacy scan.")
        st.caption(
            "PrivacyLens AI is a prototype. Automated detection may produce false positives or false negatives. "
            "Always review the protected image before sharing."
        )
        return

    if uploaded_file.name.rsplit(".", 1)[-1].lower() not in {"jpg", "jpeg", "png"}:
        st.error("Unsupported file type. Upload a JPG, JPEG, or PNG image.")
        return

    image_bytes = uploaded_file.getvalue()
    image_key = hashlib.sha256(image_bytes).hexdigest()
    try:
        image = ImageOps.exif_transpose(Image.open(uploaded_file)).convert("RGB")
        if image.width <= 0 or image.height <= 0 or np.asarray(image).size == 0:
            st.error("This image is empty. Choose another image and try again.")
            return
    except (UnidentifiedImageError, OSError, ValueError):
        st.error("This image could not be opened. It may be corrupted or empty.")
        return

    st.header("2. Original Image")
    st.image(image, caption=uploaded_file.name, width="stretch")

    if st.session_state.get("scan_key") != image_key:
        st.session_state.scan_key = image_key
        st.session_state.ocr_results = []
        st.session_state.detections = []
        st.session_state.protected_png = None
        st.session_state.protected_config = None
        try:
            with st.spinner("Scanning text locally with EasyOCR..."):
                ocr_results = get_ocr_engine().extract_text(image)
            st.session_state.ocr_results = ocr_results
            st.session_state.detections = detect_sensitive_information(ocr_results)
            st.session_state.scan_error = None
        except Exception as exc:
            st.session_state.scan_error = str(exc)

    ocr_results = st.session_state.get("ocr_results", [])
    detections: list[SensitiveDetection] = st.session_state.get("detections", [])
    st.header("3. Privacy Scan")

    if st.session_state.get("scan_error"):
        st.error(
            "The local OCR scan could not be completed. Check that the OCR dependencies and model are available, "
            "then restart the app."
        )
        with st.expander("Technical details"):
            st.code(st.session_state.scan_error)
        total_regions = 0
    else:
        total_regions = len(ocr_results)
        if total_regions == 0:
            st.warning("No readable text was detected. Try a sharper image with larger, well-lit text.")
        elif detections:
            st.success("Privacy Scan Complete")
        else:
            st.info("Privacy Scan Complete. No potentially sensitive information was detected.")

    counts = {detection.category: 0 for detection in detections}
    for detection in detections:
        counts[detection.category] = counts.get(detection.category, 0) + 1
    metric_columns = st.columns(5)
    metric_columns[0].metric("Text regions", total_regions)
    metric_columns[1].metric("Sensitive regions", len(detections))
    metric_columns[2].metric("Emails", counts.get("EMAIL", 0))
    metric_columns[3].metric("Phone numbers", counts.get("PHONE", 0))
    metric_columns[4].metric("URLs", counts.get("URL", 0))

    st.header("4. Detection Results")
    if detections:
        table_rows = [
            {
                "Category": item.category,
                "Detected Text": item.text,
                "Confidence": f"{item.confidence:.0%}",
                "Reason": item.reason,
            }
            for item in detections
        ]
        st.dataframe(table_rows, hide_index=True, width="stretch")
        with st.expander("Review highlighted regions"):
            st.image(create_detection_preview(image, detections), width="stretch")
    elif not st.session_state.get("scan_error") and total_regions > 0:
        st.caption("No regions are highlighted because no potential sensitive text matched the current rules.")

    st.header("5. Protected Preview")
    if detections:
        available_categories = sorted({item.category for item in detections})
        mask_scope = st.radio(
            "Information to mask",
            ["All sensitive information", "Selected categories"],
            horizontal=True,
        )
        if mask_scope == "All sensitive information":
            selected_categories = available_categories
        else:
            selected_categories = st.multiselect(
                "Categories to mask",
                options=available_categories,
                default=available_categories,
            )
        masking_method = st.radio("Masking method", ["Black", "Pixelated"], horizontal=True)
        selected_detections = [item for item in detections if item.category in selected_categories]
        protected_config = (image_key, tuple(sorted(selected_categories)), masking_method)
        if st.button("Create Protected Image", type="primary", disabled=not selected_detections):
            protected_image = mask_regions(image, selected_detections, method=masking_method)
            st.session_state.protected_png = export_png(protected_image)
            st.session_state.protected_config = protected_config

        if not selected_detections:
            st.warning("Select at least one category to create a protected image.")
        elif st.session_state.get("protected_config") == protected_config and st.session_state.get("protected_png"):
            st.image(
                st.session_state.protected_png,
                caption=f"Protected preview ({masking_method.lower()} mask)",
                width="stretch",
            )
            st.header("6. Download Protected Image")
            st.download_button(
                "Download Protected Image",
                data=st.session_state.protected_png,
                file_name="privacylens-protected.png",
                mime="image/png",
                type="primary",
            )
        else:
            st.caption("Choose the regions and masking method, then create the protected image.")
    else:
        st.caption("A protected image will be available here after sensitive information is detected.")

    st.caption(
        "PrivacyLens AI is a prototype. Automated detection may produce false positives or false negatives. "
        "Always review the protected image before sharing."
    )


if __name__ == "__main__":
    main()
