# PrivacyLens AI

**Detect. Protect. Share safely.**

## Overview

PrivacyLens AI is a local-first prototype that scans a screenshot, photograph, or scanned document for visible text, flags potentially sensitive regions, and lets the user mask and export those regions before sharing.

## Problem

Screenshots and documents can accidentally expose email addresses, phone numbers, web addresses, identifiers, or address details. Manual review is easy to miss, especially when text is small or mixed into a larger image.

## Solution

The app combines local OCR with conservative, rule-based privacy detection. It highlights candidate regions and lets the user mask all matches or only selected categories. The user reviews the result and downloads a protected PNG.

## Key Features

- Upload JPG, JPEG, and PNG images.
- Extract text and bounding boxes with EasyOCR.
- Detect email addresses, common phone formats, URLs, long identifier-like numbers, conservative address patterns, and names after explicit identity labels.
- Display category, recognized text, heuristic confidence, and detection reason.
- Preview highlighted regions and mask all or selected categories.
- Choose an opaque black mask (default) or pixelation.
- Download the protected image as PNG.
- Process the uploaded image locally; no image API, database, authentication, or external backend is used.

## How It Works

`Image → OCR → Privacy Detection → Bounding Boxes → Masking → Protected PNG`

## Architecture

- `app.py`: single-page Streamlit workflow, upload handling, scan status, results, selection, preview, and download.
- `ocr_engine.py`: lazy EasyOCR initialization and a normalized `OCREngine.extract_text(image)` interface returning text, pixel bounding boxes, and OCR confidence.
- `privacy_detector.py`: offline regular-expression and conservative-context rules, returning structured detection records.
- `image_processor.py`: bounding-box previews, opaque or pixelated masking, and PNG encoding.
- `tests/test_privacy_detector.py`: focused detector tests.
- `docs/snapdragon_optimization.md`: deployment considerations and verification guidance for Snapdragon devices.

## Technology Stack

Python, Streamlit, EasyOCR, OpenCV, Pillow, NumPy, Python regular expressions, and pytest. The detector uses only local code and the Python standard library.

## Snapdragon Optimization

PrivacyLens AI is designed with Snapdragon-powered Windows PCs in mind, but this prototype does **not** claim or verify Snapdragon NPU execution. OCR is isolated behind `OCREngine`, allowing a compatible Qualcomm AI Hub optimized OCR artifact and its supported runtime to replace the EasyOCR implementation without changing the detector or UI contract. Qualcomm AI Hub EasyOCR-related support is a documented deployment option, not an integration performed by this prototype. See [the Snapdragon optimization guide](docs/snapdragon_optimization.md).

## Privacy by Design

- Uploaded image data is processed in the local Python process and is not sent to a cloud OCR or AI API.
- There is no database, authentication service, external backend, or application-managed image storage.
- Masking is user-controlled, and the user should inspect the protected result before sharing.
- EasyOCR may download its model weights on first initialization if they are not already cached. This model download is separate from image processing; the application does not upload images. Run in an appropriately managed environment if model downloads are restricted.
- The app does not promise secure deletion or guarantee that detection finds every sensitive item.

## Installation

Use Python 3.12 or newer. Open PowerShell in the project folder. The commands below work with Python 3.12 and are intended to resolve compatible current wheels for Windows:

```powershell
python --version
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The output of `python --version` should show Python 3.12 or newer. EasyOCR may download OCR model weights the first time a scan runs. The initial download can take time and requires network access; after the model is cached, image analysis is local.

## Run the App

```powershell
streamlit run app.py
```

## Run Tests

```powershell
python -m pytest
```

## Project Structure

```text
PrivacyLens-AI/
├── app.py
├── privacy_detector.py
├── image_processor.py
├── ocr_engine.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── assets/demo/
├── screenshots/
├── docs/snapdragon_optimization.md
└── tests/test_privacy_detector.py
```

The demo and screenshots folders are included as locations for user-provided assets and captures; no sample image is required to run the app.

## Demo

1. Start Streamlit and open the local URL it prints.
2. Upload a JPG, JPEG, or PNG.
3. Review the original image, scan metrics, detection table, and highlighted regions.
4. Keep all categories selected or choose specific categories. Select black or pixelated masking.
5. Create the protected preview, inspect the result, then download the PNG.

## Limitations

- OCR can miss, misread, or misplace text, particularly in low-resolution, rotated, stylized, or handwritten content.
- Detection is heuristic. False positives and false negatives are possible; reported confidence combines OCR confidence with a rule score and is not a calibrated probability.
- Address detection is intentionally limited to recognizable street-number and street-type patterns. Name detection only activates after a small set of explicit identity labels; neither is comprehensive.
- ID-like numeric detection is pattern-based and cannot determine what an identifier represents.
- EasyOCR is initialized for English in this prototype. Performance depends on local hardware and model initialization. Snapdragon acceleration has not been verified.
- Pixelation is a visual obfuscation and should not be treated as equivalent to an opaque mask. Choose the black mask when stronger visual concealment is needed.

## Future Improvements

- Deploy and validate a Qualcomm AI Hub optimized OCR model and supported Snapdragon runtime.
- Verify Snapdragon NPU execution and benchmark accuracy, latency, memory, and energy on compatible hardware.
- Add multilingual OCR and additional privacy categories.
- Improve address/name classification with transparent local techniques and focused validation.

## License

The project code in this repository is licensed under the MIT License; see [LICENSE](LICENSE). Third-party packages and model weights retain their own licenses and terms. Review those terms for your intended distribution.
