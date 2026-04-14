#!/bin/bash

echo "🚀 Research Agent System - 설치 시작"
echo ""

# 현재 위치 확인
INSTALL_DIR=$(pwd)
echo "📍 설치 위치: $INSTALL_DIR"
echo ""

# 1. Python 패키지 설치
echo "📦 Python 패키지 설치 중..."
if pip install -r requirements.txt --break-system-packages; then
    echo "✅ Python 패키지 설치 완료"
else
    echo "⚠️  pip 설치 실패. 수동으로 설치하세요:"
    echo "   pip install pypdf2 --break-system-packages"
fi
echo ""

# 2. Skill 디렉토리 생성
echo "📁 Skill 디렉토리 생성 중..."
mkdir -p ~/.claude/skills/user
echo "✅ ~/.claude/skills/user 생성 완료"
echo ""

# 3. Skill 링크
echo "🔗 Skill 링크 생성 중..."
SKILL_LINK=~/.claude/skills/user/research-agent

# 기존 링크 제거
if [ -L "$SKILL_LINK" ] || [ -e "$SKILL_LINK" ]; then
    echo "   기존 링크 제거 중..."
    rm -f "$SKILL_LINK"
fi

# 새 링크 생성
if ln -s "$INSTALL_DIR/skills" "$SKILL_LINK"; then
    echo "✅ Skill 링크 생성 완료"
    echo "   $INSTALL_DIR/skills → $SKILL_LINK"
else
    echo "❌ Skill 링크 생성 실패"
    exit 1
fi
echo ""

# 4. 확인
echo "🔍 설치 확인 중..."
if [ -L "$SKILL_LINK" ]; then
    echo "✅ Skill 링크 확인됨"
    ls -la "$SKILL_LINK"
else
    echo "❌ Skill 링크 없음"
    exit 1
fi
echo ""

# 5. Consensus MCP 안내
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Consensus MCP 설정 (선택사항)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Consensus로 논문 검색하려면 다음 명령어를 실행하세요:"
echo ""
echo "  claude mcp add-json consensus '{\"type\":\"http\",\"url\":\"https://mcp.consensus.app/mcp\"}'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 6. 완료
echo "✅ 설치 완료!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 다음 단계:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 작업 폴더 생성:"
echo "   mkdir ~/Documents/research-test"
echo "   cd ~/Documents/research-test"
echo ""
echo "2. Claude Code 실행:"
echo "   claude"
echo ""
echo "3. 프로젝트 생성:"
echo "   > \"test-project 프로젝트 만들어줘\""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 즐거운 연구 되세요!"
