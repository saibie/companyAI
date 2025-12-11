from django.db import models
from django.db.models import JSONField
from django.db import transaction
from pgvector.django import VectorField

class Agent(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    
    # 계층 구조 (Manager 삭제 시 DB에선 NULL로 두되, 로직으로 처리)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    ollama_model_name = models.CharField(max_length=255, null=True, blank=True)
    context_window_size = models.IntegerField(null=True, blank=True)
    config = JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def create_sub_agent(self, name, role, ollama_model_name=None, context_window_size=None):
        return Agent.objects.create(
            name=name,
            role=role,
            manager=self,
            ollama_model_name=ollama_model_name,
            context_window_size=context_window_size,
            config={}
        )

    def delete(self, *args, **kwargs):
        """
        [Fail-safe Firing Logic]
        에이전트 삭제 시 하위 에이전트를 조부모(Grandparent)에게 자동 승계하고,
        한국어로 된 긴급 보고 태스크를 생성합니다.
        """
        with transaction.atomic():
            subordinates = list(self.subordinates.all()) # 미리 리스트로 평가
            grandparent = self.manager # 삭제되는 나의 상사

            if subordinates:
                # 1. 소속 변경 (입양)
                self.subordinates.all().update(manager=grandparent)

                # 2. 알림 Task 생성 (한국어)
                grandparent_name = grandparent.name if grandparent else "CEO (최상위)"
                
                for sub in subordinates:
                    Task.objects.create(
                        title=f"[긴급] 조직 개편에 따른 업무 보고",
                        description=(
                            f"직속 상사 '{self.name}'(이)가 해고/삭제되었습니다. "
                            f"현재 귀하는 '{grandparent_name}' 직속으로 변경되었습니다. "
                            f"현재 진행 중인 업무 현황을 파악하여 새로운 상급자에게 즉시 보고하십시오."
                        ),
                        assignee=sub,
                        creator=grandparent if grandparent else sub, # 조부모 혹은 본인 발의
                        status=Task.TaskStatus.THINKING, # 즉시 처리하도록 THINKING 상태로
                        priority='URGENT' # (Task 모델에 priority 필드 추가 필요, 없으면 생략)
                    )
            
            # 3. 실제 삭제
            super().delete(*args, **kwargs)


class Task(models.Model):
    class TaskStatus(models.TextChoices):
        TODO = 'TODO', 'To Do'
        THINKING = 'THINKING', 'Thinking'
        WAIT_APPROVAL = 'WAIT_APPROVAL', 'Wait Approval'
        APPROVED = 'APPROVED', 'Approved'
        DONE = 'DONE', 'Done'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    creator = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='created_tasks')
    assignee = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='assigned_tasks')
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    result = models.TextField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class AgentMemory(models.Model):
    class MemoryType(models.TextChoices):
        OBSERVATION = 'observation', 'Observation'
        REFLECTION = 'reflection', 'Reflection'
        SOP = 'sop', 'SOP'

    id = models.AutoField(primary_key=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    content = models.TextField()
    embedding = VectorField(dimensions=768)
    type = models.CharField(
        max_length=20,
        choices=MemoryType.choices,
        default=MemoryType.OBSERVATION,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Memory for {self.agent.name} - {self.type}"