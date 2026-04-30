#!/usr/bin/env python3
"""DEPRECATED: 이 파일은 assemble_search_results.py 로 rename되었습니다.

호환성 wrapper. 출력 경로가 papers/consensus-results.md → papers/search-results/flow.md 로 변경됨.
신규 호출은 `python3 scripts/assemble_search_results.py {PROJECT} [--stage flow|research-gap]` 사용.

이 wrapper는 구 호출(`assemble_consensus_results.py {PROJECT}`)을 stage=flow로 forward.
"""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import warnings
warnings.warn(
    "assemble_consensus_results.py is deprecated; use assemble_search_results.py "
    "(--stage flow|research-gap). Forwarding to stage=flow.",
    DeprecationWarning,
    stacklevel=2,
)

import assemble_search_results

if __name__ == "__main__":
    # 기존 인터페이스: 첫 인자 = project. stage 인자 없음 → flow 기본.
    if len(sys.argv) < 2:
        print("usage: assemble_consensus_results.py {PROJECT}  (deprecated; use assemble_search_results.py)",
              file=sys.stderr)
        sys.exit(2)
    # argparse-friendly forward
    sys.argv = [sys.argv[0], sys.argv[1], "--stage", "flow"]
    assemble_search_results.main()
