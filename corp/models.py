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
    depth = models.IntegerField(default=0) # CEO=0, 직속=1, 그 아래=2 ...
    can_hire = models.BooleanField(default=False) # 고용 권한
    can_fire = models.BooleanField(default=False) # 해고 권한
    
    ollama_model_name = models.CharField(max_length=255, null=True, blank=True)
    context_window_size = models.IntegerField(null=True, blank=True)
    config = JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 저장 전 Depth 자동 계산
        if self.manager:
            self.depth = self.manager.depth + 1
        else:
            self.depth = 0
        super().save(*args, **kwargs)

    def create_sub_agent(self, name, role, ollama_model_name=None, context_window_size=None, can_hire=False, can_fire=False):
        return Agent.objects.create(
            name=name,
            role=role,
            manager=self,
            ollama_model_name=ollama_model_name,
            context_window_size=context_window_size,
            can_hire=can_hire, # 권한 부여
            can_fire=can_fire,
            config={}
        )
    
    def is_descendant_of(self, potential_ancestor):
        """
        자신이 potential_ancestor의 하위 조직(손자, 증손자 포함)에 속하는지 확인합니다.
        (직권 해고 시 권한 확인용)
        """
        current = self.manager
        while current:
            if current == potential_ancestor:
                return True
            current = current.manager
        return False

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
                        # priority='URGENT' # (Task 모델에 priority 필드 추가 필요, 없으면 생략)
                    )
            
            # 3. 실제 삭제
            super().delete(*args, **kwargs)


class Task(models.Model):
    class TaskStatus(models.TextChoices):
        TODO = 'TODO', 'To Do'
        THINKING = 'THINKING', 'Thinking'
        WAIT_SUBTASK = 'WAIT_SUBTASK', 'Waiting for Subtasks'
        WAIT_APPROVAL = 'WAIT_APPROVAL', 'Wait Approval'
        WAIT_ANSWER = 'WAIT_ANSWER', 'Waiting for Answer'
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

class TaskLog(models.Model):
    """
    Task의 수행 이력을 저장하는 모델 (반려 기록용)
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    # 당시의 결과물
    result = models.TextField()
    # 당시의 피드백 (반려 사유)
    feedback = models.TextField()
    # 당시의 상태 (REJECTED, APPROVED 등)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.task.title} - {self.created_at}"

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

class CorporateMemory(models.Model):
    """
    전사적 지식 저장소 (Wiki / SOP / Best Practices)
    특정 에이전트에 종속되지 않으며, 모든 에이전트가 검색 가능함.
    """
    id = models.AutoField(primary_key=True)
    subject = models.CharField(max_length=255) # 지식의 주제 또는 제목
    content = models.TextField() # 지식의 본문 (요약된 내용)
    embedding = VectorField(dimensions=768) # nomic-embed-text 등과 호환
    
    # 출처 추적용 (어떤 태스크에서 파생된 지식인지)
    source_task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Wiki] {self.subject}"

class Channel(models.Model):
    name = models.CharField(max_length=50, unique=True) # 예: #general, #dev_team
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ChannelMessage(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Agent, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.channel.name}] {self.sender.name}: {self.content[:20]}"

class Announcement(models.Model):
    """CEO의 전사 공지사항 (Broadcast)"""
    content = models.TextField()
    is_active = models.BooleanField(default=True) # 활성화된 공지만 프롬프트에 주입
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Broadcast] {self.content[:30]}..."