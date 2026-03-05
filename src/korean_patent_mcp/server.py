"""
Korean Patent MCP Server
한국 특허정보 검색서비스를 위한 MCP 서버 (Smithery Container 배포용)
"""
import json
import os
import sys
from typing import Optional

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware

from .kipris_api import KiprisAPIClient, KiprisConfig
from .middleware import SmitheryConfigMiddleware, smithery_context


# =========================================================================
# Global Client
# =========================================================================

_kipris_client: Optional[KiprisAPIClient] = None
_init_error: Optional[str] = None


def get_kipris_client() -> Optional[KiprisAPIClient]:
    """KIPRIS API 클라이언트 가져오기"""
    global _kipris_client, _init_error
    
    if _kipris_client is None and _init_error is None:
        try:
            config = KiprisConfig.from_env()
            _kipris_client = KiprisAPIClient(config)
        except ValueError as e:
            _init_error = str(e)
    
    return _kipris_client


def get_init_error() -> Optional[str]:
    return _init_error


def init_client_with_key(api_key: str) -> None:
    """API 키로 클라이언트 초기화"""
    global _kipris_client, _init_error
    try:
        os.environ["KIPRIS_API_KEY"] = api_key
        config = KiprisConfig(api_key=api_key)
        _kipris_client = KiprisAPIClient(config)
        _init_error = None
    except ValueError as e:
        _init_error = str(e)


# =========================================================================
# Config Access Helpers (per-request configuration)
# =========================================================================

def get_request_config() -> dict:
    """Get full config from current request context."""
    # ContextVar에서 직접 설정을 가져옴 (middleware에서 저장한 값)
    return smithery_context.get()


def get_config_value(key: str, default=None):
    """Get a specific config value from current request."""
    config = get_request_config()
    return config.get(key, default)


# =========================================================================
# Formatting Helpers
# =========================================================================

def format_patent_markdown(patent: dict, detailed: bool = False) -> str:
    lines = []
    lines.append(f"### {patent.get('title', '제목 없음')}")
    lines.append("")
    lines.append(f"- **출원번호**: {patent.get('application_number', '-')}")
    lines.append(f"- **출원일**: {patent.get('application_date', '-')}")
    lines.append(f"- **출원인**: {patent.get('applicant', '-')}")
    lines.append(f"- **등록상태**: {patent.get('registration_status', '-')}")
    
    if patent.get('opening_number'):
        lines.append(f"- **공개번호**: {patent.get('opening_number')} ({patent.get('opening_date', '-')})")
    if patent.get('registration_number'):
        lines.append(f"- **등록번호**: {patent.get('registration_number')} ({patent.get('registration_date', '-')})")
    if detailed:
        if patent.get('ipc_number'):
            lines.append(f"- **IPC 분류**: {patent.get('ipc_number')}")
        if patent.get('abstract'):
            lines.append("")
            lines.append("**초록**:")
            lines.append(f"> {patent.get('abstract')[:500]}...")
    
    return "\n".join(lines)


def format_search_result_markdown(result: dict) -> str:
    lines = []
    lines.append("## 검색 결과")
    lines.append("")
    lines.append(f"총 **{result['total_count']:,}**건 중 {len(result['patents'])}건 표시 (페이지 {result['page']})")
    lines.append("")
    
    if not result['patents']:
        lines.append("검색 결과가 없습니다.")
        return "\n".join(lines)
    
    for i, patent in enumerate(result['patents'], 1):
        lines.append("---")
        lines.append(f"**[{i}]** {patent.get('title', '제목 없음')}")
        lines.append(f"- 출원번호: `{patent.get('application_number', '-')}`")
        lines.append(f"- 출원인: {patent.get('applicant', '-')}")
        lines.append(f"- 상태: {patent.get('registration_status', '-')}")
        lines.append("")
    
    if result.get('has_more'):
        lines.append("---")
        lines.append(f"📄 다음 페이지: `page={result['next_page']}`")
    
    return "\n".join(lines)


def format_citing_patents_markdown(citations: list, base_app_num: str) -> str:
    lines = []
    lines.append("## 인용 특허 조회 결과")
    lines.append("")
    lines.append(f"기준 특허 `{base_app_num}`를 인용한 후행 특허: **{len(citations)}**건")
    lines.append("")
    
    if not citations:
        lines.append("이 특허를 인용한 후행 특허가 없습니다.")
        return "\n".join(lines)
    
    for i, cite in enumerate(citations, 1):
        lines.append("---")
        lines.append(f"**[{i}]** 출원번호: `{cite.get('citing_application_number', '-')}`")
        lines.append(f"- 상태: {cite.get('status_name', '-')} ({cite.get('status_code', '-')})")
        lines.append(f"- 인용유형: {cite.get('citation_type_name', '-')}")
        lines.append("")
    
    return "\n".join(lines)


# =========================================================================
# MCP Server Setup
# =========================================================================

# Disable DNS rebinding protection to allow Smithery to connect
# Or explicitly allow Smithery origins
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,  # Disable for Smithery compatibility
)

mcp = FastMCP("korean_patent_mcp", transport_security=transport_security)


# =========================================================================
# Tool Definitions
# =========================================================================

@mcp.tool(name="kipris_search_patents")
async def kipris_search_patents(
    applicant_name: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    response_format: str = "markdown"
) -> str:
    """출원인명으로 한국 특허를 검색합니다.
    
    Args:
        applicant_name: 출원인명 (필수, 예: '삼성전자', '카카오뱅크')
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과 수 (기본값: 20, 최대: 100)
        status: 상태 필터 ('A': 공개, 'R': 등록, 'J': 거절, None: 전체)
        response_format: 응답 형식 ('markdown' 또는 'json')
    """
    # Get API key from session config or environment
    api_key = get_config_value("kiprisApiKey") or os.getenv("KIPRIS_API_KEY", "")
    if api_key:
        init_client_with_key(api_key)
    
    client = get_kipris_client()
    if client is None:
        error = get_init_error() or "API 클라이언트 초기화 실패. KIPRIS_API_KEY를 설정해주세요."
        return f"❌ 오류: {error}"
    
    try:
        result = await client.search_patents_by_applicant(
            applicant_name=applicant_name,
            page=page,
            page_size=min(page_size, 100),
            status=status or ""
        )
        
        if response_format == "json":
            return json.dumps(result, ensure_ascii=False, indent=2)
        return format_search_result_markdown(result)
    except Exception as e:
        return f"❌ 검색 오류: {str(e)}"


@mcp.tool(name="kipris_search_patents_by_title")
async def kipris_search_patents_by_title(
    title: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    response_format: str = "markdown"
) -> str:
    """발명의 명칭으로 한국 특허를 검색합니다.
    
    Args:
        title: 발명의 명칭 (필수, 예: '인공지능', '반도체')
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과 수 (기본값: 20, 최대: 100)
        status: 상태 필터 ('A': 공개, 'R': 등록, 'J': 거절, None: 전체)
        response_format: 응답 형식 ('markdown' 또는 'json')
    """
    # Get API key from session config or environment
    api_key = get_config_value("kiprisApiKey") or os.getenv("KIPRIS_API_KEY", "")
    if api_key:
        init_client_with_key(api_key)
    
    client = get_kipris_client()
    if client is None:
        error = get_init_error() or "API 클라이언트 초기화 실패. KIPRIS_API_KEY를 설정해주세요."
        return f"❌ 오류: {error}"
    
    try:
        result = await client.search_patents_by_title(
            title=title,
            page=page,
            page_size=min(page_size, 100),
            status=status or ""
        )
        
        if response_format == "json":
            return json.dumps(result, ensure_ascii=False, indent=2)
        return format_search_result_markdown(result)
    except Exception as e:
        return f"❌ 검색 오류: {str(e)}"


@mcp.tool(name="kipris_get_patent_detail")
async def kipris_get_patent_detail(
    application_number: str,
    response_format: str = "markdown"
) -> str:
    """출원번호로 특허의 상세 정보를 조회합니다.
    
    Args:
        application_number: 출원번호 (필수, 예: '1020200123456')
        response_format: 응답 형식 ('markdown' 또는 'json')
    """
    # Get API key from session config or environment
    api_key = get_config_value("kiprisApiKey") or os.getenv("KIPRIS_API_KEY", "")
    if api_key:
        init_client_with_key(api_key)
    
    client = get_kipris_client()
    if client is None:
        return f"❌ 오류: {get_init_error() or 'API 클라이언트 초기화 실패'}"
    
    app_num = application_number.replace("-", "")
    
    try:
        result = await client.get_patent_detail(app_num)
        if result is None:
            return f"❌ 출원번호 `{application_number}`에 해당하는 특허를 찾을 수 없습니다."
        
        if response_format == "json":
            return json.dumps(result, ensure_ascii=False, indent=2)
        return format_patent_markdown(result, detailed=True)
    except Exception as e:
        return f"❌ 조회 오류: {str(e)}"


@mcp.tool(name="kipris_get_citing_patents")
async def kipris_get_citing_patents(
    application_number: str,
    response_format: str = "markdown"
) -> str:
    """특정 특허를 인용한 후행 특허들을 조회합니다.
    
    Args:
        application_number: 기준 특허의 출원번호 (필수)
        response_format: 응답 형식 ('markdown' 또는 'json')
    """
    # Get API key from session config or environment
    api_key = get_config_value("kiprisApiKey") or os.getenv("KIPRIS_API_KEY", "")
    if api_key:
        init_client_with_key(api_key)
    
    client = get_kipris_client()
    if client is None:
        return f"❌ 오류: {get_init_error() or 'API 클라이언트 초기화 실패'}"
    
    app_num = application_number.replace("-", "")
    
    try:
        result = await client.get_citing_patents(app_num)
        
        if response_format == "json":
            return json.dumps({
                "base_application_number": app_num,
                "citing_count": len(result),
                "citing_patents": result
            }, ensure_ascii=False, indent=2)
        return format_citing_patents_markdown(result, app_num)
    except Exception as e:
        return f"❌ 조회 오류: {str(e)}"


# =========================================================================
# Server Entry Point
# =========================================================================

def main():
    """서버 실행 진입점"""
    transport_mode = os.getenv("TRANSPORT", "stdio")
    
    if transport_mode == "http":
        # HTTP mode for Smithery Container deployment
        print("Korean Patent MCP Server starting in HTTP mode...", file=sys.stderr)
        
        # Setup Starlette app with streamable HTTP
        # DNS rebinding protection is disabled via transport_security above
        app = mcp.streamable_http_app()
        
        # IMPORTANT: Add CORS middleware for browser-based clients
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )
        
        # Apply SmitheryConfigMiddleware for per-request config extraction
        app = SmitheryConfigMiddleware(app)
        
        # Use Smithery-required PORT environment variable
        port = int(os.environ.get("PORT", 8081))
        print(f"Listening on port {port}", file=sys.stderr)
        
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
    else:
        # Default stdio mode for local development
        print("Korean Patent MCP Server starting in stdio mode...", file=sys.stderr)
        mcp.run()


if __name__ == "__main__":
    main()
