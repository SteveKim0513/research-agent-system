# scripts/archive/

일회성 migration / legacy 유틸리티 보관소. 현행 파이프라인은 이 파일들을 참조하지 않는다.

## 보관 스크립트

| 파일 | 용도 | 최종 사용 |
|------|------|----------|
| `migrate_v2.py` | v1 → v2 프로젝트 폴더 구조 마이그레이션 (`flow/`, `chapters/` 분리 · 루트 `work-plan.md`) | 2026-03 전후, v2 아키텍처 전환 시 |
| `backfill_axis_tags.py` | paper-analyst 분석 결과에 `axis_tags` 필드 후처리 주입 | 2026-03, 축 태깅 도입 시 |
| `rename_to_full_title.py` | `papers/collected/` PDF 파일명 정규화 (해시 → 전체 제목) | 2026-03 이전, 파일명 스키마 전환 시 |

## 재사용 조건

기존 v1 프로젝트를 새 구조로 올려야 하는 경우에만 `migrate_v2.py` 사용. 다른 둘은 일회성이며 재사용 시 스크립트 로직 재검토 필요.
