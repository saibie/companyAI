from .models import Agent, AgentMemory
from django.db.models.functions import Coalesce
from django.db.models import F
from pgvector.django import L2Distance

class MemoryManager:
    def __init__(self, agent: Agent):
        self.agent = agent

    def add_memory(self, content: str, embedding: list[float], memory_type: str):
        AgentMemory.objects.create(
            agent=self.agent,
            content=content,
            embedding=embedding,
            type=memory_type
        )

    def search_memory(self, query_embedding: list[float], top_k: int = 5, memory_type: str = None):
        memories = AgentMemory.objects.filter(agent=self.agent)
        if memory_type:
            memories = memories.filter(type=memory_type)
        
        # Order by L2Distance (Euclidean distance) to find the most similar embeddings
        # A smaller distance means higher similarity.
        return memories.annotate(distance=L2Distance('embedding', query_embedding)).order_by('distance')[:top_k]

    def get_all_memories(self, memory_type: str = None):
        memories = AgentMemory.objects.filter(agent=self.agent)
        if memory_type:
            memories = memories.filter(type=memory_type)
        return memories.order_by('-created_at')
