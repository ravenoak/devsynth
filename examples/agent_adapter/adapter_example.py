from devsynth.adapters.agents.agent_adapter import AgentAdapter


def main() -> None:
    adapter = AgentAdapter()
    adapter.create_team("demo")
    adapter.set_current_team("demo")

    agent = adapter.create_agent("orchestrator")
    adapter.add_agent_to_team(agent)

    result = adapter.process_task(
        {
            "task_type": "specification",
            "requirements": "Build a CLI todo app",
        }
    )
    print(result)


if __name__ == "__main__":
    main()
