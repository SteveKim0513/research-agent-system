#!/bin/bash

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Research Agent System - 스마트 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

INSTALL_DIR=$(pwd)
echo "📍 설치 위치: $INSTALL_DIR"
echo ""

# 설치 상태 추적
NEEDS_CLAUDE=false
NEEDS_PYTHON=false
NEEDS_SKILL=false
NEEDS_PROJECTS=false

# 1. Claude Code CLI 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Claude Code (CLI) 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    echo "✅ Claude Code 이미 설치됨: $CLAUDE_VERSION"
    echo "   ⏭️  설치 건너뜀"
else
    echo "❌ Claude Code (CLI) 없음"
    NEEDS_CLAUDE=true
fi
echo ""

# 2. Python 패키지 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Python 패키지 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if python3 -c "import PyPDF2" 2>/dev/null; then
    PYPDF_VERSION=$(python3 -c "import PyPDF2; print(PyPDF2.__version__)" 2>/dev/null || echo "unknown")
    echo "✅ PyPDF2 이미 설치됨: $PYPDF_VERSION"
    echo "   ⏭️  설치 건너뜀"
else
    echo "❌ PyPDF2 없음"
    NEEDS_PYTHON=true
fi
echo ""

# 3. Skill 링크 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Skill 링크 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SKILL_LINK=~/.claude/skills/user/research-agent

if [ -L "$SKILL_LINK" ]; then
    LINK_TARGET=$(readlink "$SKILL_LINK")
    if [ "$LINK_TARGET" = "$INSTALL_DIR/skills" ]; then
        echo "✅ Skill 링크 이미 설정됨"
        echo "   ⏭️  설정 건너뜀"
    else
        echo "⚠️  Skill 링크가 다른 위치를 가리킴"
        NEEDS_SKILL=true
    fi
else
    echo "❌ Skill 링크 없음"
    NEEDS_SKILL=true
fi
echo ""

# 4. Projects 폴더 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Projects 폴더 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -d "projects" ]; then
    echo "✅ projects/ 폴더 이미 존재"
    echo "   ⏭️  생성 건너뜀"
else
    echo "❌ projects/ 폴더 없음"
    NEEDS_PROJECTS=true
fi
echo ""

# 모든 것이 설치되어 있으면 종료
if [ "$NEEDS_CLAUDE" = false ] && [ "$NEEDS_PYTHON" = false ] && \
   [ "$NEEDS_SKILL" = false ] && [ "$NEEDS_PROJECTS" = false ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✨ 모든 것이 이미 설치되어 있습니다!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎯 바로 사용 가능합니다:"
    echo "   claude"
    echo '   > "test-project 프로젝트 만들어줘"'
    echo ""
    exit 0
fi

# 필요한 항목만 설치
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 필요한 항목 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Claude Code 설치
if [ "$NEEDS_CLAUDE" = true ]; then
    echo "📦 Claude Code CLI 설치 필요"
    echo ""
    echo "설치 방법:"
    echo "  npm install -g @anthropic-ai/claude-code"
    echo ""
    
    read -p "지금 npm으로 설치하시겠습니까? (y/n): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v npm &> /dev/null; then
            echo "   설치 중..."
            if npm install -g @anthropic-ai/claude-code; then
                echo "✅ Claude Code 설치 완료"
            else
                echo "❌ 설치 실패"
                exit 1
            fi
        else
            echo "❌ npm이 없습니다. Node.js를 먼저 설치하세요:"
            echo "   brew install node"
            exit 1
        fi
    else
        echo "⏭️  건너뜀. 나중에 수동 설치하세요."
        exit 0
    fi
    echo ""
fi

# Python 패키지 설치
if [ "$NEEDS_PYTHON" = true ]; then
    echo "📦 PyPDF2 설치 중..."
    if pip3 install pypdf2 --break-system-packages --quiet 2>/dev/null; then
        echo "✅ PyPDF2 설치 완료"
    else
        echo "⚠️  설치 실패 (선택사항)"
    fi
    echo ""
fi

# Skill 링크 생성
if [ "$NEEDS_SKILL" = true ]; then
    echo "🔗 Skill 링크 생성 중..."
    mkdir -p ~/.claude/skills/user
    rm -f "$SKILL_LINK"
    if ln -s "$INSTALL_DIR/skills" "$SKILL_LINK"; then
        echo "✅ Skill 링크 생성 완료"
    else
        echo "❌ 링크 생성 실패"
        exit 1
    fi
    echo ""
fi

# Projects 폴더 생성
if [ "$NEEDS_PROJECTS" = true ]; then
    echo "📁 Projects 폴더 생성 중..."
    mkdir -p projects
    echo "✅ projects/ 폴더 생성 완료"
    echo ""
fi

# Consensus MCP 설정
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Consensus MCP 설정 (선택사항)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Consensus MCP를 설정하시겠습니까? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if claude mcp add-json consensus '{"type":"http","url":"https://mcp.consensus.app/mcp"}' 2>/dev/null; then
        echo "✅ Consensus MCP 설정 완료"
    else
        echo "⚠️  나중에 Claude에서 설정하세요"
    fi
else
    echo "⏭️  건너뜀"
fi
echo ""

# 최종 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 설치 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 다음 단계:"
echo "   claude"
echo '   > "test-project 프로젝트 만들어줘"'
echo ""
echo "🎉 즐거운 연구 되세요!"
echo ""
