from corp.models import CorporateMemory, Task
from ai_core.llm_gateway import OllamaClient
from pgvector.django import L2Distance
import os

# 전역 임베딩 모델 설정 (Ollama에 해당 모델이 pull 되어 있어야 함)
EMBEDDING_MODEL = "nomic-embed-text" 

def get_embedding(text: str):
    """Ollama를 통해 텍스트를 벡터로 변환합니다."""
    client = OllamaClient()
    try:
        response = client.embeddings(model=EMBEDDING_MODEL, prompt=text)
        return response.get('embedding')
    except Exception as e:
        print(f"❌ Embedding Error: {e}")
        return []

def add_knowledge(owner, subject: str, content: str, source_task_id: int = None):
    """지식을 벡터화하여 위키에 저장합니다."""
    vector = get_embedding(f"{subject}\n{content}")
    if not vector:
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

def search_wiki(query: str, top_k: int = 3):
    """질문과 유사한 위키 문서를 검색합니다."""
    query_vector = get_embedding(query)
    if not query_vector:
        return []

    # L2 Distance(유클리드 거리)로 유사도 검색 (거리가 가까울수록 유사함)
    results = CorporateMemory.objects.annotate(
        distance=L2Distance('embedding', query_vector)
    ).order_by('distance')[:top_k]
    
    return results