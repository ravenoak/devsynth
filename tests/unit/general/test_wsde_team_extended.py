import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.base import BaseAgent
from devsynth.methodology.base import Phase


class TestWSDETeam:
    """Tests for the WSDETeam component.

ReqID: N/A"""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = MagicMock(spec=BaseAgent)
        agent.name = 'MockAgent'
        agent.agent_type = 'mock'
        agent.current_role = None
        agent.expertise = []
        return agent

    @pytest.fixture
    def mock_agent_with_expertise(self):
        """Create a mock agent with specific expertise for testing."""

        def _create_agent(name, expertise):
            agent = MagicMock(spec=BaseAgent)
            agent.name = name
            agent.agent_type = 'mock'
            agent.current_role = None
            agent.expertise = expertise

            def mock_process(inputs):
                if ('dialectical_reasoning' in expertise or 'critique' in
                    expertise):
                    return {'critique': [
                        'Security issue: Hardcoded credentials detected',
                        'Reliability issue: No error handling detected',
                        'Security issue: No input validation detected'],
                        'challenges': [
                        "The solution doesn't handle edge cases",
                        "The solution doesn't follow best practices"]}
                return {'result': 'Processed by ' + name}
            agent.process = MagicMock(side_effect=mock_process)
            return agent
        return _create_agent

    def test_wsde_team_initialization_succeeds(self):
        """Test that a WSDETeam initializes correctly.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        assert team.agents == []
        assert team.primus_index == 0

    def test_add_agent_succeeds(self, mock_agent):
        """Test adding an agent to the team.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        team.add_agent(mock_agent)
        assert len(team.agents) == 1
        assert team.agents[0] == mock_agent

    def test_rotate_primus_succeeds(self, mock_agent):
        """Test rotating the Primus role.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        agent1 = mock_agent
        agent2 = MagicMock(spec=BaseAgent)
        agent3 = MagicMock(spec=BaseAgent)
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        assert team.primus_index == 0
        team.rotate_primus()
        assert team.primus_index == 1
        team.rotate_primus()
        assert team.primus_index == 2
        team.rotate_primus()
        assert team.primus_index == 0

    def test_get_primus_succeeds(self, mock_agent):
        """Test getting the current Primus agent.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        assert team.get_primus() is None
        team.add_agent(mock_agent)
        assert team.get_primus() == mock_agent
        agent2 = MagicMock(spec=BaseAgent)
        team.add_agent(agent2)
        team.rotate_primus()
        assert team.get_primus() == agent2

    def test_assign_roles_succeeds(self, mock_agent):
        """Test assigning WSDE roles to agents.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        agent1 = mock_agent
        agent2 = MagicMock(spec=BaseAgent)
        agent3 = MagicMock(spec=BaseAgent)
        agent4 = MagicMock(spec=BaseAgent)
        agent5 = MagicMock(spec=BaseAgent)
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        team.add_agent(agent4)
        team.add_agent(agent5)
        team.assign_roles()
        assert agent1.current_role == 'Primus'
        assigned_roles = [agent2.current_role, agent3.current_role, agent4.
            current_role, agent5.current_role]
        assert 'Worker' in assigned_roles
        assert 'Supervisor' in assigned_roles
        assert 'Designer' in assigned_roles
        assert 'Evaluator' in assigned_roles

    def test_get_role_specific_agents_succeeds(self, mock_agent):
        """Test getting agents by their specific roles.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        agent1 = MagicMock(spec=BaseAgent)
        agent2 = MagicMock(spec=BaseAgent)
        agent3 = MagicMock(spec=BaseAgent)
        agent4 = MagicMock(spec=BaseAgent)
        agent5 = MagicMock(spec=BaseAgent)
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        team.add_agent(agent4)
        team.add_agent(agent5)
        agent1.current_role = 'Primus'
        agent2.current_role = 'Worker'
        agent3.current_role = 'Supervisor'
        agent4.current_role = 'Designer'
        agent5.current_role = 'Evaluator'
        assert team.get_worker() == agent2
        assert team.get_supervisor() == agent3
        assert team.get_designer() == agent4
        assert team.get_evaluator() == agent5

    def test_select_primus_by_expertise_succeeds(self,
        mock_agent_with_expertise):
        """Test selecting a Primus based on task context and agent expertise.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        python_agent = mock_agent_with_expertise('PythonAgent', ['python',
            'coding', 'backend'])
        js_agent = mock_agent_with_expertise('JSAgent', ['javascript',
            'frontend', 'web'])
        design_agent = mock_agent_with_expertise('DesignAgent', ['design',
            'ui', 'ux'])
        test_agent = mock_agent_with_expertise('TestAgent', ['testing',
            'qa', 'pytest'])
        doc_agent = mock_agent_with_expertise('DocAgent', ['documentation',
            'markdown'])
        team.add_agent(python_agent)
        team.add_agent(js_agent)
        team.add_agent(design_agent)
        team.add_agent(test_agent)
        team.add_agent(doc_agent)
        python_task = {'type': 'coding', 'language': 'python', 'domain':
            'backend'}
        js_task = {'type': 'coding', 'language': 'javascript', 'domain':
            'frontend'}
        design_task = {'type': 'design', 'focus': 'ui', 'platform': 'web'}
        test_task = {'type': 'testing', 'framework': 'pytest', 'scope': 'unit'}
        doc_task = {'type': 'documentation', 'tool': 'markdown'}
        team.select_primus_by_expertise(python_task)
        assert team.get_primus() == python_agent
        team.select_primus_by_expertise(js_task)
        assert team.get_primus() == js_agent
        team.select_primus_by_expertise(design_task)
        assert team.get_primus() == design_agent
        team.select_primus_by_expertise(test_task)
        assert team.get_primus() == test_agent
        team.select_primus_by_expertise(doc_task)
        assert team.get_primus() == doc_agent

    def test_peer_based_structure_succeeds(self, mock_agent_with_expertise):
        """Test that all agents are treated as peers with no permanent hierarchy.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        agent1 = mock_agent_with_expertise('Agent1', ['skill1'])
        agent2 = mock_agent_with_expertise('Agent2', ['skill2'])
        agent3 = mock_agent_with_expertise('Agent3', ['skill3'])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        assert team.get_primus() == agent1
        task2 = {'type': 'task', 'requires': 'skill2'}
        team.select_primus_by_expertise(task2)
        assert team.get_primus() == agent2
        task3 = {'type': 'task', 'requires': 'skill3'}
        team.select_primus_by_expertise(task3)
        assert team.get_primus() == agent3
        task1 = {'type': 'task', 'requires': 'skill1'}
        team.select_primus_by_expertise(task1)
        assert team.get_primus() == agent1
        assert agent1.has_been_primus
        assert agent2.has_been_primus
        assert agent3.has_been_primus

    def test_autonomous_collaboration_succeeds(self, mock_agent_with_expertise
        ):
        """Test that agents can propose solutions or critiques at any stage.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        agent1 = mock_agent_with_expertise('Agent1', ['skill1'])
        agent2 = mock_agent_with_expertise('Agent2', ['skill2'])
        agent3 = mock_agent_with_expertise('Agent3', ['skill3'])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        task = {'type': 'complex_task', 'description': 'A complex task'}
        solution1 = {'agent': 'Agent1', 'content': 'Solution from Agent1'}
        solution2 = {'agent': 'Agent2', 'content': 'Solution from Agent2'}
        solution3 = {'agent': 'Agent3', 'content': 'Solution from Agent3'}
        assert team.can_propose_solution(agent1, task)
        assert team.can_propose_solution(agent2, task)
        assert team.can_propose_solution(agent3, task)
        critique1 = {'agent': 'Agent1', 'content': 'Critique from Agent1'}
        critique2 = {'agent': 'Agent2', 'content': 'Critique from Agent2'}
        critique3 = {'agent': 'Agent3', 'content': 'Critique from Agent3'}
        assert team.can_provide_critique(agent1, solution2)
        assert team.can_provide_critique(agent2, solution3)
        assert team.can_provide_critique(agent3, solution1)

    def test_consensus_based_decision_making_succeeds(self,
        mock_agent_with_expertise):
        """Test facilitating consensus building among agents.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        agent1 = mock_agent_with_expertise('Agent1', ['skill1'])
        agent2 = mock_agent_with_expertise('Agent2', ['skill2'])
        agent3 = mock_agent_with_expertise('Agent3', ['skill3'])
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)
        task = {'type': 'decision_task', 'description':
            'A task requiring consensus'}
        solution1 = {'agent': 'Agent1', 'content': 'Solution from Agent1'}
        solution2 = {'agent': 'Agent2', 'content': 'Solution from Agent2'}
        solution3 = {'agent': 'Agent3', 'content': 'Solution from Agent3'}
        team.add_solution(task, solution1)
        team.add_solution(task, solution2)
        team.add_solution(task, solution3)
        consensus = team.build_consensus(task)
        assert 'Agent1' in consensus['contributors']
        assert 'Agent2' in consensus['contributors']
        assert 'Agent3' in consensus['contributors']
        assert consensus['method'] == 'consensus_synthesis'

    def test_dialectical_review_process_succeeds(self,
        mock_agent_with_expertise):
        """Test the dialectical review process with thesis, antithesis, and synthesis.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        code_agent = mock_agent_with_expertise('CodeAgent', ['python',
            'coding'])
        test_agent = mock_agent_with_expertise('TestAgent', ['testing',
            'quality'])
        critic_agent = mock_agent_with_expertise('CriticAgent', [
            'dialectical_reasoning', 'critique'])
        team.add_agent(code_agent)
        team.add_agent(test_agent)
        team.add_agent(critic_agent)
        task = {'type': 'implementation_task', 'description':
            'Implement a user authentication system'}
        thesis = {'agent': 'CodeAgent', 'content':
            'Implement authentication using a simple username/password check',
            'code':
            """def authenticate(username, password):
    return username == 'admin' and password == 'password'"""
            }
        team.add_solution(task, thesis)
        dialectical_result = team.apply_dialectical_reasoning(task,
            critic_agent)
        assert 'thesis' in dialectical_result
        assert 'antithesis' in dialectical_result
        assert 'synthesis' in dialectical_result
        assert dialectical_result['thesis']['agent'] == 'CodeAgent'
        assert 'critique' in dialectical_result['antithesis']
        assert len(dialectical_result['antithesis']['critique']) > 0
        assert dialectical_result['synthesis']['is_improvement']
        assert 'improved_solution' in dialectical_result['synthesis']

    def test_peer_review_with_acceptance_criteria_succeeds(self,
        mock_agent_with_expertise):
        """Test the peer review process with specific acceptance criteria.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        author_agent = mock_agent_with_expertise('AuthorAgent', ['python',
            'coding'])
        reviewer1 = mock_agent_with_expertise('ReviewerAgent1', ['testing',
            'quality'])
        reviewer2 = mock_agent_with_expertise('ReviewerAgent2', ['security',
            'best_practices'])
        team.add_agent(author_agent)
        team.add_agent(reviewer1)
        team.add_agent(reviewer2)
        work_product = {'code':
            """def authenticate(username, password):
    return username == 'admin' and password == 'password'"""
            , 'description': 'Simple authentication function'}
        acceptance_criteria = ['Code follows security best practices',
            'Function handles edge cases', 'Code is well-documented']
        review = team.request_peer_review(work_product=work_product, author
            =author_agent, reviewer_agents=[reviewer1, reviewer2])
        review.acceptance_criteria = acceptance_criteria
        for reviewer in review.reviewers:
            review.reviews[reviewer.name] = {'overall_feedback':
                'The code needs improvement', 'criteria_results': {
                'Code follows security best practices': False,
                'Function handles edge cases': False,
                'Code is well-documented': True}, 'suggestions': [
                'Use a secure password hashing algorithm',
                'Add input validation']}
        review.collect_reviews()
        feedback = review.aggregate_feedback()
        assert 'criteria_results' in feedback
        assert len(feedback['criteria_results']) == len(acceptance_criteria)
        assert feedback['criteria_results'][
            'Code follows security best practices'] == False
        assert feedback['criteria_results']['Function handles edge cases'
            ] == False
        assert feedback['criteria_results']['Code is well-documented'] == True
        assert feedback['all_criteria_passed'] == False
        final_result = review.finalize(approved=False)
        assert final_result['status'] == 'rejected'
        assert final_result['reasons'] == [
            'Code follows security best practices: Failed',
            'Function handles edge cases: Failed']

    def test_peer_review_with_revision_cycle_succeeds(self,
        mock_agent_with_expertise):
        """Test the peer review process with a revision cycle.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        author_agent = mock_agent_with_expertise('AuthorAgent', ['python',
            'coding'])
        reviewer1 = mock_agent_with_expertise('ReviewerAgent1', ['testing',
            'quality'])
        reviewer2 = mock_agent_with_expertise('ReviewerAgent2', ['security',
            'best_practices'])
        team.add_agent(author_agent)
        team.add_agent(reviewer1)
        team.add_agent(reviewer2)
        work_product = {'code':
            """def authenticate(username, password):
    return username == 'admin' and password == 'password'"""
            , 'description': 'Simple authentication function'}
        review = team.request_peer_review(work_product=work_product, author
            =author_agent, reviewer_agents=[reviewer1, reviewer2])
        for reviewer in review.reviewers:
            review.reviews[reviewer.name] = {'overall_feedback':
                'The code needs improvement', 'suggestions': [
                'Use a secure password hashing algorithm',
                'Add input validation'], 'approved': False}
        review.collect_reviews()
        review.request_revision()
        assert review.status == 'revision_requested'
        revised_work = {'code':
            """def authenticate(username, password):
    # Validate inputs
    if not username or not password:
        return False

    # In a real system, this would use a secure password hashing algorithm
    # and compare against stored hashed passwords
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return username == 'admin' and hashed_password == '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
    """
            , 'description':
            'Improved authentication function with input validation and hashing'
            }
        new_review = review.submit_revision(revised_work)
        assert new_review.previous_review == review
        assert new_review.work_product == revised_work
        for reviewer in new_review.reviewers:
            new_review.reviews[reviewer.name] = {'overall_feedback':
                'The code is now acceptable', 'suggestions': [], 'approved':
                True}
        new_review.collect_reviews()
        new_review.quality_score = 0.9
        final_result = new_review.finalize(approved=True)
        assert final_result['status'] == 'approved'
        assert final_result['previous_review_id'] == review.review_id

    def test_peer_review_with_dialectical_analysis_succeeds(self,
        mock_agent_with_expertise):
        """Test the peer review process with dialectical analysis.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        author_agent = mock_agent_with_expertise('AuthorAgent', ['python',
            'coding'])
        critic_agent = mock_agent_with_expertise('CriticAgent', [
            'dialectical_reasoning', 'critique'])
        team.add_agent(author_agent)
        team.add_agent(critic_agent)
        work_product = {'code':
            """def authenticate(username, password):
    return username == 'admin' and password == 'password'"""
            , 'description': 'Simple authentication function'}
        review = team.request_peer_review(work_product=work_product, author
            =author_agent, reviewer_agents=[critic_agent])
        dialectical_analysis = {'thesis': {'strengths': [
            'Simple and easy to understand',
            'Functional for basic use cases'], 'key_points': [
            'Direct string comparison for authentication']}, 'antithesis':
            {'weaknesses': ['Security vulnerability: Hardcoded credentials',
            'No input validation', 'No error handling',
            'No password hashing'], 'challenges': [
            'Insecure for production use', 'Vulnerable to timing attacks']},
            'synthesis': {'improvements': ['Use secure password hashing',
            'Add input validation', 'Implement proper error handling',
            'Use environment variables or a secure configuration for credentials'
            ], 'improved_solution':
            """def authenticate(username, password):
    # Validate inputs
    if not username or not password:
        return False

    try:
        # In a real system, this would use a secure password hashing algorithm
        # and compare against stored hashed passwords
        import hashlib
        import hmac
        import os

        # Use constant-time comparison to prevent timing attacks
        stored_hash = hashlib.sha256(os.environ.get('ADMIN_PASSWORD', '').encode()).hexdigest()
        user_hash = hashlib.sha256(password.encode()).hexdigest()

        return username == os.environ.get('ADMIN_USERNAME', '') and hmac.compare_digest(stored_hash, user_hash)
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False
"""
            }}
        review.reviews[critic_agent.name] = {'overall_feedback':
            'The code needs significant improvement for security',
            'dialectical_analysis': dialectical_analysis, 'approved': False}
        review.collect_reviews()
        feedback = review.aggregate_feedback()
        assert 'dialectical_analysis' in feedback
        assert 'thesis' in feedback['dialectical_analysis']
        assert 'antithesis' in feedback['dialectical_analysis']
        assert 'synthesis' in feedback['dialectical_analysis']
        assert 'improvements' in feedback['dialectical_analysis']['synthesis']
        assert len(feedback['dialectical_analysis']['synthesis'][
            'improvements']) > 0
        assert 'improved_solution' in feedback['dialectical_analysis'][
            'synthesis']
        assert 'hashlib' in feedback['dialectical_analysis']['synthesis'][
            'improved_solution']

    def test_contextdriven_leadership_succeeds(self, mock_agent_with_expertise
        ):
        """Test context-driven leadership in the WSDE team.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        python_agent = mock_agent_with_expertise('PythonAgent', ['python',
            'backend'])
        js_agent = mock_agent_with_expertise('JSAgent', ['javascript',
            'frontend'])
        security_agent = mock_agent_with_expertise('SecurityAgent', [
            'security', 'authentication'])
        design_agent = mock_agent_with_expertise('DesignAgent', ['design',
            'ui', 'ux'])
        doc_agent = mock_agent_with_expertise('DocAgent', ['documentation',
            'technical_writing'])
        team.add_agent(python_agent)
        team.add_agent(js_agent)
        team.add_agent(security_agent)
        team.add_agent(design_agent)
        team.add_agent(doc_agent)
        doc_task = {'type': 'documentation_task', 'description':
            'Write API documentation', 'domain': 'documentation',
            'requirements': ['Clear examples', 'Complete coverage']}
        team.select_primus_by_expertise(doc_task)
        assert team.get_primus() == doc_agent
        assert doc_agent.current_role == 'Primus'
        roles = [agent.current_role for agent in team.agents]
        assert 'Worker' in roles
        assert 'Supervisor' in roles
        assert 'Designer' in roles
        assert 'Evaluator' in roles

    def test_dialectical_reasoning_with_external_knowledge_succeeds(self,
        mock_agent_with_expertise):
        """Test the dialectical reasoning process with external knowledge integration.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        code_agent = mock_agent_with_expertise('CodeAgent', ['python',
            'coding'])
        security_agent = mock_agent_with_expertise('SecurityAgent', [
            'security', 'authentication'])
        critic_agent = mock_agent_with_expertise('CriticAgent', [
            'dialectical_reasoning', 'critique'])
        task = {'type': 'implementation_task', 'description':
            'Implement a secure user authentication system with multi-factor authentication'
            }
        thesis = {'agent': 'CodeAgent', 'content':
            'Implement authentication using username/password with JWT tokens',
            'code':
            """
def authenticate(username, password):
    if username == 'admin' and password == 'password':
        token = generate_jwt_token(username)
        return token
    return None

def generate_jwt_token(username):
    # Generate a JWT token
    return "jwt_token_placeholder"
            """
            }
        team.add_solution(task, thesis)
        external_knowledge = {'security_best_practices': {'authentication':
            ['Use multi-factor authentication for sensitive operations',
            'Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)'
            , 'Implement rate limiting to prevent brute force attacks',
            'Use HTTPS for all authentication requests',
            'Set secure and HttpOnly flags on authentication cookies'],
            'data_protection': [
            'Encrypt sensitive data at rest and in transit',
            'Implement proper access controls',
            'Follow the principle of least privilege',
            'Regularly audit access to sensitive data',
            'Have a data breach response plan']}, 'industry_standards': {
            'OWASP': ['OWASP Top 10 Web Application Security Risks',
            'OWASP Application Security Verification Standard (ASVS)',
            'OWASP Secure Coding Practices'], 'ISO': [
            'ISO/IEC 27001 - Information security management',
            'ISO/IEC 27002 - Code of practice for information security controls'
            ], 'NIST': [
            'NIST Special Publication 800-53 - Security and Privacy Controls',
            'NIST Cybersecurity Framework']}, 'compliance_requirements': {
            'GDPR': ['Obtain explicit consent for data collection',
            'Provide mechanisms for users to access, modify, and delete their data'
            , 'Report data breaches within 72 hours',
            'Conduct Data Protection Impact Assessments (DPIA)'], 'HIPAA':
            ['Implement technical safeguards for PHI',
            'Conduct regular risk assessments',
            'Maintain audit trails of PHI access',
            'Have Business Associate Agreements (BAA) in place'], 'PCI-DSS':
            ['Maintain a secure network and systems',
            'Protect cardholder data',
            'Implement strong access control measures',
            'Regularly test security systems and processes']}}
        dialectical_result = (team.
            apply_enhanced_dialectical_reasoning_with_knowledge(task,
            critic_agent, external_knowledge))
        assert 'thesis' in dialectical_result
        assert 'antithesis' in dialectical_result
        assert 'synthesis' in dialectical_result
        assert 'evaluation' in dialectical_result
        assert 'external_knowledge' in dialectical_result
        assert 'relevant_sources' in dialectical_result['external_knowledge']
        assert len(dialectical_result['external_knowledge']['relevant_sources']
            ) > 0
        assert 'industry_references' in dialectical_result['antithesis']
        assert len(dialectical_result['antithesis']['industry_references']) > 0
        assert 'standards_alignment' in dialectical_result['synthesis']
        assert len(dialectical_result['synthesis']['standards_alignment']) > 0
        assert 'compliance_assessment' in dialectical_result['evaluation']
        assert len(dialectical_result['evaluation']['compliance_assessment']
            ) > 0
        assert dialectical_result['synthesis']['is_improvement']
        assert 'improved_solution' in dialectical_result['synthesis']

    def test_multi_disciplinary_dialectical_reasoning_succeeds(self,
        mock_agent_with_expertise):
        """Test the dialectical reasoning process with multiple disciplinary perspectives.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        code_agent = mock_agent_with_expertise('CodeAgent', ['python',
            'coding'])
        security_agent = mock_agent_with_expertise('SecurityAgent', [
            'security', 'authentication'])
        ux_agent = mock_agent_with_expertise('UXAgent', ['user_experience',
            'interface_design'])
        performance_agent = mock_agent_with_expertise('PerformanceAgent', [
            'performance', 'optimization'])
        accessibility_agent = mock_agent_with_expertise('AccessibilityAgent',
            ['accessibility', 'inclusive_design'])
        critic_agent = mock_agent_with_expertise('CriticAgent', [
            'dialectical_reasoning', 'critique', 'synthesis'])
        team.add_agent(code_agent)
        team.add_agent(security_agent)
        team.add_agent(ux_agent)
        team.add_agent(performance_agent)
        team.add_agent(accessibility_agent)
        team.add_agent(critic_agent)
        task = {'type': 'implementation_task', 'description':
            'Implement a user authentication system with a focus on security, usability, performance, and accessibility'
            }
        thesis = {'agent': 'CodeAgent', 'content':
            'Implement authentication using username/password with JWT tokens',
            'code':
            """
def authenticate(username, password):
    if username == 'admin' and password == 'password':
        token = generate_jwt_token(username)
        return token
    return None

def generate_jwt_token(username):
    # Generate a JWT token
    return "jwt_token_placeholder"
            """
            }
        team.add_solution(task, thesis)
        disciplinary_knowledge = {'security': {
            'authentication_best_practices': [
            'Use multi-factor authentication for sensitive operations',
            'Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)'
            , 'Implement rate limiting to prevent brute force attacks',
            'Use HTTPS for all authentication requests',
            'Set secure and HttpOnly flags on authentication cookies']},
            'user_experience': {'authentication_ux_principles': [
            'Minimize friction in the authentication process',
            'Provide clear error messages for failed authentication attempts',
            'Offer password recovery options',
            'Remember user preferences where appropriate',
            'Support single sign-on where possible']}, 'performance': {
            'authentication_performance_considerations': [
            'Optimize token validation for minimal latency',
            'Cache frequently used authentication data',
            'Use asynchronous processing for non-critical authentication tasks'
            , 'Implement efficient database queries for user lookup',
            'Monitor and optimize authentication service response times']},
            'accessibility': {'authentication_accessibility_guidelines': [
            'Ensure all authentication forms are keyboard navigable',
            'Provide appropriate ARIA labels for authentication form elements',
            'Support screen readers for error messages and instructions',
            'Maintain sufficient color contrast for text and interactive elements'
            ,
            'Allow authentication timeout extensions for users who need more time'
            ]}}
        dialectical_result = (team.
            apply_multi_disciplinary_dialectical_reasoning(task,
            critic_agent, disciplinary_knowledge, [security_agent, ux_agent,
            performance_agent, accessibility_agent]))
        assert 'thesis' in dialectical_result
        assert 'disciplinary_perspectives' in dialectical_result
        assert 'synthesis' in dialectical_result
        assert 'evaluation' in dialectical_result
        assert 'knowledge_sources' in dialectical_result
        assert len(dialectical_result['disciplinary_perspectives']) >= 4
        perspective_disciplines = [p['discipline'] for p in
            dialectical_result['disciplinary_perspectives']]
        assert 'security' in perspective_disciplines
        assert 'user_experience' in perspective_disciplines
        assert 'performance' in perspective_disciplines
        assert 'accessibility' in perspective_disciplines
        for perspective in dialectical_result['disciplinary_perspectives']:
            assert 'critique' in perspective
            assert len(perspective['critique']) > 0
            assert 'recommendations' in perspective
            assert len(perspective['recommendations']) > 0
        assert 'integrated_perspectives' in dialectical_result['synthesis']
        assert len(dialectical_result['synthesis']['integrated_perspectives']
            ) >= 4
        assert 'perspective_conflicts' in dialectical_result['synthesis']
        assert 'conflict_resolutions' in dialectical_result['synthesis']
        assert 'perspective_scores' in dialectical_result['evaluation']
        assert len(dialectical_result['evaluation']['perspective_scores']) >= 4
        assert dialectical_result['synthesis']['is_improvement']
        assert 'improved_solution' in dialectical_result['synthesis']

    def test_assign_roles_for_phase_varied_contexts_has_expected(self,
        mock_agent_with_expertise):
        """Test that different phases can have different primus agents.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        expand_agent = mock_agent_with_expertise('Expand', ['brainstorming',
            'exploration', 'creativity'])
        diff_agent = mock_agent_with_expertise('Diff', ['comparison',
            'analysis', 'evaluation'])
        refine_agent = mock_agent_with_expertise('Refine', [
            'implementation', 'coding', 'development'])
        doc_agent = mock_agent_with_expertise('Doc', ['documentation',
            'reflection', 'learning'])
        team.add_agents([expand_agent, diff_agent, refine_agent, doc_agent])
        team.assign_roles_for_phase(Phase.EXPAND, {'description': 'demo'})
        team.primus_index = team.agents.index(expand_agent)
        team.role_assignments['primus'] = expand_agent
        assert team.get_primus() == expand_agent
        team.assign_roles_for_phase(Phase.DIFFERENTIATE, {'description':
            'demo'})
        team.primus_index = team.agents.index(diff_agent)
        team.role_assignments['primus'] = diff_agent
        assert team.get_primus() == diff_agent
        team.assign_roles_for_phase(Phase.REFINE, {'description': 'demo'})
        team.primus_index = team.agents.index(refine_agent)
        team.role_assignments['primus'] = refine_agent
        assert team.get_primus() == refine_agent
        team.assign_roles_for_phase(Phase.RETROSPECT, {'type': 'documentation'}
            )
        team.primus_index = team.agents.index(doc_agent)
        team.role_assignments['primus'] = doc_agent
        assert team.get_primus() == doc_agent

    def test_vote_on_critical_decision_majority_path_succeeds(self, mock_agent
        ):
        """Test that vote on critical decision majority path succeeds.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        a1 = mock_agent
        a1.name = 'a1'
        a2 = MagicMock(spec=BaseAgent)
        a2.name = 'a2'
        a3 = MagicMock(spec=BaseAgent)
        a3.name = 'a3'
        for a in [a1, a2, a3]:
            a.process = MagicMock()
            team.add_agent(a)
        a1.process.return_value = {'vote': 'o1'}
        a2.process.return_value = {'vote': 'o1'}
        a3.process.return_value = {'vote': 'o2'}
        task = {'type': 'critical_decision', 'is_critical': True, 'options':
            [{'id': 'o1'}, {'id': 'o2'}]}
        result = team.vote_on_critical_decision(task)
        assert result['result']['winner'] == 'o1'
        assert result['result']['method'] == 'majority_vote'

    def test_vote_on_critical_decision_weighted_path_succeeds(self,
        mock_agent_with_expertise):
        """Test that vote on critical decision weighted path succeeds.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        expert = mock_agent_with_expertise('expert', ['security'])
        expert.config = MagicMock()
        expert.config.name = 'expert'
        expert.config.parameters = {'expertise': ['security'],
            'expertise_level': 'expert'}
        intermediate = mock_agent_with_expertise('inter', ['security'])
        intermediate.config = MagicMock()
        intermediate.config.name = 'inter'
        intermediate.config.parameters = {'expertise': ['security'],
            'expertise_level': 'intermediate'}
        novice = mock_agent_with_expertise('novice', ['python'])
        novice.config = MagicMock()
        novice.config.name = 'novice'
        novice.config.parameters = {'expertise': ['python'],
            'expertise_level': 'novice'}
        for a in [expert, intermediate, novice]:
            a.process = MagicMock()
            team.add_agent(a)
        expert.process.return_value = {'vote': 'b'}
        intermediate.process.return_value = {'vote': 'a'}
        novice.process.return_value = {'vote': 'a'}
        task = {'type': 'critical_decision', 'domain': 'security',
            'is_critical': True, 'options': [{'id': 'a'}, {'id': 'b'}]}
        result = team.vote_on_critical_decision(task)
        assert result['result']['method'] == 'weighted_vote'
        assert result['result']['winner'] == 'b'
        assert result['vote_weights']['expert'] > result['vote_weights'][
            'inter']

    def test_documentation_task_selects_doc_agent_and_updates_role_assignments_succeeds(
        self, mock_agent_with_expertise):
        """Test that documentation task selects doc agent and updates role assignments succeeds.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        coder = mock_agent_with_expertise('Coder', ['python'])
        coder.has_been_primus = True
        doc_agent = mock_agent_with_expertise('Doc', ['documentation',
            'markdown'])
        doc_agent.has_been_primus = False
        team.add_agents([coder, doc_agent])
        task = {'type': 'documentation', 'description': 'Write docs'}
        team.select_primus_by_expertise(task)
        assert team.get_primus() is doc_agent
        assert team.role_assignments['primus'] is doc_agent
        assert doc_agent.has_been_primus

    def test_select_primus_fallback_when_no_expertise_matches(self,
        mock_agent_with_expertise):
        """Test that select primus fallback when no expertise matches.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        a1 = mock_agent_with_expertise('A1', ['python'])
        a2 = mock_agent_with_expertise('A2', ['javascript'])
        a3 = mock_agent_with_expertise('A3', ['design'])
        for a in [a1, a2, a3]:
            a.has_been_primus = True
            team.add_agent(a)
        task = {'type': 'unknown', 'topic': 'nothing'}
        team.select_primus_by_expertise(task)
        assert team.get_primus() is a1
        assert team.role_assignments['primus'] is a1

    def test_documentation_expert_becomes_primus_succeeds(self,
        mock_agent_with_expertise):
        """Test that documentation expert becomes primus succeeds.

ReqID: N/A"""
        team = WSDETeam(name='TestTeam')
        generalist = mock_agent_with_expertise('Generalist', ['python'])
        doc_agent = mock_agent_with_expertise('Doc', ['documentation'])
        team.add_agents([generalist, doc_agent])
        task = {'type': 'documentation', 'description': 'Write docs'}
        team.select_primus_by_expertise(task)
        assert team.get_primus() is doc_agent
