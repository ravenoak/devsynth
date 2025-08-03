"""Orchestration example demonstrating ``CritiqueAgent`` usage."""

from devsynth.agents.critique_agent import CritiqueAgent


class MainAgent:
    """Trivial main agent that produces a code snippet."""

    def generate(self) -> str:
        """Return a code sample that intentionally needs work."""
        return "def add(a, b):\n    return a + b  # TODO"


def run() -> None:
    """Run a simple workflow passing results to the critic."""
    main_agent = MainAgent()
    critic = CritiqueAgent()

    produced = main_agent.generate()
    critique = critic.review(produced)

    print("Generated code:\n", produced)
    print("\nCritique:", critique)


if __name__ == "__main__":
    run()
