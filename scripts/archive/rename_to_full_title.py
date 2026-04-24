#!/usr/bin/env python3
"""
.paper-metadata.json 기반으로 collected/ 폴더의 PDF를 C스타일(full title)로 리네임.

형식: {Author}_{Year}_{Clean_Full_Title}.pdf
"""
import json
import re
import sys
import unicodedata
from pathlib import Path


MAX_FILENAME_LEN = 240  # filesystem safety (most FS allow 255)


def strip_diacritics(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_title_for_filename(raw_title: str) -> str:
    """원본 제목을 파일명에 쓸 수 있게 정돈."""
    t = raw_title

    # "Journal - YYYY - Author - Title" (원본에 대해 먼저, 더 구체적)
    m = re.match(r"^[A-Za-z][\w\s&\.\-]{4,60}\s+-\s+\d{4}\s+-\s+[A-ZÄÖÜŁ][\w\-\']+\s+-\s+(.+)$", t)
    if m:
        t = m.group(1)
    else:
        # "Author - YYYY - Title" 형식이면 Title만 추출
        m = re.match(r"^[^-\n]+\s+-\s+\d{4}\s+-\s+(.+)$", t)
        if m:
            t = m.group(1)

    # 선행 숫자 제거
    t = re.sub(r"^\d+\s+", "", t)

    # diacritics 제거 (filesystem 호환성)
    t = strip_diacritics(t)

    # 구두점 → 공백 (보존 목적)
    t = re.sub(r"[:\-–—]+", " ", t)
    t = re.sub(r"[,;!?&\(\)\[\]\{\}\/\\\|]", "", t)
    t = re.sub(r"['\"\u2018\u2019\u201c\u201d]", "", t)
    t = re.sub(r"[^\w\s]", "", t)

    # 연속 공백/탭 → 하나
    t = re.sub(r"\s+", " ", t).strip()

    # 공백 → 언더스코어
    t = t.replace(" ", "_")

    # 연속 언더스코어 정리
    t = re.sub(r"_+", "_", t).strip("_")

    return t


def compute_new_name(paper: dict) -> str:
    author = paper.get("author", "Unknown")
    year = paper.get("year", "nodate")
    title = paper.get("title", "untitled")

    clean = clean_title_for_filename(title)
    if not clean:
        clean = "untitled"

    base = f"{author}_{year}_{clean}"
    # 길이 제한 (.pdf 포함 240자)
    if len(base) + 4 > MAX_FILENAME_LEN:
        base = base[: MAX_FILENAME_LEN - 4].rstrip("_")
    return base + ".pdf"


def main(project_root: Path, dry_run: bool = False):
    meta_path = project_root / ".paper-metadata.json"
    coll_dir = project_root / "papers" / "collected"

    with open(meta_path) as f:
        metadata = json.load(f)

    rename_plan = []
    collisions = {}
    for paper in metadata["papers"]:
        old_name = paper["filename"]
        new_name = compute_new_name(paper)
        if new_name == old_name:
            continue
        rename_plan.append((old_name, new_name, paper))

    # collision detection
    target_names = {}
    for _, new, paper in rename_plan:
        target_names.setdefault(new, []).append(paper["filename"])
    for new, origs in target_names.items():
        if len(origs) > 1:
            collisions[new] = origs

    if collisions:
        print(f"⚠️  Collisions detected: {len(collisions)}")
        for new, origs in collisions.items():
            print(f"  {new}:")
            for o in origs:
                print(f"    ← {o}")
        if not dry_run:
            print("❌ Aborting due to collisions. Resolve first.")
            return 1

    print(f"Rename plan: {len(rename_plan)} files" + (" (DRY RUN)" if dry_run else ""))

    renamed = 0
    failed = []
    for old, new, paper in rename_plan:
        src = coll_dir / old
        dst = coll_dir / new
        if not src.exists():
            failed.append((old, "source missing"))
            continue
        if dst.exists() and src != dst:
            failed.append((old, f"target exists: {new}"))
            continue
        if dry_run:
            print(f"  {old[:60]}  →  {new[:60]}")
        else:
            src.rename(dst)
            paper["filename"] = new
            renamed += 1

    if not dry_run:
        from datetime import datetime
        metadata["last_updated"] = datetime.now().isoformat()
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"✅ Renamed: {renamed}")
        if failed:
            print(f"❌ Failed: {len(failed)}")
            for n, e in failed:
                print(f"  {n}: {e}")

    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    project = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path(".")
    sys.exit(main(project.resolve(), dry))
