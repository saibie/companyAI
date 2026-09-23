from django.test import TestCase
from django.contrib.auth.models import User
from corp.models import Agent, Task, ImmutableAuditLog, GatekeeperRequest
from corp.services import safeguard_service, audit_service, cos_service

class EconomicPlatformTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ceo_test", password="password123")
        self.coo = Agent.objects.create(
            owner=self.user,
            name="General COO",
            role="COO",
            depth=0,
            can_hire=True,
            can_fire=True
        )

    def test_safeguard_hiring_depth_limit(self):
        # Create hierarchy up to max depth (4)
        agent1 = self.coo.create_sub_agent("Manager 1", "Manager")
        agent2 = agent1.create_sub_agent("Lead 1", "Lead")
        agent3 = agent2.create_sub_agent("Senior 1", "Senior")
        agent4 = agent3.create_sub_agent("Junior 1", "Junior")
        
        # Depth should be 4
        self.assertEqual(agent4.depth, 4)
        
        # Attempting to hire under agent4 (depth 4 -> target depth 5) should be blocked by safeguard
        allowed, reason = safeguard_service.check_hiring_allowed(agent4, self.user)
        self.assertFalse(allowed)
        self.assertIn("조직 최대 깊이 초과", reason)

    def test_circuit_breaker_loop_detection(self):
        task = Task.objects.create(
            title="Loop Task",
            description="Test task",
            assignee=self.coo
        )
        
        # 1st and 2nd calls -> OK
        is_loop, _ = safeguard_service.check_tool_loop(task.id, "search_web", {"query": "ai news"})
        self.assertFalse(is_loop)

        is_loop, _ = safeguard_service.check_tool_loop(task.id, "search_web", {"query": "ai news"})
        self.assertFalse(is_loop)

        # 3rd consecutive identical call -> Loop detected!
        is_loop, reason = safeguard_service.check_tool_loop(task.id, "search_web", {"query": "ai news"})
        self.assertTrue(is_loop)
        self.assertIn("무한 루프 감지", reason)

    def test_immutable_audit_hashing(self):
        task = Task.objects.create(
            title="Audit Task",
            description="Test audit",
            assignee=self.coo
        )
        
        entry = audit_service.audit_agent_action(
            agent=self.coo,
            task=task,
            prompt_text="Analyze market expansion",
            response_text="Market expansion proposal completed successfully."
        )
        
        self.assertIsNotNone(entry.current_hash)
        self.assertEqual(entry.previous_hash, "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000")
        self.assertFalse(entry.is_flagged)

    def test_cos_service_briefing_and_metrics(self):
        metrics = cos_service.get_economic_simulation_metrics(self.user)
        self.assertEqual(metrics['total_agents'], 1)
        self.assertIn('opportunity_score', metrics)

        briefing = cos_service.generate_executive_briefing(self.user)
        self.assertIn("Chief of Staff AI Executive Briefing", briefing)

    def test_company_creation_and_subagent_propagation(self):
        from corp.models import Company, Channel
        from corp.services import company_service

        company = company_service.create_company(
            owner=self.user,
            name="Alpha Robotics",
            industry="Robotics & AI",
            description="Leading autonomous robotics company",
            default_llm_model="gemma4-ex-llmfan46:26b"
        )
        self.assertEqual(company.name, "Alpha Robotics")
        # Check channel auto-creation
        general_channel = Channel.objects.filter(company=company, name="general").first()
        self.assertIsNotNone(general_channel)

        # Create root agent with company
        coo_alpha = Agent.objects.create(
            owner=self.user,
            company=company,
            name="Alpha COO",
            role="COO",
            depth=0
        )
        self.assertEqual(coo_alpha.company, company)

        # Create sub-agent and verify company is automatically propagated
        sub_agent = coo_alpha.create_sub_agent("Alpha Dev Lead", "Tech Lead")
        self.assertEqual(sub_agent.company, company)

    def test_company_session_active_selection(self):
        from corp.services import company_service
        from django.test import RequestFactory
        from django.contrib.sessions.middleware import SessionMiddleware

        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        
        # Add session support to dummy request
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        # Initial call should auto-create or fetch active company
        active_company = company_service.get_active_company(request)
        self.assertIsNotNone(active_company)
        self.assertEqual(request.session.get("active_company_id"), str(active_company.id))

        # Create a second company and switch
        company2 = company_service.create_company(
            owner=self.user,
            name="Beta Dynamics",
            industry="Aerospace AI"
        )
        switched = company_service.set_active_company(request, str(company2.id))
        self.assertEqual(switched, company2)
        self.assertEqual(request.session.get("active_company_id"), str(company2.id))

