# Snapdragon Optimization Guide

## Local AI and Privacy

Image processing on the user's device avoids sending screenshots or documents to a hosted OCR service. This reduces data exposure to external services and can support offline workflows after required packages and model weights are available. Local execution does not by itself guarantee that data is securely erased or that the application detects every sensitive region.

## Snapdragon-Powered PCs

Snapdragon-powered Windows PCs provide local CPU and GPU resources and, on supported models and software stacks, an NPU intended for efficient AI workloads. Whether a particular OCR model can use that NPU depends on model format, runtime, device support, drivers, and the deployment toolchain. This repository does not currently select or invoke a Snapdragon NPU.

## Qualcomm AI Hub Deployment Concept

Qualcomm AI Hub can be used to evaluate and prepare supported models for Qualcomm hardware. A deployment normally requires selecting a supported model and device target, using the corresponding export/optimization workflow, integrating the resulting artifact with a compatible runtime, and validating output parity on target hardware. The actual runtime and integration depend on the model and current Qualcomm tooling; this guide does not assume a particular SDK API or include a fake integration.

Qualcomm AI Hub documents EasyOCR-related model support for Snapdragon device targets, including Snapdragon X Elite, Snapdragon X Plus 8-Core, and Snapdragon X2 Elite. This is a possible future deployment path, not proof that the code here uses those targets or runs on an NPU.

## EasyOCR in This Prototype

`ocr_engine.py` implements `OCREngine.extract_text(image)` using EasyOCR with local CPU execution (`gpu=False`). It normalizes each result to recognized text, an axis-aligned pixel bounding box, and OCR confidence. Initialization is lazy and failures are reported to the UI rather than terminating the app. EasyOCR may fetch its model weights on first use if they are not already cached; images are not sent to that download service.

## Replacing the OCR Backend

Keep the replacement behind the existing interface:

```python
class OCREngine:
    def extract_text(self, image):
        ...
```

The detector and image processor need normalized results with `text`, `bbox` as `(left, top, right, bottom)` pixel coordinates, and `confidence` from 0 to 1. An optimized backend should convert its native output into this contract. Preserve the image dimensions and coordinate frame, validate boxes, and compare output against representative images before switching the UI to the new engine. The UI and privacy rules should not need backend-specific SDK calls.

## Benchmarking on Compatible Hardware

To make a defensible NPU claim, use a compatible Snapdragon PC and the actual optimized artifact/runtime. Record the exact device model, OS/build, driver and runtime versions, model version, input resolution, and precision/configuration. Verify through runtime/device profiling that inference is dispatched to the NPU rather than inferred from device availability. Benchmark a representative fixed image set after warm-up; report repeated median and tail latency, throughput, memory, power/energy where tooling supports it, and OCR accuracy/box quality against a labeled reference. Compare with CPU/GPU baselines under the same conditions and include setup/model-load time separately. Preserve logs and scripts so results can be reproduced. No benchmark figures are claimed in this repository.

## Claims: Current and Future

Current: OCR is implemented with EasyOCR and configured for CPU execution; privacy rules and image operations run locally in the application process. No Qualcomm runtime is integrated, and no Snapdragon NPU execution or performance has been experimentally verified.

Future: a Qualcomm AI Hub optimized model and supported runtime may be integrated behind `OCREngine`, followed by on-device profiling and accuracy/performance validation. Only after that validation should product materials claim Snapdragon NPU execution, and claims should name the tested device and software configuration.
