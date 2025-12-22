from corp.models import Agent, Task

def create_sub_agent(manager_name: str, name: str, role: str) -> str:
    """
    Creates a new subordinate agent (Hiring).
    Args:
        manager_name: The name of the agent calling this tool (YOUR name).
        name: The name of the new agent to hire.
        role: The role/job title of the new agent.
    """
    print(f"👥 [Service] Creating agent: {name} under {manager_name}")
    try:
        # 1. 매니저(나) 찾기
        manager = Agent.objects.filter(name=manager_name).first()
        if not manager:
            return f"Error: Manager agent '{manager_name}' not found. Cannot create sub-agent."

        # 2. 하위 에이전트 생성 (Django ORM 사용)
        # create_sub_agent 메서드는 models.py에 정의되어 있다고 가정
        new_agent = manager.create_sub_agent(name=name, role=role)
        return f"Success: Hired {new_agent.name} ({new_agent.role}) as a subordinate of {manager.name}."
    except Exception as e:
        return f"Error creating agent: {str(e)}"

def fire_sub_agent(manager_name: str, target_name: str, reason: str) -> str:
    """
    Fires a subordinate agent.
    Args:
        manager_name: The name of the agent calling this tool (YOUR name).
        target_name: The name of the subordinate to fire.
        reason: The reason for firing.
    """
    # [수정] 입력값 공백 제거로 매칭 정확도 향상
    manager_name = manager_name.strip()
    target_name = target_name.strip()
    
    print(f"🔥 [Service] Attempting to fire: '{target_name}' by '{manager_name}'")
    
    try:
        # 1. 권한 확인
        manager = Agent.objects.filter(name=manager_name).first()
        if not manager:
            msg = f"Error: Manager '{manager_name}' not found."
            print(f"❌ [Service Error] {msg}") # [추가] 에러 로그 출력
            return msg

        # 2. 대상 찾기 (자신의 직속 부하만)
        target = Agent.objects.filter(name=target_name, manager=manager).first()
        
        if not target:
            # 디버깅을 위해 현재 부하 직원 명단을 로그에 남김
            current_subs = list(manager.subordinates.values_list('name', flat=True))
            msg = f"Error: Agent '{target_name}' is not found under manager '{manager_name}'. (Current subs: {current_subs})"
            print(f"❌ [Service Error] {msg}") # [추가] 에러 로그 출력
            return msg

        # 3. 해고 실행
        target.delete()
        success_msg = f"Success: Fired '{target_name}'. Reason: {reason}"
        print(f"✅ [Service Success] {success_msg}") # [추가] 성공 로그 출력
        return success_msg
        
    except Exception as e:
        error_msg = f"Error firing agent: {str(e)}"
        print(f"❌ [Service Exception] {error_msg}") # [추가] 예외 로그 출력
        return error_msg

def assign_task(manager_name: str, assignee_name: str, title: str, description: str, current_task_id: int) -> str:
    """
    Assigns a task to a subordinate.
    Args:
        manager_name: The name of the agent calling this tool.
        assignee_name: The name of the subordinate.
        title: Task title.
        description: Detailed instructions.
        current_task_id: The ID of the task YOU are currently working on.
    """
    print(f"📨 [Service] Assigning task '{title}' to {assignee_name} (Parent Task: {current_task_id})")
    try:
        manager = Agent.objects.filter(name=manager_name).first()
        assignee = Agent.objects.filter(name=assignee_name).first()
        
        # 현재 수행 중인(부모) 태스크 조회
        parent_task = Task.objects.filter(id=current_task_id).first()

        if not manager or not assignee or not parent_task:
            return "Error: Manager, Assignee, or Current Task not found."

        # 1. 하위 태스크 생성 (parent_task 연결)
        sub_task = Task.objects.create(
            title=title,
            description=description,
            creator=manager,
            assignee=assignee,
            parent_task=parent_task,  # [핵심] 부모 태스크 연결
            status=Task.TaskStatus.THINKING
        )
        
        # 2. 부모 태스크 상태 변경 (대기 상태로 전환)
        parent_task.status = Task.TaskStatus.WAIT_SUBTASK
        parent_task.save()

        return f"Success: Task assigned to {assignee_name}. I am now waiting for their report."
    except Exception as e:
        return f"Error assigning task: {str(e)}"
