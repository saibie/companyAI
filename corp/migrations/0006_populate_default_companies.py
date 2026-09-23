from django.db import migrations

def populate_default_companies(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Company = apps.get_model('corp', 'Company')
    Agent = apps.get_model('corp', 'Agent')
    CorporateMemory = apps.get_model('corp', 'CorporateMemory')
    Channel = apps.get_model('corp', 'Channel')
    Announcement = apps.get_model('corp', 'Announcement')

    for user in User.objects.all():
        # 사용자별 기본 회사 생성 (기존 데이터가 있거나 없는 경우 모두 지원)
        company, created = Company.objects.get_or_create(
            owner=user,
            defaults={
                'name': f"{user.username}의 AI 법인",
                'industry': "AI 테크 & 비즈니스",
                'description': f"{user.username} 님이 설립한 가상 자율 AI 조직입니다. 다양한 도메인의 AI 에이전트들이 협력하여 문제를 해결합니다.",
                'default_llm_model': "gemma4-ex-llmfan46:26b",
            }
        )
        
        # 기존 에이전트 연결
        Agent.objects.filter(owner=user, company__isnull=True).update(company=company)
        
        # 기존 전사 메모리 연결
        CorporateMemory.objects.filter(owner=user, company__isnull=True).update(company=company)
        
        # 기존 채널/공지사항 연결
        Channel.objects.filter(company__isnull=True).update(company=company)
        Announcement.objects.filter(company__isnull=True).update(company=company)

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('corp', '0005_alter_channel_name_company_agent_company_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_default_companies, reverse_func),
    ]
