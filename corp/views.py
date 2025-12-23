from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpRequest

# [중요] 사람용 서비스 임포트
from corp.services import human_service 
from .models import Agent, Task, AgentMemory, CorporateMemory
from ai_core.llm_gateway import OllamaClient
import requests

# ==============================================================================
# 1. 메인 뷰 (GET Only) - 화면 렌더링 담당
# ==============================================================================
class DashboardView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        agents = Agent.objects.filter(owner=request.user, manager__isnull=True).order_by('name')
        
        visible_filter = Q(assignee__owner=request.user) & Q(creator__isnull=True)
        
        todo_tasks = Task.objects.filter(
            visible_filter,
            status=Task.TaskStatus.TODO, 
        ).order_by('-created_at' if hasattr(Task, 'created_at') else '-id')
        
        approval_tasks = Task.objects.filter(
            visible_filter,
            status=Task.TaskStatus.WAIT_APPROVAL, 
        ).order_by('-created_at' if hasattr(Task, 'created_at') else '-id')
        
        question_tasks = Task.objects.filter(
            visible_filter,
            status=Task.TaskStatus.WAIT_ANSWER,
        ).order_by('-created_at' if hasattr(Task, 'created_at') else '-id')
        
        roadmap_tasks = Task.objects.filter(
            assignee__owner=request.user,
            status=Task.TaskStatus.APPROVED,
            result__startswith="REQUEST_DEV:"
        ).order_by('created_at')
        
        ollama_client = OllamaClient()
        ollama_status = "Offline"
        ollama_models = []
        try:
            ollama_client.list_models()
            ollama_status = "Online"
            ollama_models = ollama_client.list_models().get('models', [])
        except requests.exceptions.RequestException:
            pass

        all_my_agents = Agent.objects.filter(owner=request.user)
        
        context = {
            'agents': agents,
            'all_my_agents': all_my_agents,
            'todo_tasks': todo_tasks,
            'approval_tasks': approval_tasks,
            'question_tasks': question_tasks,
            'roadmap_tasks': roadmap_tasks,
            'ollama_models': ollama_models,
            'ollama_status': ollama_status,
            'agent_queue_status': 'Idle',
        }
        return render(request, 'corp/dashboard.html', context)


class MonitorView(LoginRequiredMixin, View):
    """모니터링 화면 조회 (GET Only)"""
    def get(self, request: HttpRequest, *args, **kwargs):
        all_tasks = Task.objects.filter(
            assignee__owner=request.user
        ).select_related('creator', 'assignee').order_by('status', '-created_at')

        context = {
            'tasks': all_tasks,
        }
        return render(request, 'corp/monitor.html', context)


class AgentDetailView(LoginRequiredMixin, View):
    """에이전트 상세 조회 (GET Only + Fire Action via standard POST if needed)"""
    def get(self, request, pk, *args, **kwargs):
        agent = get_object_or_404(Agent, pk=pk, owner=request.user)
        created_tasks = Task.objects.filter(creator=agent)
        assigned_tasks = Task.objects.filter(assignee=agent)
        memories = AgentMemory.objects.filter(agent=agent).order_by('-created_at')

        context = {
            'agent': agent,
            'created_tasks': created_tasks,
            'assigned_tasks': assigned_tasks,
            'memories': memories,
        }
        return render(request, 'corp/agent_detail.html', context)
    
    def post(self, request, pk, *args, **kwargs):
        # 상세 페이지에서의 해고는 대시보드 리스트 갱신이 아닌 페이지 이동이 필요하므로 일반 POST 유지
        if request.POST.get('action') == 'fire_agent':
            human_service.fire_agent(request.user, pk)
            return redirect('corp:dashboard')
        return redirect('corp:agent_detail', pk=pk)


class WikiListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        memories = CorporateMemory.objects.filter(owner=request.user).order_by('-created_at')
        return render(request, 'corp/wiki_list.html', {'memories': memories})


class WikiDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        memory = get_object_or_404(CorporateMemory, pk=pk, owner=request.user)
        return render(request, 'corp/wiki_detail.html', {'memory': memory})


# ==============================================================================
# 2. HTMX 전용 핸들러 (HTMX Logic Handlers)
# ==============================================================================

@login_required
@require_POST
def htmx_create_agent(request):
    """에이전트 고용 -> Agent List 갱신"""
    human_service.hire_agent(
        user=request.user,
        name=request.POST.get('name'),
        role=request.POST.get('role'),
        manager_id=request.POST.get('manager')
    )
    # 갱신된 리스트 반환
    agents = Agent.objects.filter(owner=request.user, manager__isnull=True).order_by('name')
    return render(request, 'corp/partials/agent_list.html', {'agents': agents})


@login_required
@require_POST
def htmx_fire_agent(request):
    """에이전트 해고 -> Agent List 갱신"""
    human_service.fire_agent(request.user, request.POST.get('agent_id'))
    
    agents = Agent.objects.filter(owner=request.user, manager__isnull=True).order_by('name')
    return render(request, 'corp/partials/agent_list.html', {'agents': agents})


@login_required
@require_POST
def htmx_create_task(request):
    """태스크 생성 -> 승인 대기 목록(Task List) 갱신"""
    human_service.create_task(
        user=request.user,
        title=request.POST.get('title'),
        description=request.POST.get('description'),
        assignee_id=request.POST.get('assignee')
    )
    # 태스크 생성 직후 '승인 대기' 목록을 보여줌 (UX상 바로 확인 가능하도록)
    tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_APPROVAL)
    return render(request, 'corp/partials/task_list.html', {'approval_tasks': tasks})


@login_required
@require_POST
def htmx_approve_task(request):
    """태스크 승인 -> 승인 대기 목록 갱신"""
    human_service.approve_task(request.user, request.POST.get('task_id'))
    
    tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_APPROVAL)
    return render(request, 'corp/partials/task_list.html', {'approval_tasks': tasks})


@login_required
@require_POST
def htmx_reject_task(request):
    """태스크 반려 -> 승인 대기 목록 갱신"""
    human_service.reject_task(
        user=request.user, 
        task_id=request.POST.get('task_id'), 
        feedback=request.POST.get('feedback')
    )
    
    tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_APPROVAL)
    return render(request, 'corp/partials/task_list.html', {'approval_tasks': tasks})


@login_required
@require_POST
def htmx_reply_question(request):
    """질문 답변 -> 질문 목록 갱신"""
    human_service.reply_question(
        user=request.user,
        task_id=request.POST.get('task_id'),
        answer=request.POST.get('answer')
    )
    
    question_tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_ANSWER)
    return render(request, 'corp/partials/question_list.html', {'question_tasks': question_tasks})


@login_required
@require_POST
def htmx_deploy_feature(request):
    """기능 배포 완료 -> 로드맵 목록 갱신"""
    human_service.mark_feature_deployed(request.user, request.POST.get('task_id'))
    
    roadmap_tasks = Task.objects.filter(
        assignee__owner=request.user,
        status=Task.TaskStatus.APPROVED,
        result__startswith="REQUEST_DEV:"
    ).order_by('created_at')
    return render(request, 'corp/partials/roadmap_list.html', {'roadmap_tasks': roadmap_tasks})


@login_required
@require_POST
def htmx_monitor_update(request):
    """모니터링 강제 액션 -> 모니터링 테이블 갱신"""
    action = request.POST.get('action')
    task_id = request.POST.get('task_id')
    
    if action == 'force_delete':
        human_service.force_delete_task(request.user, task_id)
    else:
        # force_done, force_reject
        human_service.force_update_status(request.user, task_id, action)
        
    all_tasks = Task.objects.filter(
        assignee__owner=request.user
    ).select_related('creator', 'assignee').order_by('status', '-created_at')
    return render(request, 'corp/partials/monitor_list.html', {'tasks': all_tasks})


@login_required
@require_POST
def htmx_ollama_pull(request):
    """Ollama 모델 Pull -> 상태 메시지 갱신"""
    model_name = request.POST.get('model_name')
    client = OllamaClient()
    pull_status_messages = []
    
    try:
        # 동기적으로 Pull 진행 (타임아웃 주의, 필요 시 Celery로 빼야 함)
        for chunk in client.pull_model(model_name):
            status = chunk.get('status')
            if status:
                pull_status_messages.append(status)
        pull_status_messages.append(f"✅ Successfully pulled {model_name}.")
    except Exception as e:
        pull_status_messages.append(f"❌ Error: {e}")

    return render(request, 'corp/partials/ollama_pull_status.html', {'pull_status_messages': pull_status_messages})