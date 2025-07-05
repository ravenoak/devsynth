import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.base import BaseAgent
from devsynth.methodology.base import Phase


class TestWSDETeam:
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = MagicMock(spec=BaseAgent)
        agent.name = "MockAgent"
        agent.agent_type = "mock"
        agent.current_role = None
        agent.expertise = []
        return agent

    @pytest.fixture
    def mock_agent_with_expertise(self):
        """Create a mock agent with specific expertise for testing."""

        def _create_agent(name, expertise):
            agent = MagicMock(spec=BaseAgent)
            agent.name = name
            agent.agent_type = "mock"
            agent.current_role = None
            agent.expertise = expertise

            # Mock the process method to return a critique
            def mock_process(inputs):
                if "dialectical_reasoning" in expertise or "critique" in expertise:
                    return {
                        "critique": [
                            "Security issue: Hardcoded credentials detected",
                            "Reliability issue: No error handling detected",
                            "Security issue: No input validation detected"
                        ],
                        "challenges": [
                            "The solution doesn't handle edge cases",
                            "The solution doesn't follow best practices"
                        ]
                    }
                return {"result": "Processed by " + name}

            agent.process = MagicMock(side_effect=mock_process)
            return agent

        return _create_agent

    def test_wsde_team_initialization(self):
        """Test that a WSDETeam initializes correctly."""
        team = WSDETeam()
        assert team.agents == []
        assert team.primus_index == 0

    def test_add_agent(self, mock_agent):
        """Test adding an agent to the team."""
        team = WSDETeam()
        team.add_agent(mock_agent)
        assert len(team.agents) == 1
        assert team.agents[0] == mock_agent

    def test_rotate_primus(self, mock_agent):
        """Test rotating the Primus role."""
        team = WSDETeam()

        # Add multiple agents
        agent1 = mock_agent
        agent2 = MagicMock(spec=BaseAgent)
        agent3 = MagicMock(spec=BaseAgent)

        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Initially, primus_index should be 0
        assert team.primus_index == 0

        # After rotation, it should be 1
        team.rotate_primus()
        assert team.primus_index == 1

        # After another rotation, it should be 2
        team.rotate_primus()
        assert team.primus_index == 2

        # After another rotation, it should wrap back to 0
        team.rotate_primus()
        assert team.primus_index == 0

    def test_get_primus(self, mock_agent):
        """Test getting the current Primus agent."""
        team = WSDETeam()

        # With no agents, get_primus should return None
        assert team.get_primus() is None

        # Add an agent and check that it's the Primus
        team.add_agent(mock_agent)
        assert team.get_primus() == mock_agent

        # Add another agent and rotate Primus
        agent2 = MagicMock(spec=BaseAgent)
        team.add_agent(agent2)
        team.rotate_primus()
        assert team.get_primus() == agent2

    def test_assign_roles(self, mock_agent):
        """Test assigning WSDE roles to agents."""
        team = WSDETeam()

        # Add multiple agents
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

        # Assign roles
        team.assign_roles()

        # Check that roles are assigned correctly
        assert agent1.current_role == "Primus"

        # Other agents should have Worker, Supervisor, Designer, or Evaluator roles
        assigned_roles = [
            agent2.current_role,
            agent3.current_role,
            agent4.current_role,
            agent5.current_role,
        ]
        assert "Worker" in assigned_roles
        assert "Supervisor" in assigned_roles
        assert "Designer" in assigned_roles
        assert "Evaluator" in assigned_roles

    def test_get_role_specific_agents(self, mock_agent):
        """Test getting agents by their specific roles."""
        team = WSDETeam()

        # Add multiple agents
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

        # Manually assign roles for testing
        agent1.current_role = "Primus"
        agent2.current_role = "Worker"
        agent3.current_role = "Supervisor"
        agent4.current_role = "Designer"
        agent5.current_role = "Evaluator"

        # Test getting agents by role
        assert team.get_worker() == agent2
        assert team.get_supervisor() == agent3
        assert team.get_designer() == agent4
        assert team.get_evaluator() == agent5

    def test_select_primus_by_expertise(self, mock_agent_with_expertise):
        """Test selecting a Primus based on task context and agent expertise."""
        team = WSDETeam()

        # Create agents with different expertise
        python_agent = mock_agent_with_expertise(
            "PythonAgent", ["python", "coding", "backend"]
        )
        js_agent = mock_agent_with_expertise(
            "JSAgent", ["javascript", "frontend", "web"]
        )
        design_agent = mock_agent_with_expertise("DesignAgent", ["design", "ui", "ux"])
        test_agent = mock_agent_with_expertise("TestAgent", ["testing", "qa", "pytest"])
        doc_agent = mock_agent_with_expertise("DocAgent", ["documentation", "markdown"])

        # Add agents to the team
        team.add_agent(python_agent)
        team.add_agent(js_agent)
        team.add_agent(design_agent)
        team.add_agent(test_agent)
        team.add_agent(doc_agent)

        # Define tasks requiring different expertise
        python_task = {"type": "coding", "language": "python", "domain": "backend"}
        js_task = {"type": "coding", "language": "javascript", "domain": "frontend"}
        design_task = {"type": "design", "focus": "ui", "platform": "web"}
        test_task = {"type": "testing", "framework": "pytest", "scope": "unit"}
        doc_task = {"type": "documentation", "tool": "markdown"}

        # Test that the correct agent is selected as Primus for each task
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

    def test_peer_based_structure(self, mock_agent_with_expertise):
        """Test that all agents are treated as peers with no permanent hierarchy."""
        team = WSDETeam()

        # Create multiple agents
        agent1 = mock_agent_with_expertise("Agent1", ["skill1"])
        agent2 = mock_agent_with_expertise("Agent2", ["skill2"])
        agent3 = mock_agent_with_expertise("Agent3", ["skill3"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Initially, agent1 is Primus
        assert team.get_primus() == agent1

        # Define a task that matches agent2's expertise
        task2 = {"type": "task", "requires": "skill2"}
        team.select_primus_by_expertise(task2)
        assert team.get_primus() == agent2

        # Define a task that matches agent3's expertise
        task3 = {"type": "task", "requires": "skill3"}
        team.select_primus_by_expertise(task3)
        assert team.get_primus() == agent3

        # Define a task that matches agent1's expertise
        task1 = {"type": "task", "requires": "skill1"}
        team.select_primus_by_expertise(task1)
        assert team.get_primus() == agent1

        # Verify that all agents have been Primus at some point
        assert agent1.has_been_primus
        assert agent2.has_been_primus
        assert agent3.has_been_primus

    def test_autonomous_collaboration(self, mock_agent_with_expertise):
        """Test that agents can propose solutions or critiques at any stage."""
        team = WSDETeam()

        # Create multiple agents
        agent1 = mock_agent_with_expertise("Agent1", ["skill1"])
        agent2 = mock_agent_with_expertise("Agent2", ["skill2"])
        agent3 = mock_agent_with_expertise("Agent3", ["skill3"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create a task
        task = {"type": "complex_task", "description": "A complex task"}

        # Test that any agent can propose a solution
        solution1 = {"agent": "Agent1", "content": "Solution from Agent1"}
        solution2 = {"agent": "Agent2", "content": "Solution from Agent2"}
        solution3 = {"agent": "Agent3", "content": "Solution from Agent3"}

        # All agents should be able to propose solutions
        assert team.can_propose_solution(agent1, task)
        assert team.can_propose_solution(agent2, task)
        assert team.can_propose_solution(agent3, task)

        # Test that any agent can provide critiques
        critique1 = {"agent": "Agent1", "content": "Critique from Agent1"}
        critique2 = {"agent": "Agent2", "content": "Critique from Agent2"}
        critique3 = {"agent": "Agent3", "content": "Critique from Agent3"}

        # All agents should be able to provide critiques
        assert team.can_provide_critique(agent1, solution2)
        assert team.can_provide_critique(agent2, solution3)
        assert team.can_provide_critique(agent3, solution1)

    def test_consensus_based_decision_making(self, mock_agent_with_expertise):
        """Test facilitating consensus building among agents."""
        team = WSDETeam()

        # Create multiple agents
        agent1 = mock_agent_with_expertise("Agent1", ["skill1"])
        agent2 = mock_agent_with_expertise("Agent2", ["skill2"])
        agent3 = mock_agent_with_expertise("Agent3", ["skill3"])

        # Add agents to the team
        team.add_agent(agent1)
        team.add_agent(agent2)
        team.add_agent(agent3)

        # Create a task
        task = {"type": "decision_task", "description": "A task requiring consensus"}

        # Create multiple solutions
        solution1 = {"agent": "Agent1", "content": "Solution from Agent1"}
        solution2 = {"agent": "Agent2", "content": "Solution from Agent2"}
        solution3 = {"agent": "Agent3", "content": "Solution from Agent3"}

        # Add solutions to the team
        team.add_solution(task, solution1)
        team.add_solution(task, solution2)
        team.add_solution(task, solution3)

        # Test that the team can build consensus
        consensus = team.build_consensus(task)

        # The consensus should include input from all agents
        assert "Agent1" in consensus["contributors"]
        assert "Agent2" in consensus["contributors"]
        assert "Agent3" in consensus["contributors"]

        # No single agent should have dictatorial authority
        assert consensus["method"] == "consensus_synthesis"

    def test_dialectical_review_process(self, mock_agent_with_expertise):
        """Test the dialectical review process with thesis, antithesis, and synthesis."""
        team = WSDETeam()

        # Create agents including a critic
        code_agent = mock_agent_with_expertise("CodeAgent", ["python", "coding"])
        test_agent = mock_agent_with_expertise("TestAgent", ["testing", "quality"])
        critic_agent = mock_agent_with_expertise(
            "CriticAgent", ["dialectical_reasoning", "critique"]
        )

        # Add agents to the team
        team.add_agent(code_agent)
        team.add_agent(test_agent)
        team.add_agent(critic_agent)

        # Create a task
        task = {
            "type": "implementation_task",
            "description": "Implement a user authentication system",
        }

        # Create a proposed solution (thesis)
        thesis = {
            "agent": "CodeAgent",
            "content": "Implement authentication using a simple username/password check",
            "code": "def authenticate(username, password):\n    return username == 'admin' and password == 'password'",
        }

        # Add the thesis to the team
        team.add_solution(task, thesis)

        # Apply dialectical reasoning to the thesis
        dialectical_result = team.apply_dialectical_reasoning(task, critic_agent)

        # Verify that the dialectical result contains thesis, antithesis, and synthesis
        assert "thesis" in dialectical_result
        assert "antithesis" in dialectical_result
        assert "synthesis" in dialectical_result

        # Verify that the thesis matches the original solution
        assert dialectical_result["thesis"]["agent"] == "CodeAgent"

        # Verify that the antithesis identifies issues with the thesis
        assert "critique" in dialectical_result["antithesis"]
        assert len(dialectical_result["antithesis"]["critique"]) > 0

        # Verify that the synthesis improves upon the thesis
        assert dialectical_result["synthesis"]["is_improvement"]
        assert "improved_solution" in dialectical_result["synthesis"]

    def test_peer_review_with_acceptance_criteria(self, mock_agent_with_expertise):
        """Test the peer review process with specific acceptance criteria."""
        team = WSDETeam()

        # Create agents
        author_agent = mock_agent_with_expertise("AuthorAgent", ["python", "coding"])
        reviewer1 = mock_agent_with_expertise("ReviewerAgent1", ["testing", "quality"])
        reviewer2 = mock_agent_with_expertise("ReviewerAgent2", ["security", "best_practices"])

        # Add agents to the team
        team.add_agent(author_agent)
        team.add_agent(reviewer1)
        team.add_agent(reviewer2)

        # Create a work product
        work_product = {
            "code": "def authenticate(username, password):\n    return username == 'admin' and password == 'password'",
            "description": "Simple authentication function"
        }

        # Define acceptance criteria
        acceptance_criteria = [
            "Code follows security best practices",
            "Function handles edge cases",
            "Code is well-documented"
        ]

        # Request peer review with acceptance criteria
        review = team.request_peer_review(
            work_product=work_product,
            author=author_agent,
            reviewer_agents=[reviewer1, reviewer2]
        )

        # Set acceptance criteria
        review.acceptance_criteria = acceptance_criteria

        # Mock the review process
        for reviewer in review.reviewers:
            # Simulate reviewer evaluating against criteria
            review.reviews[reviewer.name] = {
                "overall_feedback": "The code needs improvement",
                "criteria_results": {
                    "Code follows security best practices": False,
                    "Function handles edge cases": False,
                    "Code is well-documented": True
                },
                "suggestions": ["Use a secure password hashing algorithm", "Add input validation"]
            }

        # Collect and aggregate the reviews
        review.collect_reviews()
        feedback = review.aggregate_feedback()

        # Verify the review results
        assert "criteria_results" in feedback
        assert len(feedback["criteria_results"]) == len(acceptance_criteria)
        assert feedback["criteria_results"]["Code follows security best practices"] == False
        assert feedback["criteria_results"]["Function handles edge cases"] == False
        assert feedback["criteria_results"]["Code is well-documented"] == True
        assert feedback["all_criteria_passed"] == False

        # Finalize the review
        final_result = review.finalize(approved=False)
        assert final_result["status"] == "rejected"
        assert final_result["reasons"] == ["Code follows security best practices: Failed", "Function handles edge cases: Failed"]

    def test_peer_review_with_revision_cycle(self, mock_agent_with_expertise):
        """Test the peer review process with a revision cycle."""
        team = WSDETeam()

        # Create agents
        author_agent = mock_agent_with_expertise("AuthorAgent", ["python", "coding"])
        reviewer1 = mock_agent_with_expertise("ReviewerAgent1", ["testing", "quality"])
        reviewer2 = mock_agent_with_expertise("ReviewerAgent2", ["security", "best_practices"])

        # Add agents to the team
        team.add_agent(author_agent)
        team.add_agent(reviewer1)
        team.add_agent(reviewer2)

        # Create a work product
        work_product = {
            "code": "def authenticate(username, password):\n    return username == 'admin' and password == 'password'",
            "description": "Simple authentication function"
        }

        # Request peer review
        review = team.request_peer_review(
            work_product=work_product,
            author=author_agent,
            reviewer_agents=[reviewer1, reviewer2]
        )

        # Mock the initial review process
        for reviewer in review.reviewers:
            # Simulate reviewer providing feedback
            review.reviews[reviewer.name] = {
                "overall_feedback": "The code needs improvement",
                "suggestions": ["Use a secure password hashing algorithm", "Add input validation"],
                "approved": False
            }

        # Collect reviews and request revision
        review.collect_reviews()
        review.request_revision()
        assert review.status == "revision_requested"

        # Create a revised work product
        revised_work = {
            "code": """def authenticate(username, password):
    # Validate inputs
    if not username or not password:
        return False

    # In a real system, this would use a secure password hashing algorithm
    # and compare against stored hashed passwords
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return username == 'admin' and hashed_password == '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
    """,
            "description": "Improved authentication function with input validation and hashing"
        }

        # Submit the revision
        new_review = review.submit_revision(revised_work)
        assert new_review.previous_review == review
        assert new_review.work_product == revised_work

        # Mock the review process for the revised work
        for reviewer in new_review.reviewers:
            # Simulate reviewer approving the revised work
            new_review.reviews[reviewer.name] = {
                "overall_feedback": "The code is now acceptable",
                "suggestions": [],
                "approved": True
            }

        # Collect reviews and finalize
        new_review.collect_reviews()
        final_result = new_review.finalize(approved=True)
        assert final_result["status"] == "approved"
        assert final_result["previous_review_id"] == review.review_id

    def test_peer_review_with_dialectical_analysis(self, mock_agent_with_expertise):
        """Test the peer review process with dialectical analysis."""
        team = WSDETeam()

        # Create agents including a critic
        author_agent = mock_agent_with_expertise("AuthorAgent", ["python", "coding"])
        critic_agent = mock_agent_with_expertise(
            "CriticAgent", ["dialectical_reasoning", "critique"]
        )

        # Add agents to the team
        team.add_agent(author_agent)
        team.add_agent(critic_agent)

        # Create a work product
        work_product = {
            "code": "def authenticate(username, password):\n    return username == 'admin' and password == 'password'",
            "description": "Simple authentication function"
        }

        # Request peer review with the critic agent
        review = team.request_peer_review(
            work_product=work_product,
            author=author_agent,
            reviewer_agents=[critic_agent]
        )

        # Mock the critic's dialectical analysis
        dialectical_analysis = {
            "thesis": {
                "strengths": ["Simple and easy to understand", "Functional for basic use cases"],
                "key_points": ["Direct string comparison for authentication"]
            },
            "antithesis": {
                "weaknesses": [
                    "Security vulnerability: Hardcoded credentials",
                    "No input validation",
                    "No error handling",
                    "No password hashing"
                ],
                "challenges": ["Insecure for production use", "Vulnerable to timing attacks"]
            },
            "synthesis": {
                "improvements": [
                    "Use secure password hashing",
                    "Add input validation",
                    "Implement proper error handling",
                    "Use environment variables or a secure configuration for credentials"
                ],
                "improved_solution": """def authenticate(username, password):
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
            }
        }

        # Set the critic's review with dialectical analysis
        review.reviews[critic_agent.name] = {
            "overall_feedback": "The code needs significant improvement for security",
            "dialectical_analysis": dialectical_analysis,
            "approved": False
        }

        # Collect reviews and aggregate feedback
        review.collect_reviews()
        feedback = review.aggregate_feedback()

        # Verify the dialectical analysis is included in the feedback
        assert "dialectical_analysis" in feedback
        assert "thesis" in feedback["dialectical_analysis"]
        assert "antithesis" in feedback["dialectical_analysis"]
        assert "synthesis" in feedback["dialectical_analysis"]

        # Verify the synthesis contains improvements
        assert "improvements" in feedback["dialectical_analysis"]["synthesis"]
        assert len(feedback["dialectical_analysis"]["synthesis"]["improvements"]) > 0

        # Verify the improved solution is provided
        assert "improved_solution" in feedback["dialectical_analysis"]["synthesis"]
        assert "hashlib" in feedback["dialectical_analysis"]["synthesis"]["improved_solution"]

    def test_contextdriven_leadership(self, mock_agent_with_expertise):
        """Test context-driven leadership in the WSDE team."""
        team = WSDETeam()

        # Create agents with different expertise
        python_agent = mock_agent_with_expertise("PythonAgent", ["python", "backend"])
        js_agent = mock_agent_with_expertise("JSAgent", ["javascript", "frontend"])
        security_agent = mock_agent_with_expertise("SecurityAgent", ["security", "authentication"])
        design_agent = mock_agent_with_expertise("DesignAgent", ["design", "ui", "ux"])
        doc_agent = mock_agent_with_expertise("DocAgent", ["documentation", "technical_writing"])

        # Add agents to the team
        team.add_agent(python_agent)
        team.add_agent(js_agent)
        team.add_agent(security_agent)
        team.add_agent(design_agent)
        team.add_agent(doc_agent)

        # Test context-driven leadership for a documentation task
        doc_task = {
            "type": "documentation_task",
            "description": "Write API documentation",
            "domain": "documentation",
            "requirements": ["Clear examples", "Complete coverage"]
        }

        # Select primus based on expertise for the documentation task
        team.select_primus_by_expertise(doc_task)
        assert team.get_primus() == doc_agent

        # Test that the primus has the correct role
        assert doc_agent.current_role == "Primus"

        # Verify other roles are assigned appropriately
        roles = [agent.current_role for agent in team.agents]
        assert "Worker" in roles
        assert "Supervisor" in roles
        assert "Designer" in roles
        assert "Evaluator" in roles

    def test_dialectical_reasoning_with_external_knowledge(
        self, mock_agent_with_expertise
    ):
        """Test the dialectical reasoning process with external knowledge integration."""
        team = WSDETeam()

        # Create agents including a critic
        code_agent = mock_agent_with_expertise("CodeAgent", ["python", "coding"])
        security_agent = mock_agent_with_expertise(
            "SecurityAgent", ["security", "authentication"]
        )
        critic_agent = mock_agent_with_expertise(
            "CriticAgent", ["dialectical_reasoning", "critique"]
        )

        # Create a task
        task = {
            "type": "implementation_task",
            "description": "Implement a secure user authentication system with multi-factor authentication",
        }

        # Create a proposed solution (thesis)
        thesis = {
            "agent": "CodeAgent",
            "content": "Implement authentication using username/password with JWT tokens",
            "code": """
def authenticate(username, password):
    if username == 'admin' and password == 'password':
        token = generate_jwt_token(username)
        return token
    return None

def generate_jwt_token(username):
    # Generate a JWT token
    return "jwt_token_placeholder"
            """,
        }

        # Add the thesis to the team
        team.add_solution(task, thesis)

        # Create external knowledge sources
        external_knowledge = {
            "security_best_practices": {
                "authentication": [
                    "Use multi-factor authentication for sensitive operations",
                    "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                    "Implement rate limiting to prevent brute force attacks",
                    "Use HTTPS for all authentication requests",
                    "Set secure and HttpOnly flags on authentication cookies",
                ],
                "data_protection": [
                    "Encrypt sensitive data at rest and in transit",
                    "Implement proper access controls",
                    "Follow the principle of least privilege",
                    "Regularly audit access to sensitive data",
                    "Have a data breach response plan",
                ],
            },
            "industry_standards": {
                "OWASP": [
                    "OWASP Top 10 Web Application Security Risks",
                    "OWASP Application Security Verification Standard (ASVS)",
                    "OWASP Secure Coding Practices",
                ],
                "ISO": [
                    "ISO/IEC 27001 - Information security management",
                    "ISO/IEC 27002 - Code of practice for information security controls",
                ],
                "NIST": [
                    "NIST Special Publication 800-53 - Security and Privacy Controls",
                    "NIST Cybersecurity Framework",
                ],
            },
            "compliance_requirements": {
                "GDPR": [
                    "Obtain explicit consent for data collection",
                    "Provide mechanisms for users to access, modify, and delete their data",
                    "Report data breaches within 72 hours",
                    "Conduct Data Protection Impact Assessments (DPIA)",
                ],
                "HIPAA": [
                    "Implement technical safeguards for PHI",
                    "Conduct regular risk assessments",
                    "Maintain audit trails of PHI access",
                    "Have Business Associate Agreements (BAA) in place",
                ],
                "PCI-DSS": [
                    "Maintain a secure network and systems",
                    "Protect cardholder data",
                    "Implement strong access control measures",
                    "Regularly test security systems and processes",
                ],
            },
        }

        # Apply dialectical reasoning with external knowledge
        dialectical_result = team.apply_enhanced_dialectical_reasoning_with_knowledge(
            task, critic_agent, external_knowledge
        )

        # Verify that the dialectical result contains all expected components
        assert "thesis" in dialectical_result
        assert "antithesis" in dialectical_result
        assert "synthesis" in dialectical_result
        assert "evaluation" in dialectical_result
        assert "external_knowledge" in dialectical_result

        # Verify that external knowledge is incorporated
        assert "relevant_sources" in dialectical_result["external_knowledge"]
        assert len(dialectical_result["external_knowledge"]["relevant_sources"]) > 0

        # Verify that the antithesis references industry best practices
        assert "industry_references" in dialectical_result["antithesis"]
        assert len(dialectical_result["antithesis"]["industry_references"]) > 0

        # Verify that the synthesis aligns with external standards
        assert "standards_alignment" in dialectical_result["synthesis"]
        assert len(dialectical_result["synthesis"]["standards_alignment"]) > 0

        # Verify that the evaluation considers compliance
        assert "compliance_assessment" in dialectical_result["evaluation"]
        assert len(dialectical_result["evaluation"]["compliance_assessment"]) > 0

        # Verify that the synthesis improves upon the thesis
        assert dialectical_result["synthesis"]["is_improvement"]
        assert "improved_solution" in dialectical_result["synthesis"]

    def test_multi_disciplinary_dialectical_reasoning(self, mock_agent_with_expertise):
        """Test the dialectical reasoning process with multiple disciplinary perspectives."""
        team = WSDETeam()

        # Create agents with different disciplinary expertise
        code_agent = mock_agent_with_expertise("CodeAgent", ["python", "coding"])
        security_agent = mock_agent_with_expertise(
            "SecurityAgent", ["security", "authentication"]
        )
        ux_agent = mock_agent_with_expertise(
            "UXAgent", ["user_experience", "interface_design"]
        )
        performance_agent = mock_agent_with_expertise(
            "PerformanceAgent", ["performance", "optimization"]
        )
        accessibility_agent = mock_agent_with_expertise(
            "AccessibilityAgent", ["accessibility", "inclusive_design"]
        )
        critic_agent = mock_agent_with_expertise(
            "CriticAgent", ["dialectical_reasoning", "critique", "synthesis"]
        )

        # Add agents to the team
        team.add_agent(code_agent)
        team.add_agent(security_agent)
        team.add_agent(ux_agent)
        team.add_agent(performance_agent)
        team.add_agent(accessibility_agent)
        team.add_agent(critic_agent)

        # Create a task
        task = {
            "type": "implementation_task",
            "description": "Implement a user authentication system with a focus on security, usability, performance, and accessibility",
        }

        # Create a proposed solution (thesis)
        thesis = {
            "agent": "CodeAgent",
            "content": "Implement authentication using username/password with JWT tokens",
            "code": """
def authenticate(username, password):
    if username == 'admin' and password == 'password':
        token = generate_jwt_token(username)
        return token
    return None

def generate_jwt_token(username):
    # Generate a JWT token
    return "jwt_token_placeholder"
            """,
        }

        # Add the thesis to the team
        team.add_solution(task, thesis)

        # Create disciplinary knowledge sources
        disciplinary_knowledge = {
            "security": {
                "authentication_best_practices": [
                    "Use multi-factor authentication for sensitive operations",
                    "Store passwords using strong, adaptive hashing algorithms (e.g., bcrypt, Argon2)",
                    "Implement rate limiting to prevent brute force attacks",
                    "Use HTTPS for all authentication requests",
                    "Set secure and HttpOnly flags on authentication cookies",
                ]
            },
            "user_experience": {
                "authentication_ux_principles": [
                    "Minimize friction in the authentication process",
                    "Provide clear error messages for failed authentication attempts",
                    "Offer password recovery options",
                    "Remember user preferences where appropriate",
                    "Support single sign-on where possible",
                ]
            },
            "performance": {
                "authentication_performance_considerations": [
                    "Optimize token validation for minimal latency",
                    "Cache frequently used authentication data",
                    "Use asynchronous processing for non-critical authentication tasks",
                    "Implement efficient database queries for user lookup",
                    "Monitor and optimize authentication service response times",
                ]
            },
            "accessibility": {
                "authentication_accessibility_guidelines": [
                    "Ensure all authentication forms are keyboard navigable",
                    "Provide appropriate ARIA labels for authentication form elements",
                    "Support screen readers for error messages and instructions",
                    "Maintain sufficient color contrast for text and interactive elements",
                    "Allow authentication timeout extensions for users who need more time",
                ]
            },
        }

        # Apply multi-disciplinary dialectical reasoning
        dialectical_result = team.apply_multi_disciplinary_dialectical_reasoning(
            task,
            critic_agent,
            disciplinary_knowledge,
            [security_agent, ux_agent, performance_agent, accessibility_agent],
        )

        # Verify that the dialectical result contains all expected components
        assert "thesis" in dialectical_result
        assert "disciplinary_perspectives" in dialectical_result
        assert "synthesis" in dialectical_result
        assert "evaluation" in dialectical_result
        assert "knowledge_sources" in dialectical_result

        # Verify that multiple disciplinary perspectives are incorporated
        assert len(dialectical_result["disciplinary_perspectives"]) >= 4

        # Check for specific disciplinary perspectives
        perspective_disciplines = [
            p["discipline"] for p in dialectical_result["disciplinary_perspectives"]
        ]
        assert "security" in perspective_disciplines
        assert "user_experience" in perspective_disciplines
        assert "performance" in perspective_disciplines
        assert "accessibility" in perspective_disciplines

        # Verify that each perspective contains a critique
        for perspective in dialectical_result["disciplinary_perspectives"]:
            assert "critique" in perspective
            assert len(perspective["critique"]) > 0
            assert "recommendations" in perspective
            assert len(perspective["recommendations"]) > 0

        # Verify that the synthesis integrates multiple perspectives
        assert "integrated_perspectives" in dialectical_result["synthesis"]
        assert len(dialectical_result["synthesis"]["integrated_perspectives"]) >= 4

        # Verify that the synthesis addresses conflicts between perspectives
        assert "perspective_conflicts" in dialectical_result["synthesis"]
        assert "conflict_resolutions" in dialectical_result["synthesis"]

        # Verify that the evaluation assesses the solution from multiple perspectives
        assert "perspective_scores" in dialectical_result["evaluation"]
        assert len(dialectical_result["evaluation"]["perspective_scores"]) >= 4

        # Verify that the synthesis improves upon the thesis
        assert dialectical_result["synthesis"]["is_improvement"]
        assert "improved_solution" in dialectical_result["synthesis"]

    # New tests appended

    def test_assign_roles_for_phase_varied_contexts(self, mock_agent_with_expertise):
        team = WSDETeam()
        expand_agent = mock_agent_with_expertise("Expand", ["expand"])
        diff_agent = mock_agent_with_expertise("Diff", ["differentiate"])
        refine_agent = mock_agent_with_expertise("Refine", ["refine"])
        doc_agent = mock_agent_with_expertise("Doc", ["documentation"])
        team.add_agents([expand_agent, diff_agent, refine_agent, doc_agent])

        generic = {"description": "demo"}
        team.assign_roles_for_phase(Phase.EXPAND, generic)
        assert team.get_primus() == expand_agent

        team.assign_roles_for_phase(Phase.DIFFERENTIATE, generic)
        assert team.get_primus() == diff_agent

        team.assign_roles_for_phase(Phase.REFINE, generic)
        assert team.get_primus() == refine_agent

        doc_task = {"type": "documentation"}
        team.assign_roles_for_phase(Phase.RETROSPECT, doc_task)
        assert team.get_primus() == doc_agent

    def test_vote_on_critical_decision_majority_path(self, mock_agent):
        team = WSDETeam()
        a1 = mock_agent
        a1.name = "a1"
        a2 = MagicMock(spec=BaseAgent)
        a2.name = "a2"
        a3 = MagicMock(spec=BaseAgent)
        a3.name = "a3"
        for a in [a1, a2, a3]:
            a.process = MagicMock()
            team.add_agent(a)
        a1.process.return_value = {"vote": "o1"}
        a2.process.return_value = {"vote": "o1"}
        a3.process.return_value = {"vote": "o2"}
        task = {
            "type": "critical_decision",
            "is_critical": True,
            "options": [{"id": "o1"}, {"id": "o2"}],
        }
        result = team.vote_on_critical_decision(task)
        assert result["result"]["winner"] == "o1"
        assert result["result"]["method"] == "majority_vote"

    def test_vote_on_critical_decision_weighted_path(self, mock_agent_with_expertise):
        team = WSDETeam()
        expert = mock_agent_with_expertise("expert", ["security"])
        expert.config = MagicMock()
        expert.config.name = "expert"
        expert.config.parameters = {
            "expertise": ["security"],
            "expertise_level": "expert",
        }
        intermediate = mock_agent_with_expertise("inter", ["security"])
        intermediate.config = MagicMock()
        intermediate.config.name = "inter"
        intermediate.config.parameters = {
            "expertise": ["security"],
            "expertise_level": "intermediate",
        }
        novice = mock_agent_with_expertise("novice", ["python"])
        novice.config = MagicMock()
        novice.config.name = "novice"
        novice.config.parameters = {
            "expertise": ["python"],
            "expertise_level": "novice",
        }
        for a in [expert, intermediate, novice]:
            a.process = MagicMock()
            team.add_agent(a)
        expert.process.return_value = {"vote": "b"}
        intermediate.process.return_value = {"vote": "a"}
        novice.process.return_value = {"vote": "a"}
        task = {
            "type": "critical_decision",
            "domain": "security",
            "is_critical": True,
            "options": [{"id": "a"}, {"id": "b"}],
        }
        result = team.vote_on_critical_decision(task)
        assert result["result"]["method"] == "weighted_vote"
        assert result["result"]["winner"] == "b"
        assert result["vote_weights"]["expert"] > result["vote_weights"]["inter"]

    def test_documentation_task_selects_doc_agent_and_updates_role_assignments(
        self, mock_agent_with_expertise
    ):
        team = WSDETeam()
        coder = mock_agent_with_expertise("Coder", ["python"])
        coder.has_been_primus = True
        doc_agent = mock_agent_with_expertise("Doc", ["documentation", "markdown"])
        doc_agent.has_been_primus = False
        team.add_agents([coder, doc_agent])

        task = {"type": "documentation", "description": "Write docs"}
        team.select_primus_by_expertise(task)

        assert team.get_primus() is doc_agent
        assert team.role_assignments["primus"] is doc_agent
        assert doc_agent.has_been_primus

    def test_select_primus_fallback_when_no_expertise_matches(
        self, mock_agent_with_expertise
    ):
        team = WSDETeam()
        a1 = mock_agent_with_expertise("A1", ["python"])
        a2 = mock_agent_with_expertise("A2", ["javascript"])
        a3 = mock_agent_with_expertise("A3", ["design"])
        for a in [a1, a2, a3]:
            a.has_been_primus = True
            team.add_agent(a)

        task = {"type": "unknown", "topic": "nothing"}
        team.select_primus_by_expertise(task)

        assert team.get_primus() is a1
        assert team.role_assignments["primus"] is a1

    def test_documentation_expert_becomes_primus(self, mock_agent_with_expertise):
        team = WSDETeam()

        generalist = mock_agent_with_expertise("Generalist", ["python"])
        doc_agent = mock_agent_with_expertise("Doc", ["documentation"])

        team.add_agents([generalist, doc_agent])

        task = {"type": "documentation", "description": "Write docs"}
        team.select_primus_by_expertise(task)

        assert team.get_primus() is doc_agent
