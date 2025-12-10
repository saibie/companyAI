from django.db import models
from django.db.models import JSONField
from pgvector.django import VectorField

class Agent(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    config = JSONField(default=dict)  # Stores ollama_model, temperature, system_prompt
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

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
    embedding = VectorField(dimensions=768)  # Compatible with nomic-embed-text
    type = models.CharField(
        max_length=20,
        choices=MemoryType.choices,
        default=MemoryType.OBSERVATION,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Memory for {self.agent.name} - {self.type}"