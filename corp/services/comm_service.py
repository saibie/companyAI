from corp.models import Channel, ChannelMessage, Agent, Announcement
from django.db.models import Q

def post_message(agent_name: str, channel_name: str, content: str) -> str:
    """채널에 메시지를 게시합니다."""
    try:
        agent = Agent.objects.get(name=agent_name)
        # 채널이 없으면 자동으로 생성 (편의성)
        channel, created = Channel.objects.get_or_create(name=channel_name)
        
        ChannelMessage.objects.create(
            channel=channel,
            sender=agent,
            content=content
        )
        return f"✅ Posted to {channel_name}: {content}"
    except Agent.DoesNotExist:
        return f"❌ Error: Agent '{agent_name}' not found."
    except Exception as e:
        return f"❌ Error posting message: {str(e)}"

def read_channel(channel_name: str, limit: int = 5) -> str:
    """채널의 최근 메시지를 조회합니다."""
    try:
        channel = Channel.objects.get(name=channel_name)
        messages = channel.messages.select_related('sender').order_by('-created_at')[:limit]
        
        # 최신순으로 가져와서 시간순(과거->현재)으로 뒤집음
        messages = reversed(messages)
        
        result = f"💬 [Channel: {channel_name}] Recent messages:\n"
        for msg in messages:
            result += f"- {msg.sender.name} ({msg.sender.role}): {msg.content}\n"
            
        return result
    except Channel.DoesNotExist:
        return f"ℹ️ Channel '{channel_name}' does not exist yet."

def get_active_announcement() -> str:
    """활성화된 최신 공지사항을 가져옵니다 (시스템 프롬프트 주입용)."""
    announcement = Announcement.objects.filter(is_active=True).order_by('-created_at').first()
    if announcement:
        return f"\n📢 [CEO BROADCAST / ALL-HANDS ALERT]\n{announcement.content}\n(Prioritize this instruction above all else.)\n"
    return ""