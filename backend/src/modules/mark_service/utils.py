from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import cv2
from PIL import Image
from pypdf import PdfWriter

from .types import PageImage, Detection


def yolo_results_to_detections(results, category: str, conf_thres: float) -> List[Detection]:
	dets: List[Detection] = []
	for r in results:
		for box in getattr(r, "boxes", []) or []:
			conf = float(box.conf[0])
			if conf < conf_thres:
				continue
			x1, y1, x2, y2 = box.xyxy[0].tolist()
			w = x2 - x1
			h = y2 - y1
			dets.append(
				Detection(
					category=category,
					x=float(x1),
					y=float(y1),
					w=float(w),
					h=float(h),
					area=float(w * h),
					confidence=conf,
				)
			)
	return dets


def draw_boxes_on_page(page: PageImage, detections: List[Detection]) -> Path:
	img = cv2.imread(str(page.path))
	if img is None:
		raise RuntimeError(f"Cannot read page image: {page.path}")

	for det in detections:
		x1, y1 = int(det.x), int(det.y)
		x2, y2 = int(det.x + det.w), int(det.y + det.h)
		color = (0, 255, 0)
		cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
		cv2.putText(
			img,
			det.category,
			(x1, max(y1 - 5, 0)),
			cv2.FONT_HERSHEY_SIMPLEX,
			0.5,
			color,
			1,
			cv2.LINE_AA,
		)

	out_path = page.path.parent / f"page_{page.index}_labeled.png"
	cv2.imwrite(str(out_path), img)
	return out_path


def build_labeled_pdf(doc_dir: Path, pages: List[PageImage], page_dets: Dict[int, List[Detection]]) -> Path:
	labeled_page_paths: List[Path] = []
	for page in pages:
		dets = page_dets.get(page.index, [])
		labeled_page_paths.append(draw_boxes_on_page(page, dets))

	labeled_pdf_paths: List[Path] = []
	for p in labeled_page_paths:
		img = Image.open(p).convert("RGB")
		pdf_page = p.with_suffix(".pdf")
		img.save(pdf_page, "PDF")
		labeled_pdf_paths.append(pdf_page)

	labeled_pdf = doc_dir / "labeled.pdf"

	writer = PdfWriter()
	for pdf_path in labeled_pdf_paths:
		writer.append(str(pdf_path))

	writer.write(str(labeled_pdf))
	writer.close()

	return labeled_pdf
