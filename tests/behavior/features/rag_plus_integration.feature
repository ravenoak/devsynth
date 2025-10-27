Feature: RAG+ Integration
    As a DevSynth agent
    I want reasoning-aware retrieval capabilities
    So that I can effectively apply knowledge in complex reasoning tasks

    @fast @dual-corpus
    Scenario: Dual corpus stores knowledge and examples
        Given a RAG+ system with dual corpus architecture
        When initializing the knowledge stores
        Then it should maintain a knowledge corpus for factual information
        And maintain an application examples corpus for procedural guidance
        And index both corpora with appropriate retrieval mechanisms

    @fast @joint-retrieval
    Scenario: Joint retrieval of knowledge and examples
        Given a complex reasoning query requiring both facts and procedures
        When performing RAG+ retrieval
        Then it should retrieve relevant factual knowledge
        And retrieve corresponding application examples
        And correlate knowledge with procedural guidance
        And present integrated knowledge-example pairs

    @medium @query-rewriting
    Scenario: Query rewriting for better retrieval
        Given a vague or complex user query
        When preprocessing for RAG+ retrieval
        Then the system should rewrite the query for better semantic matching
        And decompose complex queries into focused sub-queries
        And optimize retrieval performance through query enhancement

    @fast @domain-specialization
    Scenario: Domain-specific reasoning enhancement
        Given queries in specialized domains like mathematics or law
        When applying domain-specific RAG+ retrieval
        Then it should retrieve domain-appropriate knowledge
        And provide specialized application examples
        And enhance reasoning performance in the target domain

    @medium @quality-assurance
    Scenario: Retrieval quality validation
        Given retrieved knowledge and example pairs
        When validating retrieval quality
        Then it should check factual accuracy of knowledge
        And verify relevance of application examples
        And detect potential retrieval biases
        And ensure high-quality knowledge-example alignment

    @fast @performance-optimization
    Scenario: Retrieval performance optimization
        Given multiple retrieval requests
        When optimizing for performance
        Then it should cache frequently accessed pairs
        And batch process related queries
        And support incremental indexing of new examples
        And maintain retrieval latency within acceptable bounds

    @medium @memory-integration
    Scenario: Integration with hybrid memory system
        Given DevSynth's hybrid memory architecture
        When integrating RAG+ capabilities
        Then it should extend vector stores with dual corpus indexing
        And leverage graph stores for example relationships
        And use structured stores for metadata tracking
        And maintain consistency across memory types

    @fast @agent-workflow
    Scenario: RAG+ in agent workflows
        Given agents using EDRR and WSDE frameworks
        When incorporating RAG+ retrieval
        Then it should provide reasoning examples during differentiation
        And support application-aware refinement
        And enhance collaborative agent decision-making
        And improve overall task completion quality
