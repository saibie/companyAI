import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models import JSONField
from django.db import transaction
from pgvector.django import VectorField

class Agent(models.Model):
    # [변경] ID를 UUIDv4로 변경 (모든 모델 공통 적용)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # [추가] 소유권 명시: 이 에이전트가 어떤 '사용자(CEO)'의 것인지 구분
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agents')
    
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    
    # manager가 null이면, 이 에이전트는 owner(사용자)의 직속 부하입니다.
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    depth = models.IntegerField(default=0)
    
    can_hire = models.BooleanField(default=False)
    can_fire = models.BooleanField(default=False)
    
    ollama_model_name = models.CharField(max_length=255, null=True, blank=True)
    context_window_size = models.IntegerField(null=True, blank=True)
    config = JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    allowed_tools = JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        # 저장 전 Depth 자동 계산
        if self.manager:
            self.depth = self.manager.depth + 1
            # 하위 에이전트는 상위 에이전트와 같은 owner를 가짐 (무결성 유지)
            self.owner = self.manager.owner
        else:
            self.depth = 0
        super().save(*args, **kwargs)

    def create_sub_agent(self, name, role, ollama_model_name=None, context_window_size=None, can_hire=False, can_fire=False):
        return Agent.objects.create(
            owner=self.owner,  # [중요] 생성자의 소유주를 그대로 상속
            name=name,
            role=role,
            manager=self,
            ollama_model_name=ollama_model_name,
            context_window_size=context_window_size,
            can_hire=can_hire,
            can_fire=can_fire,
            config={}
        )
    
    def is_descendant_of(self, potential_ancestor):
        current = self.manager
        while current:
            if current == potential_ancestor:
                return True
            current = current.manager
        return False

    def delete(self, *args, **kwargs):
        """
        [Fail-safe Firing Logic]
        에이전트 삭제 시 하위 에이전트를 조부모(Grandparent)에게 자동 승계합니다.
        """
        with transaction.atomic():
            subordinates = list(self.subordinates.all())
            grandparent = self.manager 

            if subordinates:
                # 1. 소속 변경 (입양) -> 조부모 혹은 사용자의 직속(None)으로 변경
                self.subordinates.all().update(manager=grandparent)

                # 2. 알림 Task 생성
                # grandparent가 없으면 사용자(Human CEO)가 관리하게 됨
                grandparent_name = grandparent.name if grandparent else "Human CEO (User)"
                
                for sub in subordinates:
                    Task.objects.create(
                        # Task 생성 시 creator 설정 주의: 
                        # grandparent가 있으면 그가 creator, 없으면 시스템 알림이므로 creator=None
                        creator=grandparent if grandparent else None,
                        assignee=sub,
                        title=f"[긴급] 조직 개편에 따른 업무 보고",
                        description=(
                            f"직속 상사 '{self.name}'(이)가 해고/삭제되었습니다. "
                            f"현재 귀하는 '{grandparent_name}' 직속으로 변경되었습니다. "
                            f"현재 진행 중인 업무 현황을 파악하여 새로운 상급자에게 즉시 보고하십시오."
                        ),
                        status=Task.TaskStatus.THINKING,
                    )
            
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    
    # [변경] creator가 null이면 '사용자(Human)'가 직접 지시한 태스크입니다.
    creator = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='created_tasks', null=True, blank=True)
    assignee = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='assigned_tasks')
    
    parent_task = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    result = models.TextField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TaskLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='logs')
    result = models.TextField()
    feedback = models.TextField()
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.task.title}"


class AgentMemory(models.Model):
    class MemoryType(models.TextChoices):
        OBSERVATION = 'observation', 'Observation'
        REFLECTION = 'reflection', 'Reflection'
        SOP = 'sop', 'SOP'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        return f"Memory for {self.agent.name}"


class CorporateMemory(models.Model):
    """전사적 지식 저장소"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memories')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    embedding = VectorField(dimensions=768)
    source_task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Wiki] {self.subject}"


class Channel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ChannelMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Agent, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.channel.name}] {self.sender.name}: {self.content[:20]}"


class Announcement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Broadcast] {self.content[:30]}..."