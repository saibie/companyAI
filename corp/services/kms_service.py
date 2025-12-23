from corp.models import CorporateMemory, Task
from ai_core.llm_gateway import OllamaClient
from pgvector.django import L2Distance
import os
import requests
import time

# 전역 임베딩 모델 설정
EMBEDDING_MODEL = "nomic-embed-text" 

def get_embedding(text: str):
    """
    Ollama를 통해 텍스트를 벡터로 변환합니다.
    모델이 없으면 자동으로 Pull을 시도합니다.
    """
    client = OllamaClient()
    
    def _attempt_embedding():
        response = client.embeddings(model=EMBEDDING_MODEL, prompt=text)
        return response.get('embedding')

    try:
        # 1차 시도
        return _attempt_embedding()
        
    except Exception as e:
        print(f"⚠️ [KMS] Embedding failed initially: {e}")
        
        # 모델이 없어서 발생한 에러인지 확인 (404 Not Found 등)
        # Ollama는 모델이 없으면 404를 반환합니다.
        is_model_missing = "404" in str(e) or "not found" in str(e).lower()
        
        if is_model_missing:
            print(f"📥 [KMS] Embedding model '{EMBEDDING_MODEL}' is missing. Pulling now... (Please wait)")
            try:
                # 모델 다운로드 (스트리밍으로 진행 상황 표시)
                for progress in client.pull_model(EMBEDDING_MODEL):
                    status = progress.get('status', '')
                    # 진행 상황 로그가 너무 많으므로 중요 단계만 출력
                    if 'downloading' in status and '100%' in status: 
                        print(f"   ↳ {status}")
                
                print(f"✅ [KMS] Model '{EMBEDDING_MODEL}' pulled successfully. Retrying embedding...")
                
                # 잠시 대기 (Ollama가 모델 로드할 시간 확보)
                time.sleep(2)
                
                # 2차 시도 (재귀 호출 아님)
                return _attempt_embedding()
                
            except Exception as pull_error:
                print(f"❌ [KMS] Critical: Failed to pull model '{EMBEDDING_MODEL}': {pull_error}")
                return []
        else:
            # 모델 미싱 외의 다른 에러인 경우
            print(f"❌ [KMS] Embedding Error: {e}")
            return []

def add_knowledge(owner, subject: str, content: str, source_task_id: int = None):
    """지식을 벡터화하여 위키에 저장합니다."""
    
    # 임베딩 시도 (위에서 수정한 get_embedding 함수가 호출됨)
    vector = get_embedding(f"{subject}\n{content}")
    
    # 벡터 생성 실패 시 (모델 Pull도 실패한 경우) -> None 반환하여 호출 측에서 알 수 있게 함
    if not vector:
        print(f"❌ [KMS] Failed to create embedding for '{subject}'. Skipping Wiki save.")
        return None
        
    source_task = None
    if source_task_id:
        source_task = Task.objects.filter(id=source_task_id).first()

    memory = CorporateMemory.objects.create(
        owner=owner,
        subject=subject,
        content=content,
        embedding=vector,
        source_task=source_task
    )
    print(f"📚 [KMS] New knowledge added: {subject}")
    return memory

# search_wiki는 기존 로직 유지 (get_embedding이 강화되었으므로 자동 적용됨)
def search_wiki(query: str, top_k: int = 3):
    """질문과 유사한 위키 문서를 검색합니다."""
    query_vector = get_embedding(query)
    if not query_vector:
        return []

    results = CorporateMemory.objects.annotate(
        distance=L2Distance('embedding', query_vector)
    ).order_by('distance')[:top_k]
    
    return results