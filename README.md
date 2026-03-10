# 🇰🇷 Korean Patent MCP

> **Note:** This is a forked and enhanced version of the original [Tech-curator/korean-patent-mcp](https://github.com/Tech-curator/korean-patent-mcp).
> **안내:** 이 프로젝트는 원본 [Tech-curator/korean-patent-mcp](https://github.com/Tech-curator/korean-patent-mcp)를 포크하여 기능을 추가한 버전입니다.

> **[한국어 문서는 아래에 있습니다](#-기능) / Korean documentation below**

MCP (Model Context Protocol) server for KIPRIS (Korean Intellectual Property Rights Information Service) API.

## English Documentation

### Overview

This MCP server enables AI assistants (Claude Desktop, Cursor, Windsurf, etc.) to search and analyze Korean patents through natural language queries. It connects to the official KIPRIS Plus Open API provided by the Korean Intellectual Property Office (KIPO).

### Features

| Tool | Description |
|------|-------------|
| `kipris_search_patents` | Search patents by applicant name |
| `kipris_search_patents_by_title` | Search patents by invention title *(Added in this fork)* |
| `kipris_get_patent_detail` | Get detailed patent information by application number |
| `kipris_get_citing_patents` | Find patents that cite a specific patent |

### Quick Start

```bash
# Run directly without installation via uvx (Recommended for end users)
uvx --from git+https://github.com/jay-ahnlabio/korean-patent-mcp.git korean-patent-mcp

# Or install via Smithery
npx -y @smithery/cli install korean-patent-mcp --client claude

# For local development
git clone https://github.com/jay-ahnlabio/korean-patent-mcp.git
cd korean-patent-mcp
uv pip install -e .
```

### Requirements

- Python 3.10+
- KIPRIS Plus Open API Key ([Get your key here](https://plus.kipris.or.kr))

### Configuration

Set the `KIPRIS_API_KEY` environment variable:

```bash
export KIPRIS_API_KEY="your_api_key_here"
```

Or add to your MCP client configuration:

```json
{
  "mcpServers": {
    "korean-patent": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jay-ahnlabio/korean-patent-mcp.git",
        "korean-patent-mcp"
      ],
      "env": {
        "KIPRIS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Example Queries

- "Search for Samsung Electronics' registered patents"
- "Search for patents with 'Artificial Intelligence' in the title"
- "Get details for patent application number 1020200123456"
- "Find patents that cite application 1020180056789"

---

## 한국어 문서

한국 특허정보 검색서비스(KIPRIS) API를 위한 MCP(Model Context Protocol) 서버입니다.

Claude Desktop, Cursor, Windsurf 또는 다른 MCP 클라이언트와 연동하여 자연어로 한국 특허를 검색하고 분석할 수 있습니다.

[![Smithery](https://smithery.ai/badge/korean-patent-mcp)](https://smithery.ai/server/korean-patent-mcp)

## ✨ 기능

### Core Tools

| Tool | 설명 |
|------|------|
| `kipris_search_patents` | 출원인명으로 특허 검색 |
| `kipris_search_patents_by_title` | 발명의 명칭으로 특허 검색 *(포크 버전에서 추가됨)* |
| `kipris_get_patent_detail` | 출원번호로 특허 상세 정보 조회 |
| `kipris_get_citing_patents` | 특정 특허를 인용한 후행 특허 조회 |

### Extended Tools (향후 구현 예정)

- [ ] `kipris_get_cpc_codes` - CPC 분류 코드 조회
- [ ] `kipris_get_inventors` - 발명자 정보 조회
- [ ] `kipris_check_rejection` - 거절 여부 확인
- [ ] `kipris_analyze_rejection_reason` - 거절 사유 분석

## 🚀 설치 방법

### 방법 1: uvx를 사용한 직접 실행 (일반 사용자 권장)

```bash
# 설치 과정 없이 임시 환경에서 즉시 실행
uvx --from git+https://github.com/jay-ahnlabio/korean-patent-mcp.git korean-patent-mcp
```

### 방법 2: Smithery를 통한 설치

```bash
# Smithery CLI 설치 (처음 한 번만)
npm install -g @smithery/cli

# Korean Patent MCP 서버 설치
smithery install korean-patent-mcp --client claude
```

### 방법 3: 로컬 개발용 (저장소 클론 후)

```bash
# 저장소 클론
git clone https://github.com/jay-ahnlabio/korean-patent-mcp.git
cd korean-patent-mcp

# uv로 설치 (권장)
uv pip install -e .

# 또는 pip으로 설치
pip install -e .
```

### 요구사항

- Python 3.10+
- KIPRIS Plus Open API 키 ([발급 사이트](https://plus.kipris.or.kr))

## 🔧 설정

### API 키 설정

`.env` 파일을 생성하고 API 키를 설정합니다:

```bash
echo "KIPRIS_API_KEY=your_api_key_here" > .env
```

또는 환경변수로 설정:

```bash
export KIPRIS_API_KEY="your_api_key_here"
```

## 🔌 클라이언트 연동

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) 또는 
`%APPDATA%\Claude\claude_desktop_config.json` (Windows) 파일을 편집합니다:

```json
{
  "mcpServers": {
    "korean-patent": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jay-ahnlabio/korean-patent-mcp.git",
        "korean-patent-mcp"
      ],
      "env": {
        "KIPRIS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Cursor / Windsurf

MCP 설정에서 다음을 추가합니다:

```json
{
  "korean-patent": {
    "command": "uv",
    "args": ["run", "korean-patent-mcp"],
    "env": {
      "KIPRIS_API_KEY": "your_api_key_here"
    }
  }
}
```

## 📖 사용 예시

Claude Desktop에서 다음과 같이 질문할 수 있습니다:

### 특허 검색
```
삼성전자가 출원한 특허 중 등록된 것들을 보여줘
```

```
'인공지능'이 제목에 포함된 특허를 찾아줘
```

```
충북대학교 산학협력단의 최근 특허를 검색해줘
```

### 특허 상세 정보
```
출원번호 1020200123456의 특허 상세 정보를 알려줘
```

### 인용 특허 분석
```
출원번호 1020180056789를 인용한 특허들을 찾아줘
```

## 🧪 개발 & 테스트

### MCP Inspector로 테스트

```bash
npx @modelcontextprotocol/inspector uv run korean-patent-mcp
```

### Smithery Dev 모드

```bash
smithery dev
```

## 📁 프로젝트 구조

```
korean-patent-mcp/
├── pyproject.toml          # 패키지 설정 (uv/pip 호환)
├── smithery.yaml           # Smithery 배포 설정
├── README.md
├── .env.example
└── src/
    └── korean_patent_mcp/
        ├── __init__.py
        ├── server.py       # MCP 서버 & Tool 정의
        └── kipris_api.py   # KIPRIS API 클라이언트
```

## 🔍 API 응답 형식

모든 Tool은 `response_format` 파라미터를 지원합니다:

- `markdown` (기본값): 사람이 읽기 좋은 형식
- `json`: 프로그래밍 처리에 적합한 구조화된 형식

## ⚠️ 주의사항

- KIPRIS API는 호출 제한이 있을 수 있습니다
- 대량 검색 시 페이지네이션을 활용하세요
- API 키는 절대 공개 저장소에 커밋하지 마세요

## 📝 라이선스

MIT License

## 🤝 기여

버그 리포트, 기능 제안, PR 모두 환영합니다!

## 📞 Contact

### Fork Maintainer
- **GitHub**: [jay-ahnlabio](https://github.com/jay-ahnlabio)

### Original Author
- **Tech Curator**: [https://techcurator.kr](https://techcurator.kr)
- **DiME**: [https://www.dime.kr](https://www.dime.kr)
- **E-mail**: jkh25@techcurator.kr / ceo@techcurator.kr
---

Made with ❤️ for Korean patent research
