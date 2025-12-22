from django.contrib import admin
from .models import Agent, Task, AgentMemory, TaskLog
from .models import CorporateMemory
from .models import Channel, ChannelMessage, Announcement

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'manager', 'is_active')
    list_filter = ('is_active', 'role')
    search_fields = ('name', 'role')
    raw_id_fields = ('manager',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'creator', 'assignee', 'parent_task')
    list_filter = ('status', 'creator', 'assignee')
    search_fields = ('title', 'description')
    raw_id_fields = ('creator', 'assignee', 'parent_task')

@admin.register(AgentMemory)
class AgentMemoryAdmin(admin.ModelAdmin):
    list_display = ('agent', 'type', 'created_at')
    list_filter = ('type', 'agent')
    search_fields = ('content',)
    raw_id_fields = ('agent',)

@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ('task', 'created_at')
    list_filter = ('task',)
    search_fields = ('task__title', 'details')
    raw_id_fields = ('task',)

@admin.register(CorporateMemory)
class CorporateMemoryAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'source_task')
    search_fields = ('subject', 'content')

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')

@admin.register(ChannelMessage)
class ChannelMessageAdmin(admin.ModelAdmin):
    list_display = ('channel', 'sender', 'content', 'created_at')
    list_filter = ('channel', 'sender')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('content', 'is_active', 'created_at')
    list_filter = ('is_active',)