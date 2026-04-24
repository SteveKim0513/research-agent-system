#!/usr/bin/env python3
"""
backfill_axis_tags.py — 파일명 기반 specific-match로 axis_tags 백필.

**태그 선별 기준**: 각 태그는 **3-8편**만 달도록 엄격히 제한.
- steelman: 본 thesis의 'impurity problem/latent variable 공격'에 직접 반론 제공하는 핵심 논문
- delta: 본 thesis와 **직접 경쟁**하는 대안 프레임 (Doebel/McCraw 등)
- minority: 분야가 잊은 전통의 **원전·복원** 작업 (Luria/Vygotsky/Indigenous/postcolonial)
- definition: 핵심 구성개념의 **표준 정의** 제공 (Ryan/Deci/Rothbart/DFT)

사용: python3 scripts/backfill_axis_tags.py <project_name> [--dry-run]
"""
import re
import sys
from pathlib import Path


# 파일명 prefix (Author_Year까지) 기반 explicit tag
# 한 논문이 여러 태그 가능
TAG_RULES = {
    # ─── steelman: 본 thesis의 가장 강한 반론 (15편 이내) ───
    "steelman": [
        "Loffler_2024",        # common factor = speed (central Steelman)
        "Loffler_2025",        # ERP follow-up
        "Sambol_2023",         # Miyake 3-factor CFA fails
        "Jewsbury_2016",       # CHC re-analysis, EF dissolves
        "Vermeent_2025",       # replicates Löffler
        "Karr_2018",           # meta-CFA, no consistent model
        "Cepeda_2013",         # processing speed impurity
        "Hedge_2018",          # reliability paradox
        "Reymermet_2025",      # no attention control factor
        "Paap_2016",           # test-retest impurity
        "Demetriou_2024",      # EF = relational integration only
        "Frischkorn_2019",     # EF = processing speed
        "Prencipe_2011",       # single-factor (challenges 4-quadrant separability)
        "Rosales_2023",        # network modeling critique
        "VanDerSluis_2007",    # inhibition disappears when naming controlled
    ],

    # ─── delta: 직접 경쟁하는 대안 프레임 (10편 이내) ───
    "delta": [
        "Doebel_2020",         # Rethinking EF (primary competitor)
        "DoebelLillard_2023",  # play foster development
        "Perone_2020",         # Dynamical reconceptualization
        "McCraw_2024",         # DFT autonomy-centered (surface overlap with thesis)
        "BussSpencer_2014",    # emergent executive DFT
        "Spencer_2025",        # WOLVES 2.0 moving beyond components
        "Zelazo_2022",         # Reconciling context-dependency
        "Miller_2023",         # Universality vs context-specificity (same dichotomy)
        "Munakata_2021",       # EF in social context
        "Niebaum_2022",        # EF training contextual framework
        "Niebaum_2025",        # Adaptive habits
        "Ibbotson_2023",       # Mechanisms of change
        "Zink_2020",           # Distributed EF
    ],

    # ─── minority: 잊힌 전통 복원 (15편 이내) ───
    "minority": [
        "Bodrova_2011",        # Vygotsky/Luria insights (centerpiece)
        "Bodrova_2013",
        "Bodrova_2015",
        "Wozniak_1972",        # Luria verbal regulation
        "Glozman_2007",        # Russian neuropsychology history
        "Goldberg_2019",       # Luria legacy
        "Panikratova_2022",    # Luria-Vygotsky neuroimaging
        "Smolucha_2021",       # Vygotsky theory in play
        "Dvorakova_2025",      # All psychologies are indigenous
        "PePua_2020",          # Cross-indigenous psychology
        "Ciofalo_2022",        # Indigenous community psychologies
        "Mcnamara_2018",       # Decolonizing community psychology
        "Bansal_2022",         # Critical indigenous
        "Kim_2002",            # Indigenous/cross-cultural epistemology
        "Gulnazanjum_nodate",  # Anjum 2024 cross-cultural equity
        "Jukes_2024",          # Cross-cultural EF adaptation
        "Gutchess_2022",       # Culture in cognition
        "Amir_2020",           # Cross-cultural developmental psych WEIRD
    ],

    # ─── definition: 핵심 구성개념의 표준 정의 원전 (10편 이내) ───
    "definition": [
        "Ryan_2000",           # SDT foundational (for voluntariness axis)
        "Ryan_2020",           # SDT definitions update
        "Deci_2008",           # SDT macrotheory
        "Niemiec_2009",        # SDT education applied
        "Rothbart_2007",       # Effortful control / executive attention
        "Zhou_2011",           # EC vs EF integration
        "Zelazo_2012",         # Hot/cool EF definitions (target of critique)
        "BussSpencer_2014",    # DFT Hebbian trace (for fixity axis)
        "McCraw_2024",         # DFT autonomy framework
        "EcclesWigfield_2020", # Expectancy-value theory (for resource model)
    ],
}


def get_paper_prefix(filename: str) -> str:
    """'Miyake_2000_...-analysis.md' → 'Miyake_2000'."""
    name = filename.replace("-analysis.md", "")
    parts = name.split("_")
    if len(parts) >= 2:
        return "_".join(parts[:2])  # Author_Year
    return name


def classify_by_filename(filename: str) -> list[str]:
    """파일명 prefix 기반 정확 매칭."""
    prefix = get_paper_prefix(filename)
    tags = []
    for tag, papers in TAG_RULES.items():
        if prefix in papers:
            tags.append(tag)
    return tags


def inject_tags(content: str, new_tags: list[str]) -> tuple[str, bool]:
    """axis_tags 라인 삽입 또는 병합."""
    existing_m = re.search(r"\*\*axis_tags\*\*\s*:\s*\[([^\]]*)\]", content)
    if existing_m:
        raw = existing_m.group(1)
        existing = set(re.findall(r"['\"]([a-z_]+)['\"]", raw))
        merged = sorted(existing | set(new_tags))
        if merged == sorted(existing):
            return content, False
        new_line = '**axis_tags**: [' + ", ".join(f'"{t}"' for t in merged) + ']'
        return re.sub(r"\*\*axis_tags\*\*\s*:\s*\[[^\]]*\]", new_line, content), True

    if not new_tags:
        return content, False

    tags_line = '- **axis_tags**: [' + ", ".join(f'"{t}"' for t in new_tags) + ']'
    meta_m = re.search(r"(##\s+📎?\s*메타[^\n]*\n)", content)
    if meta_m:
        insert_at = meta_m.end()
        return content[:insert_at] + tags_line + "\n" + content[insert_at:], True

    return content.rstrip() + "\n\n## 📎 메타\n\n" + tags_line + "\n", True


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    project = argv[1]
    dry_run = "--dry-run" in argv

    analyzed = Path("projects") / project / "papers" / "analyzed"
    if not analyzed.exists():
        print(f"⚠️  {analyzed} 없음", file=sys.stderr)
        return 1

    stats = {"total": 0, "tagged": 0, "changed": 0, "untagged": 0}
    tag_counts = {"steelman": 0, "delta": 0, "minority": 0, "definition": 0}
    tag_members: dict[str, list[str]] = {k: [] for k in tag_counts}

    for md in sorted(analyzed.glob("*-analysis.md")):
        stats["total"] += 1
        tags = classify_by_filename(md.name)
        for t in tags:
            tag_counts[t] += 1
            tag_members[t].append(md.name[:50])
        if not tags:
            stats["untagged"] += 1
            continue
        stats["tagged"] += 1

        content = md.read_text(encoding="utf-8")
        new_content, changed = inject_tags(content, tags)
        if changed:
            stats["changed"] += 1
            if not dry_run:
                md.write_text(new_content, encoding="utf-8")

    print("\n=== 요약 ===")
    print(f"Total: {stats['total']}")
    print(f"Tagged: {stats['tagged']} ({stats['tagged']*100//max(stats['total'],1)}%)")
    print(f"Changed: {stats['changed']}")
    print(f"Untagged: {stats['untagged']} (axis 1 coverage only)")

    print("\n태그별 카운트 및 구성원:")
    for k, members in tag_members.items():
        print(f"\n  {k}: {tag_counts[k]}편")
        for m in members:
            print(f"    - {m}")

    if dry_run:
        print("\n(DRY RUN — 실제 쓰기 안 함)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
