from corp.services import safeguard_service

MAX_AGENT_DEPTH = 4

def create_sub_agent(manager_name: str, name: str, role: str, grant_hire: bool = False, grant_fire: bool = False) -> str:
    """
    Creates a new subordinate agent with permission checks.
    Args:
        manager_name: Calling agent's name.
        name: New agent's name.
        role: New agent's role.
        grant_hire: Whether to give the new agent hiring permission.
        grant_fire: Whether to give the new agent firing permission.
    """
    print(f"👥 [Service] Hiring Request: {name} (under {manager_name})")
    
    try:
        manager = Agent.objects.filter(name=manager_name).first()
        if not manager:
            return f"Error: Manager '{manager_name}' not found."

        # 1. [Check] 고용 권한이 있는가?
        if not manager.can_hire and manager.manager is not None: 
            return f"⛔ Permission Denied: You ({manager_name}) do not have 'HIRING' permission."

        # 2. [Safeguard Check] 무한 고용 제약조건 검사
        allowed, reason = safeguard_service.check_hiring_allowed(manager, manager.owner)
        if not allowed:
            return f"⛔ Safeguard Blocked Hiring: {reason}"

        # 3. 하위 에이전트 생성 (권한 위임 포함)
        new_agent = manager.create_sub_agent(
            name=name, 
            role=role,
            can_hire=grant_hire,
            can_fire=grant_fire
        )
        
        permission_info = []
        if grant_hire: permission_info.append("HIRING")
        if grant_fire: permission_info.append("FIRING")
        perm_str = ", ".join(permission_info) if permission_info else "No special permissions"

        return f"✅ Success: Hired {new_agent.name}. Permissions granted: [{perm_str}]."

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
        manager = Agent.objects.filter(name=manager_name).first()
        if not manager:
            return f"Error: Manager '{manager_name}' not found."
            
        # 1. [Check] 해고 권한이 있는가?
        if not manager.can_fire and manager.manager is not None:
             return f"⛔ Permission Denied: You ({manager_name}) do not have 'FIRING' permission."

        # 2. 대상 찾기 (자신의 직속 부하만)
        target = Agent.objects.filter(name=target_name).first()
        
        if not target:
            # 디버깅을 위해 현재 부하 직원 명단을 로그에 남김
            current_subs = list(manager.subordinates.values_list('name', flat=True))
            msg = f"Error: Agent '{target_name}' is not found under manager '{manager_name}'. (Current subs: {current_subs})"
            print(f"❌ [Service Error] {msg}") # [추가] 에러 로그 출력
            return msg

        # 3. [관계 체크] 직속이거나, 혹은 내 하위 조직(손자/증손자)인지 확인
        if target.manager != manager and not target.is_descendant_of(manager):
            return f"⛔ Access Denied: Agent '{target_name}' is not in your command chain."
        
        # 4. 해고 실행
        target.delete()
        success_msg = f"Success: Fired '{target_name}'. Reason: {reason}"
        print(f"✅ [Service Success] {success_msg}") # [추가] 성공 로그 출력
        return success_msg
        
    except Exception as e:
        error_msg = f"Error firing agent: {str(e)}"
        print(f"❌ [Service Exception] {error_msg}") # [추가] 예외 로그 출력
        return error_msg

def assign_task(manager_name: str, assignee_name: str, title: str, description: str, current_task_id: str) -> str:
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

def ask_manager(agent_name: str, current_task_id: str, question: str) -> str:
    """에이전트가 매니저(사용자)에게 질문을 던지고 결재(답변)를 기다리게 합니다."""
    try:
        task = Task.objects.get(id=current_task_id)
        
        # 질문 내용을 결과물(Result) 필드에 임시 저장하고 '질문' 태그를 붙임
        task.result = f"[❓ QUESTION to Manager]\n{question}"
        
        # 상태를 결재 대기(WAIT_APPROVAL)로 변경하여 대시보드에 노출시킴
        task.status = Task.TaskStatus.WAIT_ANSWER
        task.save()
        
        return "Success: Question sent to manager. Waiting for feedback."
    except Task.DoesNotExist:
        return "Error: Task not found."
    except Exception as e:
        return f"Error: {str(e)}"

def reply_to_subordinate(manager_name: str, subordinate_task_id: str, answer: str) -> str:
    """
    상급자가 부하의 질문(또는 태스크)에 대해 답변/피드백을 주고, 부하를 다시 일하게 만듭니다.
    """
    try:
        # 1. 권한 및 관계 확인
        manager = Agent.objects.get(name=manager_name)
        sub_task = Task.objects.get(id=subordinate_task_id)
        subordinate = sub_task.assignee
        
        # 매니저의 직속 부하인지, 혹은 하위 조직인지 체크
        if subordinate.manager != manager and not subordinate.is_descendant_of(manager):
            return "Error: You can only reply to your own subordinates."

        # 2. 답변 로깅 (TaskLog)
        TaskLog.objects.create(
            task=sub_task,
            result=sub_task.result, # 질문 내용
            feedback=f"[Manager's Answer] {answer}",
            status='ANSWERED'
        )

        # 3. 부하 깨우기
        sub_task.feedback = f"[Manager Answered]: {answer}"
        sub_task.status = Task.TaskStatus.THINKING
        sub_task.save()
        
        return f"Success: Sent answer to {subordinate.name}. They are back to work."

    except Exception as e:
        return f"Error: {str(e)}"