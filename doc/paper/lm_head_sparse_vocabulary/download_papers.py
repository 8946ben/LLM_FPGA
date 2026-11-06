"""Download original public papers; validate every page and record provenance.

Run with Python + pypdf. Existing PDFs are verified and never overwritten.
Use --verify-only to check the frozen manifest without network access.
"""
import argparse
import concurrent.futures
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
TEXT_ROOT = ROOT.parents[2] / "tmp" / "paper_review_20261019"


def inspect(data, item):
    if not data.startswith(b"%PDF-"):
        raise ValueError("Response is not an original PDF")
    # Some official PDFs (P03) contain duplicate /Group keys in image objects.
    # Tolerant parsing preserves their original bytes and extracts all pages.
    reader = PdfReader(io.BytesIO(data), strict=False)
    pdfinfo = shutil.which("pdfinfo")
    pdftotext = Path(pdfinfo).with_name("pdftotext.exe") if pdfinfo else None
    bundled_pdftotext = Path(sys.executable).parents[1] / "native/poppler/Library/bin/pdftotext.exe"
    if not pdftotext and bundled_pdftotext.exists():
        pdftotext = bundled_pdftotext
    if pdftotext and pdftotext.exists():
        process = subprocess.run([str(pdftotext), "-layout", "-", "-"], input=data,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        texts = process.stdout.decode("utf-8").split("\f")
        if not texts[-1].strip():
            texts.pop()
        assert len(texts) == len(reader.pages), "Page extraction count mismatch"
    else:
        texts = [page.extract_text() or "" for page in reader.pages]
    if not texts or any(len(t.strip()) < 10 for t in texts):
        raise ValueError("Missing or unreadable PDF page")
    normalize = lambda s: re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).lower())
    if normalize(item["title"]) not in normalize(texts[0]):
        raise ValueError("First-page title does not match catalog")
    TEXT_ROOT.mkdir(parents=True, exist_ok=True)
    (TEXT_ROOT / (Path(item["file"]).stem + ".txt")).write_text(
        "\n\n".join(f"=== PDF PAGE {i+1} ===\n{t}" for i, t in enumerate(texts)),
        encoding="utf-8",
    )
    return {
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "pages": len(texts), "title_verified": True,
        "all_pages_text_extracted": True,
    }


def fetch(item):
    path = ROOT / item["file"]
    if path.exists():
        data = path.read_bytes()
        original = next((p for p in PREVIOUS if p["id"] == item["id"]), {})
        provenance = {k: original[k] for k in
                      ["fetched_utc", "resolved_url", "content_type"] if k in original}
    else:
        request = urllib.request.Request(item["pdf_url"], headers={"User-Agent": "Mozilla/5.0 (research paper archive)"})
        with urllib.request.urlopen(request, timeout=50) as response:
            data = response.read()
            provenance = {"fetched_utc": datetime.now(timezone.utc).isoformat(),
                          "resolved_url": response.url,
                          "content_type": response.headers.get("Content-Type")}
        inspect(data, item)
        path.write_bytes(data)
    return {**item, **provenance, **inspect(data, item)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    manifest = ROOT / "manifest.json"
    PREVIOUS = json.loads(manifest.read_text(encoding="utf-8"))["papers"] if manifest.exists() else []
    if args.verify_only:
        assert len(PREVIOUS) == len(catalog), "Manifest is incomplete"
        for item in PREVIOUS:
            result = inspect((ROOT / item["file"]).read_bytes(), item)
            assert all(result[k] == item[k] for k in result), item["file"]
            print(f"PASS {item['id']} {item['pages']} pages {item['sha256']}")
    else:
        completed, errors = [], []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fetch, item): item for item in catalog}
            for future in concurrent.futures.as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                    completed.append(result)
                    print(f"OK {item['id']} {result['pages']} pages {result['bytes']} bytes", flush=True)
                except Exception as exc:
                    errors.append({"id": item["id"], "error": str(exc)})
                    print(f"FAILED {item['id']}: {exc}", flush=True)
        completed.sort(key=lambda p: p["id"])
        manifest.write_text(json.dumps({"review_date":"2026-10-19", "papers":completed,
                                       "errors":errors}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        if errors:
            raise SystemExit(1)
