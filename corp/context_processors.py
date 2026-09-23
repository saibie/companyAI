from corp.services import company_service

def active_company_context(request):
    """
    모든 템플릿에서 현재 로그인한 사용자의 활성 회사(active_company)와
    소유한 회사 목록(my_companies)을 즉시 참조할 수 있도록 전역 컨텍스트를 제공합니다.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}
    
    active_company = company_service.get_active_company(request)
    my_companies = company_service.get_user_companies(request.user)
    return {
        'active_company': active_company,
        'my_companies': my_companies,
    }
