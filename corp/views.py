from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import Agent, Task, AgentMemory
from ai_core.llm_gateway import OllamaClient
import requests

class DashboardView(View):
    def get(self, request, *args, **kwargs):
        agents = Agent.objects.filter(manager__isnull=True).order_by('name')
        approval_tasks = Task.objects.filter(
            status=Task.TaskStatus.WAIT_APPROVAL, 
            assignee__manager__isnull=True
        ).order_by('-id')
        
        question_tasks = Task.objects.filter(
            status=Task.TaskStatus.WAIT_ANSWER,
            assignee__manager__isnull=True
        ).order_by('-id')
        
        ollama_client = OllamaClient()
        ollama_status = "Offline"
        ollama_models = []
        try:
            ollama_client.list_models()
            ollama_status = "Online"
            ollama_models = ollama_client.list_models().get('models', [])
        except requests.exceptions.RequestException:
            pass

        context = {
            'agents': agents,
            'approval_tasks': approval_tasks, # 변수명 변경 (tasks -> approval_tasks)
            'question_tasks': question_tasks, # [New]'ollama_status': ollama_status,
            'ollama_models': ollama_models,
            'agent_queue_status': 'Idle',
        }
        return render(request, 'corp/dashboard.html', context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'create_agent':
            name = request.POST.get('name')
            role = request.POST.get('role')
            manager_id = request.POST.get('manager')
            manager = Agent.objects.get(id=manager_id) if manager_id else None
            Agent.objects.create(name=name, role=role, manager=manager, can_hire=True, can_fire=True)
            
            if request.htmx:
                agents = Agent.objects.filter(manager__isnull=True).order_by('name')
                return render(request, 'corp/partials/agent_list.html', {'agents': agents})

        elif action == 'create_task':
            title = request.POST.get('title')
            description = request.POST.get('description')
            assignee_id = request.POST.get('assignee')
            assignee = Agent.objects.get(id=assignee_id)
            creator, _ = Agent.objects.get_or_create(name='CEO', role='CEO')
            Task.objects.create(title=title, description=description, assignee=assignee, creator=creator, status=Task.TaskStatus.THINKING)
            
            if request.htmx:
                tasks = Task.objects.filter(status=Task.TaskStatus.WAIT_APPROVAL).order_by('-id')
                return render(request, 'corp/partials/task_list.html', {'tasks': tasks})

        elif action == 'approve_task':
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id)
            task.status = Task.TaskStatus.APPROVED
            task.save()
            
            if request.htmx:
                tasks = Task.objects.filter(status=Task.TaskStatus.WAIT_APPROVAL).order_by('-id')
                return render(request, 'corp/partials/task_list.html', {'tasks': tasks})

        elif action == 'reply_question':
            task_id = request.POST.get('task_id')
            answer = request.POST.get('answer') # 답변 내용
            
            task = get_object_or_404(Task, id=task_id)
            
            # 답변을 로그에 저장 (에이전트가 히스토리로 볼 수 있게)
            # result=질문, feedback=답변 형태로 저장하면 에이전트 프롬프트에 자연스럽게 들어감
            from .models import TaskLog
            TaskLog.objects.create(
                task=task,
                result=task.result,  # 질문 내용
                feedback=f"[Manager's Answer] {answer}", # 답변 내용
                status='ANSWERED'
            )

            # 상태를 다시 THINKING으로 변경하여 에이전트 깨우기
            task.status = Task.TaskStatus.THINKING
            task.feedback = answer # 최신 피드백 필드에도 업데이트
            task.save()
            
            if request.htmx:
                 # 질문 목록 갱신
                question_tasks = Task.objects.filter(status=Task.TaskStatus.WAIT_ANSWER, assignee__manager__isnull=True).order_by('-id')
                return render(request, 'corp/partials/question_list.html', {'question_tasks': question_tasks})
        
        elif action == 'reject_task':
            task_id = request.POST.get('task_id')
            feedback = request.POST.get('feedback')
            task = get_object_or_404(Task, id=task_id)
            
            # [추가] 반려 전, 현재 제출물과 피드백을 로그로 저장
            from .models import TaskLog  # 상단 import 권장
            TaskLog.objects.create(
                task=task,
                result=task.result,   # 에이전트가 제출했던 결과
                feedback=feedback,    # 지금 내리는 피드백
                status='REJECTED'
            )

            # 기존 로직 (상태 초기화 및 피드백 덮어쓰기)
            task.status = Task.TaskStatus.THINKING
            task.feedback = feedback
            task.save()
            
            if request.htmx:
                tasks = Task.objects.filter(status=Task.TaskStatus.WAIT_APPROVAL).order_by('-id')
                return render(request, 'corp/partials/task_list.html', {'tasks': tasks})
        
        elif action == 'ollama_pull_model':
            model_name = request.POST.get('model_name')
            ollama_client = OllamaClient()
            pull_status_messages = []
            try:
                for chunk in ollama_client.pull_model(model_name):
                    status = chunk.get('status')
                    if status: # Only add if status is not empty
                        pull_status_messages.append(status)
                        print(f"Ollama Pull Status: {status}")
                pull_status_messages.append(f"Successfully pulled {model_name}.")
            except requests.exceptions.RequestException as e:
                pull_status_messages.append(f"Error pulling model {model_name}: {e}")
                print(f"Error pulling model {model_name}: {e}")

            if request.htmx:
                # Render a partial template with the pull status
                return render(request, 'corp/partials/ollama_pull_status.html', {'pull_status_messages': pull_status_messages})

        return redirect('corp:dashboard')


class AgentDetailView(View):
    def get(self, request, pk, *args, **kwargs):
        agent = get_object_or_404(Agent, pk=pk)
        created_tasks = Task.objects.filter(creator=agent).order_by('-id')
        assigned_tasks = Task.objects.filter(assignee=agent).order_by('-id')
        memories = AgentMemory.objects.filter(agent=agent).order_by('-created_at')

        context = {
            'agent': agent,
            'created_tasks': created_tasks,
            'assigned_tasks': assigned_tasks,
            'memories': memories,
        }
        return render(request, 'corp/agent_detail.html', context)