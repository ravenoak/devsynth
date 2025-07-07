# Citation Key: AgentNet-2504.00587v2

---

## A GENT N ET : D ECENTRALIZED E VOLUTIONARY C OORDINATION FOR LLM- BASED M ULTI -A GENT S YSTEMS

**Yingxuan Yang** **[1]** **, Huacan Chai** _[∗]_ **[1]** _[∗]_ **, Shuai Shao** **[1]** **,**
**Yuanyi Song** [1], **Siyuan Qi** [1], **Renting Rui** [1], **Weinan Zhang** [1,2] _[†]_

1 Shanghai Jiao Tong University, 2 SII
{zoeyyx, fatcat, wnzhang}@sjtu.edu.cn

**A** **BSTRACT**

The rapid advancement of Large Language Models (LLMs) has catalyzed the development of multiagent systems, where multiple LLM-based agents collaborate to solve complex tasks. However,
existing systems predominantly rely on centralized coordination, which introduces scalability bottlenecks, limits adaptability, and creates single points of failure. Additionally, concerns over privacy and
proprietary knowledge sharing hinder cross-organizational collaboration, leading to siloed expertise.
To address these challenges, we propose **AgentNet**, a decentralized, Retrieval-Augmented Generation
(RAG)-based framework that enables LLM-based agents to autonomously evolve their capabilities
and collaborate efficiently in a Directed Acyclic Graph (DAG)-structured network. Unlike traditional multi-agent systems that depend on static role assignments or centralized control, AgentNet
allows agents to specialize dynamically, adjust their connectivity, and route tasks without relying on
predefined workflows. AgentNet’s core design is built upon several key innovations: (1) Fully Decentralized Paradigm: Removing the central orchestrator, allowing agents to coordinate and specialize
autonomously, fostering fault tolerance and emergent collective intelligence. (2) Dynamically Evolving Graph Topology: Real-time adaptation of agent connections based on task demands, ensuring
scalability and resilience. (3) Adaptive Learning for Expertise Refinement: A retrieval-based memory
system that enables agents to continuously update and refine their specialized skills. By eliminating
centralized control, AgentNet enhances fault tolerance, promotes scalable specialization, and enables
privacy-preserving collaboration across organizations. Through decentralized coordination and minimal data exchange, agents can leverage diverse knowledge sources while safeguarding sensitive
information. Experimental results demonstrate that AgentNet outperforms traditional centralized
multi-agent systems, significantly improving efficiency, adaptability, and scalability in dynamic
environments, making it a promising foundation for next-generation autonomous, privacy-respecting
multi-agent ecosystems.

_**Keywords**_ LLM-based Multi-Agent Systems (MAS) _·_ Decentralized MAS _·_ RAG _·_ Natural Evolution _·_ DAG

**1** **Introduction**

Recently, large language models (LLMs) have demonstrated remarkable capabilities in various domains, ranging from
basic text understanding to complex reasoning and multimodal integration [OpenAI et al., 2024, Touvron et al., 2023,
Yang et al., 2025]. Consequently, LLM-based agents have exhibited exceptional performance in numerous tasks,
including scientific discovery [Gottweis et al., 2025], automated reasoning [Putta et al., 2024], and website operations

[Zhou et al., 2024]. However, due to the lack of collective intelligence and collaboration, LLM-based Single Agents
struggle to address the complex challenges encountered in the real world. By leveraging collective intelligence through
parallel decision-making or workflow collaboration, LLM-based Multi-Agent Systems (MAS) have emerged as a
promising framework for tackling complex real-world problems [Guo et al., 2024, Sun et al., 2024, Yang et al., 2024].

_∗_ These authors contributed equally to this work.

_†_ Weinan Zhang is the corresponding author.

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-1-0.png)

Figure 1: The illustration contrasts Pre-Defined Multi-Agents (hierarchical, static, with centralized control and single point of failure)
against Self-Evolving Agents/AgentNet (adaptive, decentralized, and fault-tolerant with dynamic expertise development).

However, most MAS following the workflow collaboration paradigm rely heavily on a centralized controller or a static,
predefined workflow to allocate tasks among agents with fixed roles [Chen et al., 2023a, Hong et al., 2024, Wu et al.,
2023, Wang et al., 2024, Ye et al., 2025]. While such designs simplify orchestration, they also introduce inherent
constraints—including limited scalability, a single point of failure, and challenges to cross-organizational collaboration
due to privacy and proprietary knowledge concerns.

A more critical drawback arises from the inability of these systems to adapt to real-time fluctuations in agent performance or rapidly changing task requirements. Relying on a central controller inflates deployment complexity and
restricts dynamic role reassignment, rendering the system vulnerable when the controller fails or becomes overloaded.
Furthermore, rigid role definitions prevent agents from flexibly leveraging their full expertise in dynamic environments,
ultimately undermining both efficiency and scalability. Taken together, these limitations highlight the need for more
decentralized, fault-tolerant approaches that support dynamic task allocation, enhance adaptability, and safeguard
privacy across organizational boundaries.

Beyond the scalability and failure-tolerance issues previously discussed, centralized architectures become even more
problematic when organizations attempt to collaborate at scale [Yang et al., 2024, Shi et al., 2025]. Each institution—be
it an enterprise, research lab, or government agency—typically holds proprietary expertise, sensitive data, or both.
In a centralized setup, concerns over data ownership, privacy regulations, and inconsistent governance often create
barriers that prevent free exchange of knowledge. As a result, LLM-based agents contributed by multiple organizations
remain siloed, unable to fully capitalize on each other’s specialized capabilities or datasets. This fragmentation not
only hampers collective intelligence but also highlights the urgency of developing secure, decentralized collaboration
mechanisms. By enabling each participant to maintain and share only the minimal necessary information, these
mechanisms address data confidentiality requirements while still allowing for a richer, more collaborative multi-agent
ecosystem.

To address these challenges in multi-agent systems, we propose AgentNet, a novel framework designed to foster
adaptive agent evolution, optimize task coordination, and preserve privacy. By eliminating the reliance on a central
orchestrator, AgentNet enables agents to dynamically reconfigure their connections and redistribute tasks, forming a
self-organizing, fault-tolerant architecture. Within this architecture, tasks are efficiently routed via a Directed Acyclic
Graph (DAG) [Kahn, 1962, Ahuja et al., 1993], which supports flexible collaboration and prevents cyclic dependencies.

Unlike traditional MAS frameworks that fix each agent’s role, AgentNet incorporates a retrieval-based RAG [Lewis et al.,
2020, Gao et al., 2023, Zhou et al., 2024] memory mechanism to refine agent expertise over time. Each agent maintains
a limited-capacity pool of successful task trajectories; when a new task arises, it retrieves the most relevant trajectories
through few-shot learning, thus improving decision-making. To prevent memory overflow, agents autonomously prune
less pertinent trajectories, ensuring the retention of valuable knowledge. This dynamic specialization strategy not only
streamlines task allocation and agent adaptation but also supports a highly scalable and privacy-respecting environment
for multi-agent collaboration.

2

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

AgentNet’s core design is built upon several key innovations:

    - **Fully Decentralized Paradigm** : By removing the need for a central orchestrator, AgentNet fosters emergent
collective intelligence. Decision-making authority is distributed across all agents, thereby eliminating single
points of failure and allowing each agent to coordinate, delegate, and specialize as conditions evolve. This
approach leads to a self-organizing and fault-tolerant architecture that can rapidly respond to new tasks and
unforeseen challenges. This decentralized setup also encourages emergent collective intelligence—in other
words, agents can collectively discover and refine optimal strategies rather than waiting for instructions from a
central controller.

    - **Dynamically Evolving Graph Topology** : AgentNet employs a network structure in which both nodes (agents)
and edges (agent-to-agent connections) adapt in real time based on task demands and agent performance. Rather
than relying on fixed workflows, the system continuously reconfigures its topology to optimize information
flow and task distribution, ensuring scalability and resilience in complex, changing environments.

    - **Adaptive Learning Mechanism for Expertise Refinement** : AgentNet’s third innovation is its retrievalbased memory system, enabling agents to capture and update knowledge from successful task trajectories.
This mechanism continuously refines each agent’s specialized skills without altering the network’s topology,
allowing agents to avoid over-reliance on outdated information and sustain high performance in dynamic
scenarios.

Moreover, each of these three innovations inherently enhances data privacy. By eliminating a central orchestrator,
every agent stores and processes knowledge locally, sharing only minimal task-relevant metadata. The dynamic
graph topology further confines data flow to necessary agent-to-agent interactions, reducing the exposure of sensitive
information. Meanwhile, the retrieval-based memory mechanism restricts how much and how long data is retained,
pruning outdated trajectories so that only high-value knowledge persists. Together, these design choices safeguard
privacy and intellectual property, particularly crucial for cross-organizational collaborations.

Our experimental evaluation shows that AgentNet significantly outperforms traditional LLM-based multi-agent frameworks in dynamic environments, demonstrating improved task efficiency, specialization stability, and adaptive learning
speed. These results highlight the effectiveness of decentralized evolutionary coordination in large-scale AI ecosystems.

**2** **Related Work**

**2.1** **LLM-based Multi-Agent Systems**

The development of LLM-based multi-agent systems (LaMAS) [Yang et al., 2024] has advanced rapidly in recent years.
Early frameworks, such as AutoGen [Wu et al., 2023] and MetaGPT [Hong et al., 2024], made significant strides in
establishing foundational architectures for orchestrating multiple LLM agents through structured workflows. AutoGen
provided a flexible framework for defining agent interactions, while MetaGPT incorporated software development principles to enhance collaboration. These centralized frameworks proved effective for managing multi-agent interactions.
However, they also faced inherent challenges, including limited scalability, single points of failure, and difficulty in
dynamically adapting to evolving tasks or incorporating new expertise.

In response to these limitations, more recent frameworks such as AgentScope [Gao et al., 2024] and MegaAgent

[Wang et al., 2024] have focused on improving robustness and scalability. AgentScope introduced modular design
patterns to enhance system reliability, while MegaAgent employed hierarchical structures to scale agent interactions.
Although these frameworks offer improvements, they still operate under centralized control paradigms, with a master
agent delegating tasks, which continues to lead to scalability bottlenecks and single points of failure. Moreover,
existing LaMAS implementations predominantly utilize single-source LLMs, lacking the integration of heterogeneous
models. Their workflows are typically static, unable to dynamically allocate resources based on task complexity, further
constraining adaptability.

In contrast, AgentNet introduces a novel decentralized approach, addressing these challenges by enabling agents to
autonomously refine their expertise and dynamically allocate resources. AgentNet supports scalable, fault-tolerant
collaboration without reliance on a central orchestrator, overcoming the limitations of centralized frameworks.

**2.2** **Evolutionary Agent Systems**

Inspired by natural evolution, recent researchers have explored evolutionary approaches to automate and optimize agent
behaviors and workflows in LaMAS. Existing efforts can be broadly categorized into the following areas:

3

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-3-0.png)

Figure 2: Illutration of AgentNet. Initially, agents are fully connected and equipped with executors and routers. The system eliminates
the need for a central controller, using a DAG for dynamic task routing and agents leveraging RAG pools and few-shot learning. In
the evolved phase, the network adapts with agents developing private trajectories and diversified abilities, ensuring scalability, fault
tolerance, and continuous evolution of expertise..

    - **Prompt Evolution and Optimization** – Techniques such as PromptBreeder [Fernando et al., 2023], DsPy

[Khattab et al., 2023] and AgentPrune [Zhang et al., 2024a] apply evolutionary algorithms to iteratively refine
prompt generation, improving task performance through better input design.

    - **Inter-Agent Topology Optimization** – Systems like GPTSwarm [Zhuge et al., 2024], DyLAN [Liu et al.,
2024], and G-Designer [Zhang et al., 2024b] focus on evolving the structural organization of agent interactions.
These works aim to optimize communication patterns, task allocation, and collaboration efficiency within
multi-agent networks.

    - **Agent Role and Persona Specialization** – Frameworks such as AgentVerse and MorphAgent [Chen et al.,
2023b, Lu et al., 2024] refine agent roles and profiles, enabling more effective specialization and coordination
among agents in complex tasks.

While these evolutionary approaches have shown promise, they primarily focus on individual agent adaptation rather
than collective coordination. Additionally, they still tend to operate within centralized control structures, which limits
their scalability and dynamic adaptability. Recent frameworks like AgentSquare [Shang et al., 2024] and AFlow

[Zhang et al., 2024c] have begun to formalize automated design processes for agentic systems, improving system-level
orchestration and workflow automation. Another key direction is self-adaptive agent architectures, where agents adjust
their strategies in real-time based on feedback and accumulated experience. For example, EvoMAC [Hu et al., 2024]
combines reinforcement learning with evolutionary algorithms to optimize agent decision-making and policy updates.

However, these approaches are often limited to single-agent adaptation and lack mechanisms for decentralized specialization and coordination across large-scale agent collectives. While EvoMAC and other systems focus on optimizing
individual agents, they are not designed for scalable, multi-agent, decentralized collaboration. In contrast, AgentNet
integrates evolutionary learning with decentralized control, enabling heterogeneous agents to dynamically evolve their
roles, adapt their strategies in real-time, and collaborate flexibly across a large-scale multi-agent system. This integration
of evolutionary learning with decentralized control makes AgentNet a more suitable framework for real-time, adaptive,
and scalable multi-agent collaboration.

**3** **Methodology**

**3.1** **Overview of AgentNet Architecture**

Unlike traditional MAS frameworks with fixed agent roles and rigid workflows using central coordinators, AgentNet
creates a privacy-preserving, collective intelligence multi-agent system with high scalability and failure-tolerance by
leveraging an innovative framework, consisting of a fully decentralized network architecture, a dynamic task allocation
mechanism, and an adaptive agent learning method.

We begin with a brief introduction of AgentNet, including notation and basic architectures of agents employed.

4

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

Formally, we define AgentNet as a tuple _G_ = ( _**A**_ _,_ _**E**_ ), where _**A**_ = _{a_ 1 _, a_ 2 _, ..., a_ _n_ _}_ represents the set of autonomous
agents, _**C**_ = _{c_ 1 _, c_ 2 _, ..., c_ _n_ _}_ represents each agent’s ability, and _**E**_ _⊆_ _**A**_ _×_ _**A**_ represents the communication connections
between agents, specifically _e_ _i,j_ _∈_ _**E**_ referring to a unidirectional connection from Agent _a_ _i_ to Agent _a_ _j_ .

For each agent _a_ _i_ _∈_ _**A**_ contains two key components. _rou_ _i_ is an agent router, responsible for analyzing received
routing queries and making routing decisions. _exe_ _i_ is an agent executor, responsible for responding to executing queries
through operations and tools.

The two components mentioned above are underpinned by a substantial LLM that leverages its extensive knowledge and
understanding to solve specific problems. Furthermore, both _rou_ _i_ and _exe_ _i_ in _a_ _i_ maintain fixed-size memory modules
_M_ _i_ _[rou]_ and _M_ _i_ _[exe]_, respectively, providing _a_ _i_ with powerful adaptive evolutionary capabilities by storing and utilizing
the agent’s experiences through the RAG mechanism.

For optimization, AgentNet will be given a series of tasks denoted as _**T**_ = _{t_ 1 _, t_ 2 _, ..., t_ _M_ _}_ to resolve, along with an
evaluation function _Eval_ ( _·_ ) . The optimization goal of AgentNet is to maximize the evaluated score by _Eval_ ( _·_ ) for the
solution output by AgentNet, specifically optimizing _**A**_ and _**E**_, as the following formula:

_G_ _[∗]_ = ( _**A**_ _**[∗]**_ _,_ _**E**_ _**[∗]**_ ) = arg max _Eval_ ( _G,_ _**T**_ ) _._ (1)
_**A**_ _,_ _**E**_

The innovation of AgentNet emerges from the synergistic integration of three key mechanisms: (1) AgentNet realized
a fully decentralized network architecture by distributing decision-making authority across all agents, leading to a
high failure tolerance and privacy-preserving MAS. (2) By using a dynamic task allocation mechanism, AgentNet
can optimize workload distribution based on agent capabilities and the current system state flexibly. (3) The adaptive
learning in AgentNet can achieve continuous specialization of agents, making the whole MAS more scalable and
adaptive. Therefore, we can create a self-organizing system capable of handling complex tasks while preserving privacy
and adapting to changing environments.

**3.2** **Decentralized Network Topology**

As illustrated in Figure 3, AgentNet employs a dual-role
design. Each agent _a_ _i_ is equipped with a router _rou_ _i_ to
facilitate routing decisions and an executor _exe_ _i_ to execute
specific tasks. We will introduce details of the router and
executor in the following sections. In essence, the router
within each agent endows AgentNet with a fully decentralized network structure because the routing decisions are
made independently by each agent, without relying on a
central authority or coordinator.

This contrasts with traditional LLM based Multi-Agent Systems that typically depend on a centralized controller to
manage the coordination and allocation of tasks. Each agent
in AgentNet autonomously determines how to route tasks
to other agents based on its local knowledge and the task
requirements, ensuring that decision-making is distributed
across the network and that there is no single point of con
![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-4-0.png)
trol, thus achieving full decentralization. Figure 3: Dual-role agent architecture.

Mathematically, we represent the architecture of AgentNet as _G_ _m_ = ( _**A**_ _**m**_ _,_ _**E**_ _**m**_ ) when given the _m_ +1 -th task _t_ _m_ +1 after
completing task _t_ _m_, where _**A**_ _**m**_ = _{a_ _[m]_ 1 _[, a]_ 2 _[m]_ _[, ..., a]_ _[m]_ _n_ _[}]_ [ represents the states of agents after task] _[ t]_ _[m]_ [and] _**[ E]**_ _[m]_ _[⊆]_ _**[A]**_ _**[m]**_ _[×]_ _**[A]**_ _**[m]**_
represents the set of directed edges between agents and each edge _e_ _[m]_ _i,j_ [means a directed edge from] _[ a]_ _[m]_ _i_ [to] _[ a]_ _[m]_ _j_ [. A weight]
matrix _w_ _m_ will be maintained throughout all the tasks before _t_ _m_ +1 to weight the connection between agents, namely
_w_ _m_ ( _i, j_ ). After completing _t_ _m_ +1, _w_ _m_ +1 can be updated using the following formula from _w_ _m_ :

_w_ _m_ +1 ( _i, j_ ) = _α · w_ _m_ ( _i, j_ ) + (1 _−_ _α_ ) _· S_ ( _a_ _[m]_ _i_ [+1] _, a_ _[m]_ _j_ [+1] _, t_ _m_ +1 ) _,_ (2)

where _α_ _∈_ [0 _,_ 1] is a decay factor that balances historical performance with recent interactions, and
_S_ ( _a_ _[m]_ _i_ [+1] _, a_ _[m]_ _j_ [+1] _, t_ _m_ +1 ) is a success metric for task _t_ _m_ +1 routed from agent _a_ _[m]_ _i_ [+1] to _a_ _[m]_ _j_ [+1] . This adaptive weighting mechanism ensures that the network continuously refines its structure based on operational experience.

5

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

**Algorithm 1** AgentNet System

**Require:** Task set _T_ = _{t_ 1 _, t_ 2 _, . . ., t_ _M_ _}_
**Ensure:** Optimized network _G_ _[∗]_ = ( _**A**_ _[∗]_ _,_ _**E**_ _[∗]_ )

1: Initialize _**A**_ = _{a_ 1 _, a_ 2 _, . . ., a_ _n_ _}_, _**E**_, _**C**_ = _{c_ 1 _, c_ 2 _, . . ., c_ _n_ _}_, _w_ 0, _M_ _i_ _[rou]_ and _M_ _i_ _[exe]_ _∀a_ _i_ _∈_ _**A**_
2: **for** each task _t_ _m_ +1 _∈_ _T_ **do**
3: // 1. Task allocation and processing
4: _c_ _t_ _m_ +1 _←_ Φ( _o_ _t_ _m_ +1 ), _a_ _curr_ _←_ arg max _a_ _i_ _∈A_ _m_ sim( _c_ _t_ _m_ +1 _, c_ _[m]_ _i_ [)]
5: _task_ _ _state ←_ ( _o_ _t_ _m_ +1 _, ∅, p_ _t_ _m_ +1 ), _visited ←∅_, _finished ←_ _false_
6: **while** not _finished_ and _a_ _curr_ _/∈_ _visited_ **do**
7: _visited ←_ _visited ∪{a_ _curr_ _}_
8: _fragments_ _[rou]_ _←_ Select( _M_ _curr_ _[rou]_ _[, t]_ _[m]_ [+1] _[, k]_ [)]
9: _action ←F_ _act_ ( _o_ _t_ _m_ +1 _, c_ _t_ _m_ +1 _, F_ _reason_ ( _o_ _t_ _m_ +1 _, c_ _t_ _m_ +1 _, fragments_ _[rou]_ ) _, fragments_ _[rou]_ )
10: **if** _action_ = _O_ _fwd_ **then**
11: _a_ _curr_ _←_ arg max _a_ _k_ _∈A_ _m_ _\{a_ _curr_ _}_ sim( _c_ _t_ _m_ +1 _, c_ _[m]_ _k_ [)]
12: **else if** _action_ = _O_ _split_ **then**
13: _subtasks ←_ DecomposeTask( _t_ _m_ +1 )
14: _task_ _ _state.context ←_ _task_ _ _state.context ⊕_ ProcessSubtasks( _subtasks, a_ _curr_ _, A_ _m_ )
15: _finished ←_ AllSubtasksCompleted( _subtasks_ )
16: **else**
17: _task_ _ _state.context ←_ _task_ _ _state.context ⊕_ ExecuteTask( _a_ _curr_ _, t_ _m_ +1 _,_ Select( _M_ _curr_ _[exe]_ _[, t]_ _[m]_ [+1] _[, k]_ [))]
18: _finished ←_ _true_
19: **end if**

20: **end while**
21: // 2. Network update
22: **for** each interacting pair ( _a_ _i_ _, a_ _j_ ) **do**
23: _w_ _m_ +1 ( _i, j_ ) _←_ _α · w_ _m_ ( _i, j_ ) + (1 _−_ _α_ ) _· S_ ( _a_ _[m]_ _i_ [+1] _, a_ _[m]_ _j_ [+1] _, t_ _m_ +1 )
24: **end for**
25: _**E**_ _m_ +1 _←{_ ( _a_ _[m]_ _i_ [+1] _, a_ _[m]_ _j_ [+1] ) _| w_ _m_ +1 ( _i, j_ ) _> θ_ _w_ _}_
26: // 3. Agent capability and memory update
27: **for** each participating agent _a_ _i_ **do**
28: _c_ _[m]_ _i_ [+1] _←_ _β · c_ _[m]_ _i_ [+ (1] _[ −]_ _[β]_ [)] _[ ·]_ [ ∆] _[c]_ _[m]_ _i_ [+1], Update _M_ _i_ _[rou]_ and _M_ _i_ _[exe]_
29: **end for**

30: **end for**
31: **return** _G_ _[∗]_ = ( _**A**_ _,_ _**E**_ )

Over tasks, the weight matrix _w_ _m_ will evolve based on collaborative success, and the edges with a lower weight than a
hyper-parameter threshold _θ_ _w_ are periodically pruned:

_**E**_ _**m**_ **+1** = _{_ ( _a_ _[m]_ _i_ [+1] _, a_ _[m]_ _j_ [+1] ) _| w_ _m_ +1 ( _i, j_ ) _> θ_ _w_ _}._ (3)

This pruning mechanism ensures that the network maintains efficient pathways while eliminating unproductive connections, optimizing both communication overhead and routing efficiency.

**3.3** **Adaptive Learning and Specialization**

AgentNet’s adaptive learning mechanism facilitates continuous improvement and specialization of agents based on
their task experiences, without the need for explicit role assignment. This process enables agents to gradually develop
expertise in specific domains, differentiating AgentNet from static multi-agent systems and allowing it to adapt to
evolving requirements over time.

Agents in AgentNet follow the _ReAct_ (Reasoning + Acting) framework Yao et al. [2023], Zhou et al. [2024], which
empowers agents to reason about a given query and its context before deciding appropriate actions for the executor
modules. In addition to the given query and its context, the agent also retrieves relevant trajectory fragments from its
memory modules to enhance reasoning and acing. The retrieval process is performed using a Retrieval-Augmented
Generation (RAG) mechanism [Lewis et al., 2020, Gao et al., 2023, Zhou et al., 2024], which allows the agent to
leverage past experiences to generate informed decisions and actions for new tasks.

6

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

In the AgentNet, Each agent _a_ _i_ _∈_ _**A**_ maintains two memory modules _M_ _i_ _[rou]_ and _M_ _i_ _[exe]_ for its router module _rou_ _i_ and
_exe_ _i_, which store local trajectory fragments from prior tasks corresponding to the specific steps where _a_ _i_ was actively
involved instead of storing the whole task trajectories cooperated by all agents.

Formally, each entry in _M_ _i_ _[rou]_ and _M_ _i_ _[exe]_ is the local step fragment represented as: _f_ _[r]_ = ( _o_ _[r]_ _, c_ _[r]_ _, a_ _[r]_ ), where _r_ represents
this entry belongs to _rou_ _i_ (when _r_ = _rou_ ) or _exe_ _i_ (when _r_ = _exe_ ). _o_ _[r]_ denotes the observation, namely the query of
the corresponding task, and _c_ _[r]_ represents the context of the corresponding task so far (i.e., partial trajectory before this
step), and _a_ _[r]_ is the action or response of the agent. These step fragments are collected from different tasks in which the
agent has participated and serve as experiential knowledge for future reasoning.

When agent _a_ _[m]_ _i_ [receives a new task] _[ t]_ _[m]_ [+1] [ to solve, it retrieves the] _[ k]_ [ most relevant fragments from both memory modules.]
For each module type _r ∈{rou, exe}_, the retrieval process is defined as:

Select( _M_ _i_ _[r]_ _[, t]_ _[m]_ [+1] _[, k]_ [) =] _[ {][f]_ 1 _[ r]_ _[, f]_ 2 _[ r]_ _[, . . ., f]_ _k_ _[ r]_ _[} ⊂]_ _[M]_ _[ r]_ _i_ _[,]_ [ such that]
_∀f_ _j_ _[r]_ _[∈]_ [Select][(] _[M]_ _[ r]_ _i_ _[, t]_ _[m]_ [+1] _[, k]_ [)][ and] _[ ∀][f][ ∈]_ _[M]_ _[ r]_ _i_ _[\]_ [ Select][(] _[M]_ _[ r]_ _i_ _[, t]_ _[m]_ [+1] _[, k]_ [) :] (4)

sim(embed( _o_ _[r]_ _f_ _j_ _[r]_ _[, c]_ _f_ _[r]_ _j_ _[r]_ [)] _[,]_ [ embed][(] _[o]_ _t_ _[r]_ _m_ +1 _[, c]_ _t_ _[r]_ _m_ +1 [))] _[ ≥]_ [sim][(][embed][(] _[o]_ _f_ _[r]_ _[, c]_ _[r]_ _f_ [)] _[,]_ [ embed][(] _[o]_ _t_ _[r]_ _m_ +1 _[, c]_ _t_ _[r]_ _m_ +1 [))] _[.]_

Here, embed( _·_ ) is a semantic embedding function that projects the input context into a high-dimensional vector space,
and the fragments with the highest relevance are retrieved to inform the agent’s reasoning or action for both routing and
execution processes.

Both the reasoning and acting processes are enhanced by the retrieval of historical task fragments, allowing the agent to
make better decisions based on prior experiences. The reasoning function for each module type is modeled as:

_R_ _a_ _i_ ( _t_ _m_ +1 _, r_ ) = _F_ reason ( _o_ _t_ _m_ +1 _,_ c _t_ _m_ +1 _, {f_ _j_ _[r]_ _[}]_ _[k]_ _j_ =1 [)] _[,]_ (5)

where _F_ reason represents the large language model that serves as the backbone of the LLM Agent, processing the inputs
to generate reasoned decisions. The reasoning function _R_ _a_ _i_ takes the current observation and question _o_ _t_ _m_ +1, the
historical context c _t_ _m_ +1 representing the partial task trajectory and interactions up to the current point, and the retrieved
fragments _{f_ _j_ _[r]_ _[}]_ _[k]_ _j_ =1 [as input to generate the reasoning output. The fragments allow the agent to reason based on prior]
experiences that are most relevant to the current situation.

Once the reasoning process has been completed, the agent executes the chosen action. The action is informed by the
reasoning output, which can be expressed as:

_A_ _a_ _i_ ( _t_ _m_ +1 _, r_ ) = _F_ act ( _o_ _t_ _m_ +1 _,_ c _t_ _m_ +1 _, R_ _a_ _i_ ( _t_ _m_ +1 _, r_ ) _, {f_ _j_ _[r]_ _[}]_ _[k]_ _j_ =1 [)] _[,]_ (6)

where _F_ act represents the large language model that serves as the backbone of the LLM Agent, translating reasoning into
concrete operations. The _A_ _a_ _i_ ( _t_ _m_ +1 _, r_ ) function utilizes the reasoning output _R_ _a_ _i_ ( _t_ _m_ +1 _, r_ ) along with the retrieved
memory fragments to determine the appropriate action. The specific action depends on the module type: for _r_ = _rou_,
the router module may produce actions such as forwarding the task to another agent or splitting it into subtasks; for
_r_ = _exe_, the executor module generates a single-step operation or response to directly address the final answer.

To manage memory effectively, each agent employs a dynamic memory management strategy. As the agent receives new
tasks, it evaluates the trajectories stored in its memory modules and decides which to retain or prune. This evaluation
is based on reasoning about the task context, historical usage patterns, and the relevance of each trajectory to future
tasks. Several factors influence the decision-making process, including the frequency of use, recency of tasks, and the
uniqueness of the trajectory. The agent assesses these factors through a prompt-based reasoning process that helps
determine the utility of each trajectory. When a memory module reaches its capacity limit _C_ max, the agent compares
the new trajectory with the existing ones in that memory module and selects the least useful trajectory to remove, thus
ensuring the memory pool remains focused on high-quality and relevant knowledge.

Through this adaptive and memory-driven learning process, agents in AgentNet continuously refine their expertise
and specialize in the areas where they excel. This specialization occurs naturally over time, allowing the system to
self-organize and adapt to the demands of a wide variety of tasks.

**3.4** **Dynamic Task Allocation**

The dynamic task allocation mechanism in AgentNet enables efficient distribution of tasks without centralized coordination, creating a responsive system that optimizes both performance and load balancing. This decentralized approach to

7

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-7-0.png)

Figure 4: Details of Dynamic Task Allocation.

task routing represents a significant advancement over static assignment strategies employed in traditional multi-agent
frameworks.

Each task _t ∈_ _T_ is formally represented as a tuple _t_ = ( _o_ _t_ _, c_ _t_ _, p_ _t_ ), where _o_ _t_ contains the task description in natural
language, _c_ _t_ is a vector of capability requirements, and _p_ _t_ denotes the priority level. To efficiently process a new task
_t_ _m_ +1 after completing task _t_ _m_, AgentNet employs a sophisticated mechanism to select the most suitable initial agent.

Agent capability representation and matching form the foundation of task allocation. Each agent _a_ _[m]_ _i_ [, after completing]
task _t_ _m_, possesses a capability vector _c_ _[m]_ _i_ [that is dynamically updated through task performance during system operation.]
In the initial allocation phase, the system selects an entry agent for _t_ _m_ +1 using the following formula:

_a_ _initial_ = argmax _{_ sim( _c_ _t_ _m_ +1 _, c_ _[m]_ _i_ [)] _[}][,]_ (7)
_a_ _i_ _∈A_ _m_

where _c_ _t_ _m_ +1 = Φ( _o_ _t_ _m_ +1 ) represents the capability requirements of task _t_ _m_ +1, _c_ _[m]_ _i_ [denotes the capability vector of agent]
_a_ _i_, and sim( _·, ·_ ) is a similarity function measuring the match between task requirements and agent capabilities. The
capability requirements are determined through different methodologies depending on task complexity:

Φ _atomic_ ( _t_ _m_ +1 ) _,_ for atomic tasks
_c_ _t_ _m_ +1 = �Φ _compound_ ( _t_ _m_ +1 ) _,_ for compound tasks _._ (8)

For atomic tasks, the system employs function Φ _atomic_ that maps task properties to capability requirements based on
predefined heuristics. For compound tasks, function Φ _compound_ leverages an instruction set containing carefully crafted
prompts that guide the large language model in analyzing task descriptions and inferring the required capability vectors.
The system subsequently ranks all agents according to capability matching scores and selects the highest-scoring agent
as the initial agent.

Once a task is assigned to the initial agent, this agent determines how to process the task based on the reasoning results
from its router module _rou_ _i_ . As illustrated in Figure 4, the agent can perform three operations:

1. **Forward** ( _O_ fwd ): Transfer the task unchanged to another more suitable agent, maintaining the task’s original
state and preserving the Directed Acyclic Graph (DAG) property of the routing path. Forwarding decisions
are based on analyzing the gap between the current agent’s capabilities and the task requirements, as well as
evaluating the capability vectors of other agents in the network.

2. **Split** ( _O_ split ): Decompose the task into subtasks, execute portions matching the agent’s expertise, and route the
remaining subtasks to an appropriate agents. Subtask routing follows this formula:

_a_ _next_ = argmax _{_ sim(Φ( _o_ _t_ _m_ +1 ) _, c_ _[m]_ _k_ [)] _[}][,]_ (9)
_a_ _k_ _∈A_ _m_ _\{a_ _i_ _}_

where Φ( _o_ _t_ _m_ +1 ) represents the capability requirements derived from the observation of subtask _j_, determined
through the current agent’s task decomposition reasoning, and _A_ _m_ _\{a_ _i_ _}_ denotes the set of all agents excluding
the current one.

3. **Execute** ( _O_ exec ): Complete the entire task without further delegation.

A key design feature in the system is that when an agent chooses to split a task, it only forwards the results of the
subtasks it has completed, and not the reasoning behind the decomposition. This prevents the transfer of unnecessary
information and ensures that task decomposition errors made by one agent do not propagate to other agents in the
network.

8

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

The agent capability vector _c_ _[m]_ _i_ is updated based on task execution history and success rates, using the following
formula:
_c_ _[m]_ _i_ [+1] = _β · c_ _[m]_ _i_ [+ (1] _[ −]_ _[β]_ [)] _[ ·]_ [ ∆] _[c]_ _[m]_ _i_ [+1] _,_ (10)

where _β ∈_ [0 _,_ 1] is a decay factor balancing historical capabilities with newly acquired ones, and ∆ _c_ _[m]_ _i_ [+1] represents the
new capability contribution demonstrated by the agent in task _t_ _m_ +1, calculated by analyzing the types of operations
successfully executed by the agent and the quality of results.

Furthermore, the task’s state is updated only when an agent completes a part of the task (whether by executing or
splitting it). When the agent completes a subtask, it updates the context and forwards it to the next agent:

context updated = context original _⊕_ result( _a_ _j_ _, t_ _i_ ) _._ (11)

While the task is only being forwarded from one agent to another, its state remains unchanged, preserving the Directed
Acyclic Graph (DAG) structure of the task routing path. This ensures that the task’s progression avoids being trapped in
an infinite loop during task forwarding, maintaining a consistent and effective routing process across different agents.

Through this dynamic task allocation mechanism, AgentNet can adaptively optimize task flow based on task characteristics and changes in agent capabilities, achieving improved overall system performance and efficient resource
utilization.

**4** **Experiment**

**4.1** **Experimental Setup**

**Tasks and Benchmarks** We evaluate methods using several benchmarks across three task categories, along with
custom constructed training and test sets for each benchmark:

    - **Mathematics** : This task involves mathematical problem and is evaluated using MATH Hendrycks et al. [2021],
which includes problems with 7 different types. The training set consists of 100 examples per type (total of
700 problems), while the test set consists of 20 examples per type (total of 140 problems).

    - **Logical Question Answering** : This task tests reasoning and logical question answering abilities using the
BBH (Big-Bench Hard) benchmark Suzgun et al. [2022]. The training set follows the MorphAgent setup,
selecting 627 examples from 20 tasks. For testing, each task has 5 examples of varying difficulty, totaling 100
test problems.

    - **Function-Calling** : This benchmark evaluates the agent’s ability to perform tool-augmented task planning and
API usage, based on the API-Bank dataset Li et al. [2023]. We construct a training set of 100 tasks and a
test set of 100 tasks, randomly sampled from the full API-Bank corpus. Since the original dataset does not
include category labels, we annotate each task using GPT-4o-mini to assign one of the seven task types: _health_,
_account_, _schedule_, _information_, _housework_, _finance_, and _others_ . Each task is further categorized into one of
three difficulty levels, determined by prompt complexity and required toolchain length.

**Baselines** We compare AgentNet with two categories of baselines: single-agent and multi-agent frameworks:

    - **Single-agent frameworks:** These methods involve a single agent solving tasks independently without
collaboration or coordination with other agents.

**– Direct** : A baseline approach where the LLM directly generates outputs.
**–** **React** : A prompting technique that elicits step-by-step reasoning from language models Wei et al. [2023],
Yao et al. [2023].

**–**
**Synapse** : A trajectory-as-exemplar prompting method, which prompts the LLM with complete trajectories
of the abstracted states and actions to improve multi-step decision-making. Zheng et al. [2024]

**–**
**Self-Consistency** : A decoding strategy that samples multiple reasoning paths and selects the most
consistent answer through majority voting, enhancing reliability Wang et al. [2023].

**–**
**Self-Refinement** : An iterative approach where models critically evaluate and improve their own solutions
over multiple passes, progressively enhancing solution quality Madaan et al. [2023].

    - **Multi-agent frameworks:** These methods involve multiple agents working collaboratively to solve tasks,
each contributing to different aspects of the task-solving process.

**–**
**MorphAgent** : A framework featuring self- evolving agent profiles that dynamically optimize individual
expertise in the profile through three metrics Lu et al. [2024].

9

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

Table 1: Performance comparison of different methods across various tasks. In all multi-agent methods, we set **3 agents** for each
method to ensure a fair comparison. The best result is in bold, while the second is underlined.

~~**Backbone**~~ ~~**Category**~~ ~~**Method**~~ ~~**MATH(Acc/%)**~~ ~~**BBH(Acc/%)**~~ ~~**API-Bank(Acc/%)**~~


Single Agent


Direct 47.86 69.00 26.00
React 77.14 88.00 29.00
Synapse 89.28 92.00 28.00
Self-Consistency 88.00 85.00 29.00
Self-Refinement 87.14 84.00 25.00


DeepSeek-V3

GPT-4o-mini

Qwen-turbo


MorghAgent 39.29 56.00 16.00
MetaGPT 92.14 64.00 22.00
Multi-Agent
AFLOW 91.67 88.00 28.00
GPTSwarm 72.14 90.00 21.00
~~**AgentNet**~~ ~~**92**~~ **.** ~~**86**~~ ~~**94**~~ **.** ~~**00**~~ ~~**30**~~ **.** ~~**00**~~


Single Agent


Direct 31.43 59.00 15.00
React 55.71 80.00 24.00
Synapse 77.14 79.00 22.00
Self-Consistency 54.28 85.00 22.00
Self-Refinement 68.57 81.00 23.00


MorghAgent 80.71 56.00 16.00
MetaGPT 73.57 53.00 19.00
Multi-Agent
AFLOW **85.00** 75.00 21.00
GPTSwarm **85.00** **86.00** 13.00
~~**AgentNet**~~ ~~**85**~~ **.** ~~**00**~~ ~~**86**~~ **.** ~~**00**~~ ~~**29**~~ **.** ~~**00**~~


Single Agent


Direct 37.85 57.00 27.00
React 53.57 69.00 23.00
Synapse 67.14 68.00 24.00
Self-Consistency 64.28 70.00 28.00
Self-Refinement 76.43 74.00 23.00


MorghAgent 16.43 56.00 9.00
MetaGPT 63.57 51.00 20.00
Multi-Agent
AFLOW **82.14** 57.00 22.00
GPTSwarm 79.29 75.00 30.00
~~**AgentNet**~~ ~~81~~ . ~~43~~ ~~**92**~~ **.** ~~**00**~~ ~~**32**~~ **.** ~~**00**~~

**–** **MetaGPT** : A software development framework where specialized agents (like product manager, architect,
engineer) collaborate in a waterfall workflow to complete complex engineering tasks Hong et al. [2024].

**–** **AFLOW** : A framework that optimizes agent workflows using Monte Carlo Tree Search over coderepresented workflows with execution feedback Zhang et al. [2024c].

**–** **GPTSwarm** : A framework modeling agents as computational graphs with automatic optimization of
both prompts and agent collaboration patterns Zhuge et al. [2024].

**Parameter Configuration** In our implementation, we configure the LLM API with a temperature of 0.0, a maximum
token limit of 2048, and a top-p value of 1.0, ensuring consistent results throughout our experiments and enabling
reliable comparisons and analysis. For the memory pool experiment, we utilize the "BAAI/bge-large-en-v1.5" model to
compute the similarity between task queries and database trajectories.

**4.2** **Main Results**

Table 1 summarizes performance across Math, Logical QA tasks and API-Calling tasks. For Math, Logical QAs
and API-Calling tasks, accuracy is reported. Compared to single-agent methods (e.g., Synapse, ReAct), AgentNet
achieves competitive or superior performance across all tasks. While ReAct performs well on Math and Logic, its static
prompting strategy limits generalization to more complex tasks. Against multi-agent baselines, AgentNet consistently
outperforms centralized frameworks such as MetaGPT, which suffers from limited scalability—e.g., only 53.00%
accuracy on Logical QA. AgentNet’s decentralized coordination and retrieval-augmented memory contribute to its
robustness across domains, particularly in tasks requiring contextual understanding and adaptive role specialization.

10

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

**4.3** **Experiments on Heterogeneous Agents**

To investigate the impact of agent diversity on performance, we designed a heterogeneity experiment across different
settings on the BBH task. Agents were tested under four configurations: fully homogeneous (identical models and
capabilities), LLM heterogeneity (different language models, same capabilities), skill heterogeneity (same model but
varied capabilities), and a combination of both. This design allows us to isolate and analyze how model-level and
capability-level diversity influence multi-agent collaboration.

Table 2: BBH Accuracy under Different Heterogeneity Settings (Acc%)

|Setting|Fully Homogeneous|Skill Hetero.|LLM Hetero.|Both Heter|
|---|---|---|---|---|
|3 Agents|0.86|0.84|0.81|0.81|
|5 Agents|0.79|0.86|0.85|0.85|



The results show that the impact of heterogeneity on multi-agent performance depends on team size. With 3 agents, the
fully homogeneous setting performs best, while introducing either model or skill diversity reduces accuracy, suggesting
uniform reasoning is more effective in small teams. However, with 5 agents, heterogeneous configurations outperform
the homogeneous one, indicating that diversity enhances collaboration and complementary reasoning in larger teams.
Overall, heterogeneity may introduce coordination overhead in small groups but offers clear benefits at larger scales.

**4.4** **Ablation Study**


**Router Effectiveness in AgentNet** To evaluate AgentNet’s decentralized router, experiments were conducted
comparing AgentNet with ablation configurations: "Totally Random", "Random Operations", "Random Next Agent ID"
and a centralized "Global Router". Each router manages external routing (selecting the next agent) and internal routing
(deciding to forward, split, or execute).



Performance was tested on the BBH task (training: 627
problems, testing: 100 problems), with results in Figure 5.
AgentNet outperforms randomized methods, achieving
82.14% accuracy during training and 86.00% during testing. Randomizing operations (forward/split/execute) affects task execution more directly, randomizing next agent
ID primarily results in suboptimal task delegation but
does not disrupt task completion as severely. These results underscore the critical role of effective routing and
suggest that optimizing routing decisions can significantly
enhance multi-agent system performance.







![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-10-0.png)


|AgentNet's Router Performance on BBH|Col2|Col3|Col4|Col5|Col6|
|---|---|---|---|---|---|
|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|
|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|627ps)<br>00ps)<br>71.<br>69.00|81.<br>00|4982.00 81.|18||
|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et||||||
|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|0|||||
|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et||||||
|AgentNet's Router Performance on BBH<br>90<br>T Te ras it T (r 6e 2n 7d 82.1486.00<br>n ps) 81.4982.00 81.1883.00<br>80 Test (100ps)<br>71.00<br>70 69.00 (%)<br>Accuracy<br>60<br>54.8655.00<br>50<br>40 RandT oot mally Random O Randomperations N Gext Agent ID lobal Router AgentN et|Randomom O per|Randomations|N Agent Gext ID lobal Router AgentN et|N Agent Gext ID lobal Router AgentN et|N Agent Gext ID lobal Router AgentN et|


enhance multi-agent system performance. Figure 5: AgentNet’s Router Performance on the BBH

**Impact of Evolution Phase** Results in Table 3 clearly Table 3: Performance Comparison of AgentNet vs. Without
indicate that AgentNet significantly improves perfor- evolution (Backbone: gpt-4o-mini)
mance compared to the non-evolution baseline. On the
MATH task, AgentNet achieves a score of 85.00 versus
77.86. For the function-calling task, performance im- ~~**Acc(%)**~~ ~~**Acc(%)**~~ ~~**Acc(%)**~~
proves notably from 23.00 to 32.00. On the BBH task, ~~w/o~~ ~~evolution~~ ~~77~~ . ~~86~~ ~~23~~ . ~~00~~ ~~76~~ . ~~00~~
accuracy rises from 76% to 86%, demonstrating the impact of evolution phase for AgentNet.

|Col1|Acc(%)|Acc(%)|Acc(%)|
|---|---|---|---|
|w/o evolutio<br>AgentNet|n 77.86<br>85.00|23.00<br>32.00|76.00<br>86.00|



These results confirm that AgentNet’s adaptive learning during the evolution phase effectively enhances agent specialization and task performance, demonstrating its essential role in the system’s optimization and overall efficiency.





**4.5** **Case Studies**

This case study is presented to illustrate the differences between the two methods, based on results obtained using
GPT-4o-mini on the BBH dataset. The left image shows the trajectory produced by the ReAct method, while the right
image illustrates the trajectory generated by AgentNet. In the case of ReAct, the lack of collective reasoning results in
an incorrect response after a single-step inference, highlighting the limitations of the method in handling tasks that
require more complex reasoning. In contrast, AgentNet uses a multi-step workflow where agents without the necessary
expertise are bypassed, while those with the relevant skills divide the task into smaller steps, leading to a more accurate
final solution.

11

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT


**Question:**
Which sentence has the correct adjective order?
**Options:**
**A.** old-fashioned circular green cardboard exercise
computer
**B.** old-fashioned green exercise circular cardboard
computer

**ReAct**

**Reasoning:** (B) was selected because it follows a common
pattern in English, where opinion adjectives (e.g.,
"old-fashioned") precede color adjectives (e.g., "green")
and shape adjectives (e.g., "circular").

**Action:** (B) **Ground Truth:(A)**

Figure 6: ReAct Response with Reasoning

**5** **Analysis**

**5.1** **Scalability and Robustness of the System**


**AgentNet (5 Agents)**
**Agent 0:** Decision: Forward Next Agent: Agent 1
**Agent 1:** Decision: Forward Next Agent: Agent 2
**Agent 2:** Decision: Forward Next Agent: Agent 3
**Agent 3:** Decision: Split
Executable: Adjective order analysis
Delegate: Final answer to another agent
Findings:

Correct order: Quantity, opinion, size, age, shape, color, origin,
material, purpose Correct Option: (A)
Next Agent: Agent 4
**Agent 4:** Decision: Execute Action: Confirmed option (A)
**Final Outcome:** (A) **Ground Truth:(A)**

Figure 7: AgentNet Task Breakdown


Based on the experimental results as illustrated in Figure 8, we observed that both training and testing performance
improve slightly as the number of agents and executor pool limit increase. However, the improvements are incremental,
with diminishing returns as the system scales up. Specifically, performance in the training phase increased from 80.38
for 3 agents and 30 executors to 81.18 for 9 agents and 40 executors. In the testing phase, performance fluctuated
between 80 and 86, with the highest performance seen in configurations with 40 executors.

![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-11-0.png)

Figure 8: AgentNet Performance with Different Net Parameters. Experiments were conducted with routers without pool limit, where
(A, B) represents A as the number of agents and B as the upper limit of the executor pool, with performance evaluated on the BBH.

These results suggest that AgentNet’s decentralized coordination model allows for gradual performance improvement
as resources are added. This indicates that AgentNet can scale effectively, enhancing performance without the dramatic
bottlenecks commonly seen in centralized systems. Additionally, while performance benefits from increased resources,
the marginal gains suggest there may be an optimal point where resource allocation reaches its most efficient balance.
The experiment demonstrates that AgentNet’s design, which dynamically adjusts agent connections and executor pool
sizes, effectively supports scalable and adaptable multi-agent systems with a high degree of fault tolerance.

**5.2** **Autonomous Specialization of Agents**

Based on the observed results in Figure 9, the experiments demonstrate that AgentNet’s multi-agent system can
naturally specialize agents in a decentralized environment. With varying numbers of agents and a fixed executor
pool of 40 pieces, the ability scores across different tasks such as reasoning, language, knowledge, and sequence
showed significant variation. As the number of agents increased, specialization became more evident, particularly in
complex tasks, with certain agents excelling in specific areas while others focused on different abilities. This highlights
AgentNet’s capacity to dynamically refine agent expertise and optimize performance in a decentralized, task-driven
system.

Notably, with 3 agents, the abilities were more evenly distributed across the agents, but as the number of agents
increased, specialization became more evident, especially in tasks like knowledge and sequence, where specific agents
showed notable proficiency. In the (5, 40) configuration, the specialization became clearer, with some agents excelling
in certain abilities, while others lagged behind in different tasks. As we scaled up to 7 and 9 agents, the system displayed
even greater specialization, especially in complex tasks, demonstrating AgentNet’s ability to allow for dynamic expertise

12

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-12-0.png)

Figure 9: Autonomous Specialization under Different Agent Sets. The upper limit of the executor pool is fixed at 40, regardless of
the number of agents. The experiment was run on the BBH, and the images show the final ability scores of the agents after training.

refinement. This confirms that AgentNet supports the hypothesis of autonomous specialization within a decentralized,
task-driven multi-agent system, where agents evolve to optimize task performance independently, without the need for
a central controller.

**5.3** **Evolution of Agents Networks**

The evolution of the agent network in our experiment is illustrated in Figure 10, which demonstrates the transition of a
multi-agent system composed of 5 agents running on the BBH (627 pieces) benchmark. The figure captures the network
at three key stages: the initial state, an intermediate state, and the final evolved state.

![](/Users/ravenoak/Documents/AgentNet-2504.00587v2-bib4llm/AgentNet-2504.00587v2/AgentNet-2504.00587v2.pdf-12-1.png)

Figure 10: Evolution Example of Agents Networks.

In the initial state, the network is fully connected with uniform connection values of 1.00, indicating equal capabilities
among all agents. At this stage, there is no specialization, and all agents are equally equipped to handle tasks.

As the network evolves, agents begin to specialize, and connection values vary, reflecting the strength of collaboration.
Stronger connections indicate tighter cooperation, while weaker ones suggest less interaction. This evolution shows
how agents naturally adapt and form more efficient collaboration patterns.

By the final stage, the network exhibits clear specialization, with agents taking on distinct roles. The connection values
further emphasize the growing cooperation between specialized agents, improving task performance. This progression
demonstrates the effectiveness of decentralized coordination, where evolving collaboration enhances task allocation,
scalability, and fault tolerance.

**6** **Limitations and Future Work**

Despite AgentNet implementing a fully distributed, adaptive learning multi-agent system (MAS) with dynamic task
allocation, several important limitations remain that require further exploration in future work.

One key challenge is how to improve task performance in heterogeneous agent environments. In real-world applications,
agents often vary significantly in terms of model capabilities, workflow structures, tools, and available data. The impact

13

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

of such heterogeneity on AgentNet’s performance, especially in terms of task coordination and resource allocation,
remains an open question. Understanding how to adapt the system to handle such variations efficiently will be crucial
for its scalability and effectiveness in complex environments.

Secondly, the decision-making process of the router within each agent, particularly in relation to exploration and
discovery, requires more in-depth study. Currently, the router selects agents from a relatively small pool of predefined
candidates. However, in larger-scale systems involving hundreds or potentially thousands of agents, the challenge of
accurately identifying the most suitable agent for task delegation becomes significantly more complex. This problem is
further compounded in heterogeneous settings, where different agents may possess distinct strengths and weaknesses. To
address this, future research could focus on developing more sophisticated routing mechanisms that can autonomously
identify and delegate tasks to the most appropriate agents, even in large and diverse agent pools.

Additionally, a promising direction for future work involves designing incentives that encourage the router to explore
agents beyond the predefined candidate set. By enabling AgentNet to dynamically discover new agents or specialized
capabilities, such an approach would enhance its adaptability and scalability, ultimately improving the system’s overall
performance and autonomy.

**7** **Conclusion**

In conclusion, AgentNet provides an effective approach to addressing the limitations of traditional centralized multiagent systems. With its decentralized architecture, dynamic task allocation, and adaptive learning mechanisms,
AgentNet improves scalability, fault tolerance, and task efficiency in collaborative environments. Its privacy-preserving
features further ensure secure cooperation across organizations. Our experimental results highlight the advantages
of this approach, demonstrating improvements in task efficiency, adaptability, and specialization. AgentNet offers a
practical framework for developing more flexible and secure multi-agent systems in dynamic, real-world settings.

**Acknowledgement**

The authors gratefully acknowledge the generous support provided by Bytedance, which has been instrumental in
enabling the successful execution of this research. Their sponsorship significantly contributed to the advancement and
completion of this work.

**Acknowledgement**

This research was supported by Bytedance through a sponsored project that facilitated the execution and completion of
this work.

**Ethics Statement**

This study did not involve human participants, animal subjects, or the use of personal data. All datasets and benchmarks
employed are publicly available and used in accordance with their respective licenses. Therefore, no ethics approval
was required.

**References**

OpenAI, Josh Achiam, Steven Adler, Sandhini Agarwal, et al. Gpt-4 technical report, 2024. URL [https://arxiv.](https://arxiv.org/abs/2303.08774)
[org/abs/2303.08774.](https://arxiv.org/abs/2303.08774)

Hugo Touvron, Louis Martin, Kevin Stone, et al. Llama 2: Open foundation and fine-tuned chat models, 2023. URL
[https://arxiv.org/abs/2307.09288.](https://arxiv.org/abs/2307.09288)

Yingxuan Yang, Bo Huang, Siyuan Qi, Chao Feng, Haoyi Hu, Yuxuan Zhu, Jinbo Hu, Haoran Zhao, Ziyi He, Xiao Liu,
Zongyu Wang, Lin Qiu, Xuezhi Cao, Xunliang Cai, Yong Yu, and Weinan Zhang. Who’s the mvp? a game-theoretic
evaluation benchmark for modular attribution in llm agents, 2025. URL [https://arxiv.org/abs/2502.](https://arxiv.org/abs/2502.00510)
[00510.](https://arxiv.org/abs/2502.00510)

Juraj Gottweis, Wei-Hung Weng, Alexander Daryin, Tao Tu, Anil Palepu, Petar Sirkovic, Artiom Myaskovsky, Felix
Weissenberger, Keran Rong, Ryutaro Tanno, Khaled Saab, Dan Popovici, Jacob Blum, Fan Zhang, Katherine Chou,
Avinatan Hassidim, Burak Gokturk, Amin Vahdat, Pushmeet Kohli, Yossi Matias, Andrew Carroll, Kavita Kulkarni,

14

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

Nenad Tomasev, Yuan Guan, Vikram Dhillon, Eeshit Dhaval Vaishnav, Byron Lee, Tiago R D Costa, José R Penadés,
Gary Peltz, Yunhan Xu, Annalisa Pawlosky, Alan Karthikesalingam, and Vivek Natarajan. Towards an ai co-scientist,
[2025. URL https://arxiv.org/abs/2502.18864.](https://arxiv.org/abs/2502.18864)

Pranav Putta, Edmund Mills, Naman Garg, Sumeet Motwani, Chelsea Finn, Divyansh Garg, and Rafael Rafailov. Agent
q: Advanced reasoning and learning for autonomous ai agents, 2024. URL [https://arxiv.org/abs/2408.](https://arxiv.org/abs/2408.07199)
[07199.](https://arxiv.org/abs/2408.07199)

Ruiwen Zhou, Yingxuan Yang, Muning Wen, Ying Wen, Wenhao Wang, Chunling Xi, Guoqiang Xu, Yong Yu, and
Weinan Zhang. Trad: Enhancing llm agents with step-wise thought retrieval and aligned decision, 2024. URL
[https://arxiv.org/abs/2403.06221.](https://arxiv.org/abs/2403.06221)

Taicheng Guo, Xiuying Chen, Yaqi Wang, Ruidi Chang, Shichao Pei, N. Chawla, Olaf Wiest, and Xiangliang Zhang.
Large language model based multi-agents: A survey of progress and challenges. In _International Joint Conference_
_on Artificial Intelligence_ [, 2024. URL https://api.semanticscholar.org/CorpusID:267412980.](https://api.semanticscholar.org/CorpusID:267412980)

Chuanneng Sun, Songjun Huang, and Dario Pompili. Llm-based multi-agent reinforcement learning: Current and
future directions. _ArXiv_, abs/2405.11106, 2024. URL [https://api.semanticscholar.org/CorpusID:](https://api.semanticscholar.org/CorpusID:269921354)
[269921354.](https://api.semanticscholar.org/CorpusID:269921354)

Yingxuan Yang, Qiuying Peng, Jun Wang, Ying Wen, and Weinan Zhang. Llm-based multi-agent systems: Techniques
[and business perspectives, 2024. URL https://arxiv.org/abs/2411.14033.](https://arxiv.org/abs/2411.14033)

Guangyao Chen, Siwei Dong, Yu Shu, Ge Zhang, Sesay Jaward, Karlsson Börje, Jie Fu, and Yemin Shi. Autoagents:
The automatic agents generation framework. _arXiv preprint_, 2023a.

Sirui Hong, Mingchen Zhuge, Jiaqi Chen, Xiawu Zheng, Yuheng Cheng, Ceyao Zhang, Jinlin Wang, Zili Wang, Steven
Ka Shing Yau, Zijuan Lin, Liyang Zhou, Chenyu Ran, Lingfeng Xiao, Chenglin Wu, and Jürgen Schmidhuber.
Metagpt: Meta programming for a multi-agent collaborative framework, 2024. URL [https://arxiv.org/](https://arxiv.org/abs/2308.00352)
[abs/2308.00352.](https://arxiv.org/abs/2308.00352)

Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li Jiang, Xiaoyun Zhang, Shaokun Zhang,
Jiale Liu, Ahmed Hassan Awadallah, Ryen W White, Doug Burger, and Chi Wang. Autogen: Enabling next-gen llm
[applications via multi-agent conversation, 2023. URL https://arxiv.org/abs/2308.08155.](https://arxiv.org/abs/2308.08155)

Qian Wang, Tianyu Wang, Qinbin Li, Jingsheng Liang, and Bingsheng He. Megaagent: A practical framework for
autonomous cooperation in large-scale llm agent systems. _arXiv preprint arXiv:2408.09955_, 2024.

Rui Ye, Shuo Tang, Rui Ge, Yaxin Du, Zhenfei Yin, Siheng Chen, and Jing Shao. Mas-gpt: Training llms to build
[llm-based multi-agent systems, 2025. URL https://arxiv.org/abs/2503.03686.](https://arxiv.org/abs/2503.03686)

Zitong Shi, Guancheng Wan, Wenke Huang, Guibin Zhang, Jiawei Shao, Mang Ye, and Carl Yang. Privacy-enhancing
[paradigms within federated multi-agent systems, 2025. URL https://arxiv.org/abs/2503.08175.](https://arxiv.org/abs/2503.08175)

Arthur B Kahn. Topological sorting of large networks. _Communications of the ACM_, 5(11):558–562, 1962.

Ravindra K Ahuja, Thomas L Magnanti, James B Orlin, et al. _Network flows: theory, algorithms, and applications_,
volume 1. Prentice hall Englewood Cliffs, NJ, 1993.

Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler,
Mike Lewis, Wen-tau Yih, Tim Rocktäschel, et al. Retrieval-augmented generation for knowledge-intensive nlp tasks.
_Advances in neural information processing systems_, 33:9459–9474, 2020.

Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, Haofen Wang, and Haofen
Wang. Retrieval-augmented generation for large language models: A survey. _arXiv preprint arXiv:2312.10997_, 2,
2023.

Dawei Gao, Zitao Li, Xuchen Pan, Weirui Kuang, Zhijian Ma, Bingchen Qian, Fei Wei, Wenhao Zhang, Yuexiang
Xie, Daoyuan Chen, Liuyi Yao, Hongyi Peng, Zeyu Zhang, Lin Zhu, Chen Cheng, Hongzhu Shi, Yaliang Li,
Bolin Ding, and Jingren Zhou. Agentscope: A flexible yet robust multi-agent platform, 2024. URL [https:](https://arxiv.org/abs/2402.14034)
[//arxiv.org/abs/2402.14034.](https://arxiv.org/abs/2402.14034)

Chrisantha Fernando, Dylan Banarse, Henryk Michalewski, Simon Osindero, and Tim Rocktäschel. Promptbreeder:
Self-referential self-improvement via prompt evolution. _arXiv preprint arXiv:2309.16797_, 2023.

Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav Santhanam, Sri Vardhamanan, Saiful Haq,
Ashutosh Sharma, Thomas T Joshi, Hanna Moazam, et al. Dspy: Compiling declarative language model calls into
self-improving pipelines. _arXiv preprint arXiv:2310.03714_, 2023.

Guibin Zhang, Yanwei Yue, Zhixun Li, Sukwon Yun, Guancheng Wan, Kun Wang, Dawei Cheng, Jeffrey Xu Yu, and
Tianlong Chen. Cut the crap: An economical communication pipeline for llm-based multi-agent systems, 2024a.
[URL https://arxiv.org/abs/2410.02506.](https://arxiv.org/abs/2410.02506)

15

AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems A P REPRINT

Mingchen Zhuge, Wenyi Wang, Louis Kirsch, Francesco Faccio, Dmitrii Khizbullin, and Jürgen Schmidhuber.
Gptswarm: Language agents as optimizable graphs. In _Forty-first International Conference on Machine Learning_,
2024.

Zijun Liu, Yanzhe Zhang, Peng Li, Yang Liu, and Diyi Yang. A dynamic llm-powered agent network for task-oriented
[agent collaboration, 2024. URL https://arxiv.org/abs/2310.02170.](https://arxiv.org/abs/2310.02170)

Guibin Zhang, Yanwei Yue, Xiangguo Sun, Guancheng Wan, Miao Yu, Junfeng Fang, Kun Wang, Tianlong Chen, and
Dawei Cheng. G-designer: Architecting multi-agent communication topologies via graph neural networks. _arXiv_
_preprint arXiv:2410.11782_, 2024b.

Weize Chen, Yusheng Su, Jingwei Zuo, Cheng Yang, Chenfei Yuan, Chen Qian, Chi-Min Chan, Yujia Qin, Yaxi Lu,
Ruobing Xie, et al. Agentverse: Facilitating multi-agent collaboration and exploring emergent behaviors in agents.
_arXiv preprint arXiv:2308.10848_, 2(4):6, 2023b.

Siyuan Lu, Jiaqi Shao, Bing Luo, and Tao Lin. Morphagent: Empowering agents through self-evolving profiles and
decentralized collaboration. _arXiv preprint arXiv:2410.15048_, 2024.

Yu Shang, Yu Li, Keyu Zhao, Likai Ma, Jiahe Liu, Fengli Xu, and Yong Li. Agentsquare: Automatic llm agent search
in modular design space. _arXiv preprint arXiv:2410.06153_, 2024.

Jiayi Zhang, Jinyu Xiang, Zhaoyang Yu, Fengwei Teng, Xionghui Chen, Jiaqi Chen, Mingchen Zhuge, Xin Cheng, Sirui
Hong, Jinlin Wang, et al. Aflow: Automating agentic workflow generation. _arXiv preprint arXiv:2410.10762_, 2024c.

Yue Hu, Yuzhu Cai, Yaxin Du, Xinyu Zhu, Xiangrui Liu, Zijie Yu, Yuchen Hou, Shuo Tang, and Siheng Chen.
Self-evolving multi-agent collaboration networks for software development. _arXiv preprint arXiv:2410.16946_, 2024.

Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. React: Synergizing
[reasoning and acting in language models, 2023. URL https://arxiv.org/abs/2210.03629.](https://arxiv.org/abs/2210.03629)

Dan Hendrycks, Collin Burns, Saurav Kadavath, Akul Arora, Steven Basart, Eric Tang, Dawn Song, and Jacob
Steinhardt. Measuring mathematical problem solving with the math dataset. _NeurIPS_, 2021.

Mirac Suzgun, Nathan Scales, Nathanael Schärli, Sebastian Gehrmann, Yi Tay, Hyung Won Chung, Aakanksha
Chowdhery, Quoc V. Le, Ed H. Chi, Denny Zhou, and Jason Wei. Challenging big-bench tasks and whether
[chain-of-thought can solve them, 2022. URL https://arxiv.org/abs/2210.09261.](https://arxiv.org/abs/2210.09261)

Minghao Li, Yingxiu Zhao, Bowen Yu, Feifan Song, Hangyu Li, Haiyang Yu, Zhoujun Li, Fei Huang, and Yongbin
Li. Api-bank: A comprehensive benchmark for tool-augmented llms, 2023. URL [https://arxiv.org/abs/](https://arxiv.org/abs/2304.08244)
[2304.08244.](https://arxiv.org/abs/2304.08244)

Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou.
Chain-of-thought prompting elicits reasoning in large language models, 2023. URL [https://arxiv.org/abs/](https://arxiv.org/abs/2201.11903)
[2201.11903.](https://arxiv.org/abs/2201.11903)

Longtao Zheng, Rundong Wang, Xinrun Wang, and Bo An. Synapse: Trajectory-as-exemplar prompting with memory
[for computer control, 2024. URL https://arxiv.org/abs/2306.07863.](https://arxiv.org/abs/2306.07863)

Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang, Aakanksha Chowdhery, and Denny
Zhou. Self-consistency improves chain of thought reasoning in language models, 2023. URL [https://arxiv.](https://arxiv.org/abs/2203.11171)
[org/abs/2203.11171.](https://arxiv.org/abs/2203.11171)

Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri,
Shrimai Prabhumoye, Yiming Yang, Shashank Gupta, Bodhisattwa Prasad Majumder, Katherine Hermann, Sean
Welleck, Amir Yazdanbakhsh, and Peter Clark. Self-refine: Iterative refinement with self-feedback, 2023. URL
[https://arxiv.org/abs/2303.17651.](https://arxiv.org/abs/2303.17651)

16

