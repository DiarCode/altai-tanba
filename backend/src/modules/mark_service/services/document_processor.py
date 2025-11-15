# modules/mark_service/services/document_processor.py

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

from ultralytics import YOLO


# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]  # modules/mark_service
WEIGHTS_DIR = BASE_DIR / "model" / "weights"

QR_WEIGHTS = WEIGHTS_DIR / "qr_yolov8n_best.pt"
SIG_WEIGHTS = WEIGHTS_DIR / "signature_yolov8n_bw_best.pt"
STAMP_WEIGHTS = WEIGHTS_DIR / "stamp_yolov8n_best.pt"

IMG_SIZE = 640
BATCH_SIZE = 8  # YOLO internal batch


from core.utils.pdf import pdf_to_images
from modules.mark_service.types import PageImage, Detection
from modules.mark_service.utils import yolo_results_to_detections, build_labeled_pdf
from modules.mark_service.formatters import build_challenge_json
from core.s3 import S3Client, MockS3Client
from core.config.settings import settings

class DigitalInspectorProcessor:
    def __init__(self, s3_client=None):
        if s3_client is not None:
            self.s3 = s3_client
        else:
            self.s3 = MockS3Client() if settings.USE_STUB_ADAPTER else S3Client()
        self.qr_model = YOLO(str(QR_WEIGHTS))
        self.sig_model = YOLO(str(SIG_WEIGHTS))
        self.stamp_model = YOLO(str(STAMP_WEIGHTS))


    def run_inference_on_pages(
        self, pages: List[PageImage], conf_thres: float = 0.25
    ) -> Dict[int, List[Detection]]:
        """
        Runs 3 models on all pages using batched inference.
        Returns mapping: page_index -> [Detection...]
        """
        if not pages:
            return {}

        image_paths = [str(p.path) for p in pages]

        # YOLO can take list of paths and will batch internally
        qr_results = self.qr_model(image_paths, imgsz=IMG_SIZE, batch=BATCH_SIZE, verbose=False)
        sig_results = self.sig_model(image_paths, imgsz=IMG_SIZE, batch=BATCH_SIZE, verbose=False)
        stamp_results = self.stamp_model(image_paths, imgsz=IMG_SIZE, batch=BATCH_SIZE, verbose=False)

        page_dets: Dict[int, List[Detection]] = {p.index: [] for p in pages}

        for idx, page in enumerate(pages):
            qr_d = yolo_results_to_detections([qr_results[idx]], "qr", conf_thres)
            sg_d = yolo_results_to_detections([sig_results[idx]], "signature", conf_thres)
            st_d = yolo_results_to_detections([stamp_results[idx]], "stamp", conf_thres)

            page_dets[page.index].extend(qr_d)
            page_dets[page.index].extend(sg_d)
            page_dets[page.index].extend(st_d)

        return page_dets


    def upload_document_to_s3(
        self,
        doc_hash: str,
        pdf_path: Path,
        labeled_pdf_path: Path,
        pages: List[PageImage],
    ) -> Dict[str, str]:
        """
        Upload original.pdf, labeled.pdf and pages/* to S3 in parallel.
        Returns mapping of logical name -> s3 URI.
        """
        uploads = {}

        tasks = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            # original
            tasks.append(
                ex.submit(
                    self.s3.upload_file,
                    str(pdf_path),
                    f"/{doc_hash}/original.pdf",
                )
            )
            # labeled
            tasks.append(
                ex.submit(
                    self.s3.upload_file,
                    str(labeled_pdf_path),
                    f"/{doc_hash}/labeled.pdf",
                )
            )
            # pages
            for page in pages:
                tasks.append(
                    ex.submit(
                        self.s3.upload_file,
                        str(page.path),
                        f"/{doc_hash}/pages/page_{page.index}.png",
                    )
                )

            for fut in as_completed(tasks):
                uri = fut.result()
                # we don't distinguish keys here, just collect URIs
                uploads.setdefault("files", []).append(uri)

        return uploads

    # -------------- HIGH-LEVEL ENTRYPOINT -------------------

    def process_pdf(
        self,
        pdf_path: Path,
        work_root: Path,
        conf_thres: float = 0.25,
    ) -> Dict:
        """
        High-level:
          - pdf → images
          - run 3 detectors on all pages (batched)
          - build labeled.pdf
          - upload original + labeled + pages to S3 (mock)
          - return challenge JSON + S3 info
        """
        pdf_path = pdf_path.resolve()
        pdf_name = pdf_path.name

        # 1) PDF → images
        doc_hash, pages = pdf_to_images(pdf_path, work_root)
        doc_dir = work_root / doc_hash

        # 2) inference
        page_dets = self.run_inference_on_pages(pages, conf_thres=conf_thres)

        # 3) labeled.pdf
        labeled_pdf = build_labeled_pdf(doc_dir, pages, page_dets)

        # 4) S3 uploads
        s3_info = self.upload_document_to_s3(
            doc_hash=doc_hash,
            pdf_path=doc_dir / "original.pdf",
            labeled_pdf_path=labeled_pdf,
            pages=pages,
        )

        # 5) JSON
        challenge_json = build_challenge_json(pdf_name, pages, page_dets)

        return {
            "doc_hash": doc_hash,
            "json": challenge_json,
            "s3": s3_info,
        }


# -------------------------------------------------------------------
# CLI / quick manual test
# -------------------------------------------------------------------

if __name__ == "__main__":
    # Example usage:
    # python document_processor.py /path/to/document.pdf
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=str, help="Path to PDF document")
    parser.add_argument(
        "--work-dir",
        type=str,
        default=str(Path.cwd() / "work_dir"),
        help="Where to store per-document folders",
    )
    args = parser.parse_args()

    processor = DigitalInspectorProcessor()
    out = processor.process_pdf(Path(args.pdf), Path(args.work_dir))

    print("\n=== JSON preview ===")
    print(json.dumps(out["json"], ensure_ascii=False, indent=2))
    print("\n=== S3 mock info ===")
    print(json.dumps(out["s3"], ensure_ascii=False, indent=2))
    print("\nDocument hash:", out["doc_hash"])
