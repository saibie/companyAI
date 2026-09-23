---
type: concept
title: Vector Memory & pgvector Integration
description: AgentMemory, CorporateMemory, vector dimensions, and semantic retrieval patterns.
updated_at: 2026-09-23
tags:
  - pgvector
  - embeddings
  - memory
  - postgresql
related_files:
  - corp/models.py
  - corp/memory_manager.py
  - corp/services/kms_service.py
---

# 🧠 Vector Memory & pgvector Integration

## 1. Dual Memory Architecture
companyAI separates memory into two distinct scopes:

### A. Individual Memory (`AgentMemory`)
- **Scope**: Specific to an individual agent.
- **Model**: [AgentMemory](file:///home/saibie1677/projects/companyAI/corp/models.py#L153)
- **Memory Types**:
  - `OBSERVATION`: Raw observations or task completion notes.
  - `REFLECTION`: Meta-analysis of past mistakes or performance critiques.
  - `SOP`: Standard Operating Procedures assigned to this role.
- **Access**: Only queried by the owner agent during reasoning loops.

### B. Enterprise Knowledge Store (`CorporateMemory`)
- **Scope**: Company-wide organizational knowledge (Corporate Wiki).
- **Model**: [CorporateMemory](file:///home/saibie1677/projects/companyAI/corp/models.py#L174)
- **Access**: Searchable by all authorized agents via `search_wiki_tool` and KMS service.

---

## 2. Vector Specifications & pgvector Extension
- **Extension**: `pgvector` in PostgreSQL 16 (`pgvector/pgvector:pg16` Docker image).
- **Django Integration**: `pgvector.django.VectorField(dimensions=768)`.
- **Target Embedding Model**: `nomic-embed-text` (768 dimensions), served via local Ollama.
- **Distance Metric**: Cosine Distance (`<=>` operator in pgvector).

```python
# Semantic search query pattern:
from pgvector.django import CosineDistance

similar_memories = AgentMemory.objects.filter(agent=agent).annotate(
    distance=CosineDistance('embedding', query_embedding)
).order_by('distance')[:top_k]
```

---

## 3. Database Migration Requirement
Any migration introducing or modifying vector fields must explicitly include the extension operation:
```python
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    operations = [
        VectorExtension(),
        # ... model operations
    ]
```
