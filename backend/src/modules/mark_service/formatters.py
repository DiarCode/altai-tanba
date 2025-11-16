from __future__ import annotations

from typing import Dict, List

from .types import PageImage, Detection


def build_challenge_json(pdf_name: str, pages: List[PageImage], page_dets: Dict[int, List[Detection]]) -> Dict:
    """
    Builds the JSON format:
    {
      "file.pdf": {
        "page_1": { "annotations": [ ... ], "page_size": {width, height} },
        ...
      }
    }
    """
    result = {pdf_name: {}}
    ann_id = 0

    for page in pages:
        annotations = []
        for det in page_dets.get(page.index, []):
            ann_id += 1
            ann_key = f"annotation_{ann_id}"
            annotations.append(
                {
                    ann_key: {
                        "category": det.category,
                        "bbox": {
                            "x": det.x,
                            "y": det.y,
                            "width": det.w,
                            "height": det.h,
                        },
                        "area": det.area,
                        "confidence": det.confidence,
                    }
                }
            )

        page_key = f"page_{page.index}"
        result[pdf_name][page_key] = {
            "annotations": annotations,
            "page_size": {
                "width": page.width,
                "height": page.height,
            },
        }

    return result
