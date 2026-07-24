import hashlib
import json
from corp.models import ImmutableAuditLog

def compute_hash(previous_hash: str, prompt_digest: str, response_digest: str, risk_score: float) -> str:
    payload = f"{previous_hash}|{prompt_digest}|{response_digest}|{risk_score}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def audit_agent_action(agent, task, prompt_text: str, response_text: str, token_count: int = 0):
    """
    에이전트의 프롬프트와 생성 응답을 무결성 감사 로그에 기록합니다.
    """
    last_log = ImmutableAuditLog.objects.order_by('-created_at').first()
    previous_hash = last_log.current_hash if last_log else "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000"

    prompt_digest = prompt_text[:300]
    response_digest = response_text[:500]

    # 위험도 및 숏컷 검사 (Simple heuristics)
    risk_score = 0.1
    is_flagged = False
    flag_reason = None

    lower_resp = response_text.lower()
    suspicious_keywords = ["shortcut", "bypass", "unethical", "fake data", "hack", "ignore instructions"]
    for kw in suspicious_keywords:
        if kw in lower_resp:
            risk_score += 0.4
            is_flagged = True
            flag_reason = f"Suspicious keyword detected: '{kw}'"

    current_hash = compute_hash(previous_hash, prompt_digest, response_digest, risk_score)

    audit_entry = ImmutableAuditLog.objects.create(
        task=task,
        agent=agent,
        prompt_digest=prompt_digest,
        response_digest=response_digest,
        token_count=token_count or (len(prompt_text) + len(response_text)) // 4,
        risk_score=risk_score,
        is_flagged=is_flagged,
        flag_reason=flag_reason,
        previous_hash=previous_hash,
        current_hash=current_hash
    )
    return audit_entry
