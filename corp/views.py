from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest
from .models import Agent, Task, AgentMemory, TaskLog, CorporateMemory
from ai_core.llm_gateway import OllamaClient
import requests

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
            'ollama_models': ollama_models,
            'ollama_status': ollama_status,
            'agent_queue_status': 'Idle',
        }
        return render(request, 'corp/dashboard.html', context)

    def post(self, request: HttpRequest, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'create_agent':
            name = request.POST.get('name')
            role = request.POST.get('role')
            manager_id = request.POST.get('manager')
            
            manager = None
            if manager_id:
                manager = get_object_or_404(Agent, id=manager_id, owner=request.user) # 보안: 내 에이전트만 매니저로 지정 가능

            # [수정] owner=request.user 추가 (에러 해결 핵심)
            Agent.objects.create(
                owner=request.user, 
                name=name, 
                role=role, 
                manager=manager, 
                can_hire=True, 
                can_fire=True
            )
            
            if request.htmx:
                # 갱신된 리스트 반환
                agents = Agent.objects.filter(owner=request.user, manager__isnull=True).order_by('name')
                return render(request, 'corp/partials/agent_list.html', {'agents': agents})

        elif action == 'create_task':
            title = request.POST.get('title')
            description = request.POST.get('description')
            assignee_id = request.POST.get('assignee')
            
            assignee = get_object_or_404(Agent, id=assignee_id, owner=request.user)
            
            # [수정] creator=None (사람이 만듦)
            Task.objects.create(
                title=title, 
                description=description, 
                assignee=assignee, 
                creator=None,  # 사람이 만든 태스크임을 명시
                status=Task.TaskStatus.THINKING
            )
            
            if request.htmx:
                # UUID 필터링 주의: 정렬 기준이 모호하므로 Task 모델에 created_at 추가가 시급함.
                # 임시로 그냥 가져옴
                tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_APPROVAL)
                return render(request, 'corp/partials/task_list.html', {'tasks': tasks})

        elif action == 'approve_task':
            task_id = request.POST.get('task_id')
            # [보안] 내 에이전트의 태스크만 승인 가능
            task = get_object_or_404(Task, id=task_id, assignee__owner=request.user)
            task.status = Task.TaskStatus.APPROVED
            task.save()
            
            if request.htmx:
                tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_APPROVAL)
                return render(request, 'corp/partials/task_list.html', {'tasks': tasks})

        elif action == 'reply_question':
            task_id = request.POST.get('task_id')
            answer = request.POST.get('answer')
            
            task = get_object_or_404(Task, id=task_id, assignee__owner=request.user)
            
            TaskLog.objects.create(
                task=task,
                result=task.result,
                feedback=f"[Manager's Answer] {answer}",
                status='ANSWERED'
            )

            task.status = Task.TaskStatus.THINKING
            task.feedback = answer
            task.save()
            
            if request.htmx:
                question_tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_ANSWER)
                return render(request, 'corp/partials/question_list.html', {'question_tasks': question_tasks})
        
        elif action == 'reject_task':
            task_id = request.POST.get('task_id')
            feedback = request.POST.get('feedback')
            task = get_object_or_404(Task, id=task_id, assignee__owner=request.user)
            
            TaskLog.objects.create(
                task=task,
                result=task.result,
                feedback=feedback,
                status='REJECTED'
            )

            task.status = Task.TaskStatus.THINKING
            task.feedback = feedback
            task.save()
            
            if request.htmx:
                tasks = Task.objects.filter(assignee__owner=request.user, status=Task.TaskStatus.WAIT_APPROVAL)
                return render(request, 'corp/partials/task_list.html', {'tasks': tasks})
        
        elif action == 'ollama_pull_model':
            model_name = request.POST.get('model_name')
            ollama_client = OllamaClient()
            pull_status_messages = []
            try:
                for chunk in ollama_client.pull_model(model_name):
                    status = chunk.get('status')
                    if status:
                        pull_status_messages.append(status)
                        print(f"Ollama Pull Status: {status}")
                pull_status_messages.append(f"Successfully pulled {model_name}.")
            except requests.exceptions.RequestException as e:
                pull_status_messages.append(f"Error pulling model {model_name}: {e}")
                print(f"Error pulling model {model_name}: {e}")

            if request.htmx:
                return render(request, 'corp/partials/ollama_pull_status.html', {'pull_status_messages': pull_status_messages})

        return redirect('corp:dashboard')


class AgentDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # [보안] 내 에이전트만 상세 조회 가능
        agent = get_object_or_404(Agent, pk=pk, owner=request.user)
        
        # creator가 None인 경우(사람이 만든 태스크)도 있을 수 있으므로 필터 조건 주의
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

class WikiListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # 내 소유의 지식만 최신순 조회
        memories = CorporateMemory.objects.filter(owner=request.user).order_by('-created_at')
        return render(request, 'corp/wiki_list.html', {'memories': memories})

class WikiDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        memory = get_object_or_404(CorporateMemory, pk=pk, owner=request.user)
        return render(request, 'corp/wiki_detail.html', {'memory': memory})