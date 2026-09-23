import json
import logging
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from corp.models import Company, Channel
from ai_core.llm_gateway import OllamaClient
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)

DEFAULT_FALLBACK_MODELS = [
    "gemma4-ex-llmfan46:26b",
    "llama3:8b",
    "mistral:7b",
    "qwen2.5:7b",
    "phi3:mini",
]

def get_available_ollama_models() -> List[str]:
    """
    로컬 Ollama 인스턴스에 설치된 모델 태그 목록을 조회합니다.
    Ollama 서버가 비활성화되어 있거나 오류 발생 시 기본 추천 모델 목록을 반환합니다.
    """
    try:
        client = OllamaClient()
        data = client.list_models()
        models = [m.get("name") for m in data.get("models", []) if m.get("name")]
        if models:
            return sorted(models)
    except Exception as e:
        logger.warning(f"Failed to fetch models from Ollama: {e}")
    return DEFAULT_FALLBACK_MODELS


def generate_company_lore_with_ai(name_or_theme: str, industry: str = "", model_name: str = None) -> Dict[str, str]:
    """
    입력된 키워드 또는 테마를 바탕으로 AI(Ollama)가 전문적인 회사 배경 스토리 및 미션을 생성합니다.
    """
    selected_model = model_name or "gemma4-ex-llmfan46:26b"
    
    prompt = f"""당신은 혁신 기업 브랜딩 전문가이자 시나리오 작가입니다.
사용자가 제안한 다음 키워드 및 테마를 바탕으로 가상 AI 기업의 매력적이고 전문적인 프로필을 한국어로 작성해주세요.

[입력 정보]
- 테마 / 키워드: {name_or_theme}
- 산업 분야(있을 경우): {industry or '자동 제안 필요'}

[요청 사항]
1. 제안된 테마에 걸맞은 혁신적이고 세련된 회사명(name)을 제안하거나 정제해주세요.
2. 구체적인 산업 분야(industry)를 1줄로 정의해주세요.
3. 회사의 배경 스토리, 미션, 핵심 비즈니스 모델, AI 에이전트들이 가져야 할 철학(description)을 2~3개 문단으로 상세히 작성해주세요.

[응답 형식 - 반드시 아래 JSON 형식만 정확히 출력하십시오]
```json
{{
  "name": "회사명",
  "industry": "산업 분야",
  "description": "상세한 기업 배경 스토리 및 미션"
}}
```
"""
    try:
        llm = ChatOllama(model=selected_model, temperature=0.7)
        response_text = llm.invoke(prompt).content
        
        # JSON 블록 추출
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
            
        data = json.loads(json_str)
        return {
            "name": data.get("name", name_or_theme),
            "industry": data.get("industry", industry or "AI 테크"),
            "description": data.get("description", "")
        }
    except Exception as e:
        logger.error(f"AI Lore generation failed: {e}")
        # 오류 시 기본 fallback 텍스트 구성
        return {
            "name": name_or_theme,
            "industry": industry or "신성장 비즈니스",
            "description": f"{name_or_theme}을(를) 중심으로 전 세계 시장을 선도하는 지능형 AI 가상 법인입니다. 각 분야의 자율 에이전트들이 협력하여 혁신적인 가치를 창출합니다."
        }


def create_company(
    owner: User,
    name: str,
    industry: str = "",
    description: str = "",
    default_llm_model: str = "gemma4-ex-llmfan46:26b"
) -> Company:
    """새로운 가상 법인을 설립하고 기본 채널을 자동 구성합니다."""
    company = Company.objects.create(
        owner=owner,
        name=name,
        industry=industry,
        description=description,
        default_llm_model=default_llm_model or "gemma4-ex-llmfan46:26b",
    )
    # 회사 전용 기본 general 채널 생성
    Channel.objects.get_or_create(
        company=company,
        name="general",
        defaults={"description": f"{company.name} 전사 공식 커뮤니케이션 채널"}
    )
    return company


def update_company(
    company: Company,
    name: str = None,
    industry: str = None,
    description: str = None,
    default_llm_model: str = None
) -> Company:
    """회사 정보 및 기본 LLM 모델을 갱신합니다."""
    if name is not None:
        company.name = name
    if industry is not None:
        company.industry = industry
    if description is not None:
        company.description = description
    if default_llm_model is not None:
        company.default_llm_model = default_llm_model
    company.save()
    return company


def get_user_companies(user: User):
    """사용자가 소유한 모든 활성 회사를 반환합니다."""
    return Company.objects.filter(owner=user, is_active=True).order_by('-created_at')


def get_active_company(request) -> Optional[Company]:
    """
    현재 세션의 활성 회사를 반환합니다.
    세션에 없거나 유효하지 않으면 첫 번째 회사를 활성화하고, 회사가 없으면 기본 회사를 자동 생성합니다.
    """
    if not request.user.is_authenticated:
        return None

    active_id = request.session.get("active_company_id")
    if active_id:
        try:
            company = Company.objects.filter(id=active_id, owner=request.user, is_active=True).first()
            if company:
                return company
        except Exception:
            pass

    # 활성 회사가 없거나 만료된 경우 첫 번째 회사 선택
    company = Company.objects.filter(owner=request.user, is_active=True).first()
    if not company:
        company = create_company(
            owner=request.user,
            name=f"{request.user.username}의 AI 법인",
            industry="지능형 소프트웨어 & AI 에이전트",
            description=f"{request.user.username} CEO가 지휘하는 차세대 자율 AI 기업입니다.",
            default_llm_model="gemma4-ex-llmfan46:26b"
        )

    request.session["active_company_id"] = str(company.id)
    return company


def set_active_company(request, company_id: str) -> Optional[Company]:
    """활성 회사를 세션에 저장하고 전환합니다."""
    if not request.user.is_authenticated:
        return None
    company = Company.objects.filter(id=company_id, owner=request.user, is_active=True).first()
    if company:
        request.session["active_company_id"] = str(company.id)
        return company
    return None
