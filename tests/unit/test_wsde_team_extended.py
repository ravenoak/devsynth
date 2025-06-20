
import pytest
from unittest.mock import MagicMock, patch
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.base import BaseAgent

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
        assigned_roles = [agent2.current_role, agent3.current_role, agent4.current_role, agent5.current_role]
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
        python_agent = mock_agent_with_expertise("PythonAgent", ["python", "coding", "backend"])
        js_agent = mock_agent_with_expertise("JSAgent", ["javascript", "frontend", "web"])
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
        critic_agent = mock_agent_with_expertise("CriticAgent", ["dialectical_reasoning", "critique"])

        # Add agents to the team
        team.add_agent(code_agent)
        team.add_agent(test_agent)
        team.add_agent(critic_agent)

        # Create a task
        task = {"type": "implementation_task", "description": "Implement a user authentication system"}

        # Create a proposed solution (thesis)
        thesis = {
            "agent": "CodeAgent",
            "content": "Implement authentication using a simple username/password check",
            "code": "def authenticate(username, password):\n    return username == 'admin' and password == 'password'"
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

    def test_dialectical_reasoning_with_external_knowledge(self, mock_agent_with_expertise):
        """Test the dialectical reasoning process with external knowledge integration."""
        team = WSDETeam()

        # Create agents including a critic
        code_agent = mock_agent_with_expertise("CodeAgent", ["python", "coding"])
        security_agent = mock_agent_with_expertise("SecurityAgent", ["security", "authentication"])
        critic_agent = mock_agent_with_expertise("CriticAgent", ["dialectical_reasoning", "critique"])

        # Add agents to the team
        team.add_agent(code_agent)
        team.add_agent(security_agent)
        team.add_agent(critic_agent)

        # Create a task
        task = {
            "type": "implementation_task", 
            "description": "Implement a secure user authentication system with multi-factor authentication"
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
            """
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
                    "Set secure and HttpOnly flags on authentication cookies"
                ],
                "data_protection": [
                    "Encrypt sensitive data at rest and in transit",
                    "Implement proper access controls",
                    "Follow the principle of least privilege",
                    "Regularly audit access to sensitive data",
                    "Have a data breach response plan"
                ]
            },
            "industry_standards": {
                "OWASP": [
                    "OWASP Top 10 Web Application Security Risks",
                    "OWASP Application Security Verification Standard (ASVS)",
                    "OWASP Secure Coding Practices"
                ],
                "ISO": [
                    "ISO/IEC 27001 - Information security management",
                    "ISO/IEC 27002 - Code of practice for information security controls"
                ],
                "NIST": [
                    "NIST Special Publication 800-53 - Security and Privacy Controls",
                    "NIST Cybersecurity Framework"
                ]
            },
            "compliance_requirements": {
                "GDPR": [
                    "Obtain explicit consent for data collection",
                    "Provide mechanisms for users to access, modify, and delete their data",
                    "Report data breaches within 72 hours",
                    "Conduct Data Protection Impact Assessments (DPIA)"
                ],
                "HIPAA": [
                    "Implement technical safeguards for PHI",
                    "Conduct regular risk assessments",
                    "Maintain audit trails of PHI access",
                    "Have Business Associate Agreements (BAA) in place"
                ],
                "PCI-DSS": [
                    "Maintain a secure network and systems",
                    "Protect cardholder data",
                    "Implement strong access control measures",
                    "Regularly test security systems and processes"
                ]
            }
        }

        # Apply dialectical reasoning with external knowledge
        dialectical_result = team.apply_enhanced_dialectical_reasoning_with_knowledge(
            task, 
            critic_agent,
            external_knowledge
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
        security_agent = mock_agent_with_expertise("SecurityAgent", ["security", "authentication"])
        ux_agent = mock_agent_with_expertise("UXAgent", ["user_experience", "interface_design"])
        performance_agent = mock_agent_with_expertise("PerformanceAgent", ["performance", "optimization"])
        accessibility_agent = mock_agent_with_expertise("AccessibilityAgent", ["accessibility", "inclusive_design"])
        critic_agent = mock_agent_with_expertise("CriticAgent", ["dialectical_reasoning", "critique", "synthesis"])

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
            "description": "Implement a user authentication system with a focus on security, usability, performance, and accessibility"
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
            """
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
                    "Set secure and HttpOnly flags on authentication cookies"
                ]
            },
            "user_experience": {
                "authentication_ux_principles": [
                    "Minimize friction in the authentication process",
                    "Provide clear error messages for failed authentication attempts",
                    "Offer password recovery options",
                    "Remember user preferences where appropriate",
                    "Support single sign-on where possible"
                ]
            },
            "performance": {
                "authentication_performance_considerations": [
                    "Optimize token validation for minimal latency",
                    "Cache frequently used authentication data",
                    "Use asynchronous processing for non-critical authentication tasks",
                    "Implement efficient database queries for user lookup",
                    "Monitor and optimize authentication service response times"
                ]
            },
            "accessibility": {
                "authentication_accessibility_guidelines": [
                    "Ensure all authentication forms are keyboard navigable",
                    "Provide appropriate ARIA labels for authentication form elements",
                    "Support screen readers for error messages and instructions",
                    "Maintain sufficient color contrast for text and interactive elements",
                    "Allow authentication timeout extensions for users who need more time"
                ]
            }
        }

        # Apply multi-disciplinary dialectical reasoning
        dialectical_result = team.apply_multi_disciplinary_dialectical_reasoning(
            task, 
            critic_agent,
            disciplinary_knowledge,
            [security_agent, ux_agent, performance_agent, accessibility_agent]
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
        perspective_disciplines = [p["discipline"] for p in dialectical_result["disciplinary_perspectives"]]
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
