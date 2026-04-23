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
NEEDS_CONSENSUS=false

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

# 5. Consensus MCP 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Consensus MCP 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v claude &> /dev/null; then
    if claude mcp list 2>/dev/null | grep -q "consensus.*Connected"; then
        echo "✅ Consensus MCP 이미 연결됨"
        echo "   ⏭️  설정 건너뜀"
    elif claude mcp list 2>/dev/null | grep -q "consensus"; then
        echo "⚠️  Consensus MCP 설정됨 (연결 끊김 — 재인증 필요)"
        echo ""
        echo "   👉 Claude Code 실행 후 재인증하세요:"
        echo "      claude"
        echo "      > /mcp"
        echo "      → consensus 선택 → Authenticate"
    else
        echo "❌ Consensus MCP 미설정"
        NEEDS_CONSENSUS=true
    fi
else
    echo "⏭️  Claude Code 설치 후 설정 예정"
    NEEDS_CONSENSUS=true
fi
echo ""

# 모든 것이 설치되어 있으면 종료
if [ "$NEEDS_CLAUDE" = false ] && [ "$NEEDS_PYTHON" = false ] && \
   [ "$NEEDS_SKILL" = false ] && [ "$NEEDS_PROJECTS" = false ] && \
   [ "$NEEDS_CONSENSUS" = false ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✨ 모든 것이 이미 설치되어 있습니다!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 Consensus 로그인 확인:"
    echo "   비로그인 시 검색당 최대 3개 논문만 반환됩니다."
    echo "   아직 인증하지 않았다면:"
    echo "   1) https://consensus.app/sign-up/?utm_source=claude_code&auth=claude_code 에서 가입"
    echo "   2) claude 실행 후 /mcp → consensus → Authenticate"
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

# Activity Log hooks 자동 구성 (Claude Code hooks)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🪝 Activity Log hooks 구성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

HOOKS_FILE="$INSTALL_DIR/.claude/settings.json"
if [ -f "$HOOKS_FILE" ]; then
    if grep -q '"UserPromptSubmit"' "$HOOKS_FILE" 2>/dev/null; then
        echo "✅ Activity Log hooks 이미 구성됨"
        echo "   📄 $HOOKS_FILE"
    else
        echo "⚠️  $HOOKS_FILE 존재하나 hooks 섹션 없음."
        echo "   → 수동 확인 필요 (기존 설정 보존을 위해 자동 덮어쓰기 안 함)"
    fi
else
    echo "❌ .claude/settings.json 없음 — 레포 clone이 완전하지 않을 수 있습니다."
    echo "   git pull 후 다시 실행하거나 수동으로 .claude/settings.json을 생성하세요."
fi
echo ""
echo "💡 Hooks는 사용자의 명령·turn·bash 이벤트를 자동 로깅합니다."
echo "   로그 파일: projects/{프로젝트}/activity.log (가시)"
echo "   끄고 싶으면 .claude/settings.json의 hooks 섹션을 지우세요."
echo ""

# Consensus MCP 설정 (필수)
if [ "$NEEDS_CONSENSUS" = true ]; then
    echo "📡 Consensus MCP 설정 중..."
    if command -v claude &> /dev/null; then
        if claude mcp add-json consensus '{"type":"http","url":"https://mcp.consensus.app/mcp"}' 2>/dev/null; then
            echo "✅ Consensus MCP 설정 완료"
        else
            echo "⚠️  자동 설정 실패. 수동으로 설정하세요:"
            echo "   claude mcp add-json consensus '{\"type\":\"http\",\"url\":\"https://mcp.consensus.app/mcp\"}'"
        fi
    else
        echo "⚠️  Claude Code 설치 후 아래 명령어로 설정하세요:"
        echo "   claude mcp add-json consensus '{\"type\":\"http\",\"url\":\"https://mcp.consensus.app/mcp\"}'"
    fi
    echo ""
fi

# Consensus 계정 로그인 안내 (필수)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Consensus 계정 로그인 (필수)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  비로그인 상태에서는 검색당 최대 3개 논문만 반환됩니다."
echo "   무료 계정 연결 시 검색당 10-20개 결과를 받을 수 있습니다."
echo ""
echo "1️⃣  무료 가입 (브라우저):"
echo "   https://consensus.app/sign-up/?utm_source=claude_code&auth=claude_code"
echo ""
echo "2️⃣  Claude Code 실행 후 아래 명령어로 인증:"
echo "   claude"
echo "   > /mcp"
echo "   → consensus 선택 → Authenticate"
echo ""
read -p "지금 브라우저에서 가입 페이지를 여시겠습니까? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        open "https://consensus.app/sign-up/?utm_source=claude_code&auth=claude_code"
        echo "✅ 브라우저를 열었습니다. 가입 후 Claude Code에서 /mcp 로 인증하세요."
    elif command -v xdg-open &> /dev/null; then
        xdg-open "https://consensus.app/sign-up/?utm_source=claude_code&auth=claude_code"
        echo "✅ 브라우저를 열었습니다. 가입 후 Claude Code에서 /mcp 로 인증하세요."
    else
        echo "⚠️  브라우저를 자동으로 열 수 없습니다. 위 URL을 직접 방문하세요."
    fi
else
    echo "⏭️  나중에 위 URL에서 가입하고 /mcp 로 인증하세요."
fi
echo ""

# 최종 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 설치 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 다음 단계:"
echo "   1. claude 실행"
echo "   2. /mcp 로 Consensus 인증 (위 안내 참조)"
echo '   3. "test-project 프로젝트 만들어줘"'
echo ""
echo "🎉 즐거운 연구 되세요!"
echo ""
