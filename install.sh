#!/bin/bash

set -e  # 에러 발생 시 중단

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Research Agent System - 자동 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

INSTALL_DIR=$(pwd)
echo "📍 설치 위치: $INSTALL_DIR"
echo ""

# 1. Claude Code 설치 확인 및 설치
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Claude Code 설치 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    echo "✅ Claude Code 이미 설치됨: $CLAUDE_VERSION"
else
    echo "📦 Claude Code 설치 중..."
    
    # macOS 확인
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Homebrew 확인
        if command -v brew &> /dev/null; then
            echo "   Homebrew로 설치 중..."
            if brew install claude; then
                echo "✅ Claude Code 설치 완료"
            else
                echo "❌ Claude Code 설치 실패"
                echo ""
                echo "수동 설치가 필요합니다:"
                echo "1. https://claude.ai/download 방문"
                echo "2. macOS 버전 다운로드"
                echo "3. 설치 후 다시 ./install.sh 실행"
                exit 1
            fi
        else
            echo "❌ Homebrew가 설치되지 않았습니다."
            echo ""
            echo "옵션 1: Homebrew 설치 (추천)"
            echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            echo ""
            echo "옵션 2: 수동 설치"
            echo "https://claude.ai/download"
            exit 1
        fi
    else
        echo "❌ macOS가 아닙니다."
        echo "Claude Code를 수동으로 설치하세요: https://claude.ai/download"
        exit 1
    fi
fi
echo ""

# 2. Python 패키지 설치
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Python 패키지 설치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "requirements.txt" ]; then
    echo "📦 PyPDF2 설치 중..."
    if pip install -r requirements.txt --break-system-packages --quiet; then
        echo "✅ Python 패키지 설치 완료"
    else
        echo "⚠️  pip 설치 실패. 수동으로 설치하세요:"
        echo "   pip install pypdf2 --break-system-packages"
    fi
else
    echo "⚠️  requirements.txt 없음. PyPDF2 직접 설치 중..."
    pip install pypdf2 --break-system-packages --quiet && echo "✅ PyPDF2 설치 완료"
fi
echo ""

# 3. Skill 디렉토리 생성 및 링크
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Claude Skill 링크 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Skill 디렉토리 생성
echo "📁 ~/.claude/skills/user 디렉토리 생성 중..."
mkdir -p ~/.claude/skills/user
echo "✅ 디렉토리 생성 완료"
echo ""

# 기존 링크 제거
SKILL_LINK=~/.claude/skills/user/research-agent
if [ -L "$SKILL_LINK" ] || [ -e "$SKILL_LINK" ]; then
    echo "🔄 기존 Skill 링크 제거 중..."
    rm -f "$SKILL_LINK"
fi

# 새 링크 생성
echo "🔗 Skill 링크 생성 중..."
if ln -s "$INSTALL_DIR/skills" "$SKILL_LINK"; then
    echo "✅ Skill 링크 생성 완료"
    echo "   $INSTALL_DIR/skills → $SKILL_LINK"
else
    echo "❌ Skill 링크 생성 실패"
    exit 1
fi
echo ""

# 4. Projects 폴더 생성
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Projects 폴더 생성"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -d "projects" ]; then
    mkdir -p projects
    echo "✅ projects/ 폴더 생성 완료"
else
    echo "✅ projects/ 폴더 이미 존재"
fi
echo ""

# 5. Consensus MCP 설정 (선택사항)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Consensus MCP 설정 (선택사항)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Consensus MCP를 설정하시겠습니까? (논문 검색 기능)"
echo "y: 설정함 (추천)"
echo "n: 나중에 수동 설정"
echo ""
read -p "선택 (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📡 Consensus MCP 설정 중..."
    if claude mcp add-json consensus '{"type":"http","url":"https://mcp.consensus.app/mcp"}' 2>/dev/null; then
        echo "✅ Consensus MCP 설정 완료"
    else
        echo "⚠️  자동 설정 실패. 수동으로 설정하세요:"
        echo '   claude mcp add-json consensus '"'"'{"type":"http","url":"https://mcp.consensus.app/mcp"}'"'"
    fi
else
    echo "⏭️  Consensus MCP 건너뜀"
    echo ""
    echo "나중에 설정하려면 다음 명령어를 실행하세요:"
    echo '   claude mcp add-json consensus '"'"'{"type":"http","url":"https://mcp.consensus.app/mcp"}'"'"
fi
echo ""

# 6. 설치 확인
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  설치 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Claude Code 확인
if command -v claude &> /dev/null; then
    echo "✅ Claude Code: $(claude --version 2>/dev/null || echo 'installed')"
else
    echo "❌ Claude Code: 설치 안 됨"
fi

# Skill 링크 확인
if [ -L "$SKILL_LINK" ]; then
    echo "✅ Skill 링크: 정상"
else
    echo "❌ Skill 링크: 없음"
fi

# Python 패키지 확인
if python3 -c "import PyPDF2" 2>/dev/null; then
    echo "✅ PyPDF2: 설치됨"
else
    echo "⚠️  PyPDF2: 설치 안 됨"
fi

# Projects 폴더 확인
if [ -d "projects" ]; then
    echo "✅ Projects 폴더: 존재"
else
    echo "❌ Projects 폴더: 없음"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 설치 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 다음 단계:"
echo ""
echo "1. Claude Code 실행:"
echo "   claude"
echo ""
echo "2. 프로젝트 생성:"
echo '   > "test-project 프로젝트 만들어줘"'
echo ""
echo "3. 프로젝트 확인:"
echo "   ls -la projects/"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 사용 가능한 명령어:"
echo '   - "[이름] 프로젝트 만들어줘"'
echo '   - "작업 시작해줘" (Consensus 검색)'
echo '   - "새 논문 처리해줘"'
echo '   - "초안 작성해줘"'
echo ""
echo "🆘 문제 발생 시:"
echo "   - Skill 재설정: rm ~/.claude/skills/user/research-agent && ./install.sh"
echo "   - PyPDF2 재설치: pip install pypdf2 --break-system-packages"
echo ""
echo "🎉 즐거운 연구 되세요!"
echo ""
