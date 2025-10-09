import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.methodology.base import Phase
from devsynth.methodology.sprint_adapter import (
    CEREMONY_PHASE_MAP,
    align_sprint_planning,
    align_sprint_review,
)
from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Load the feature file
scenarios(feature_path(__file__, "general", "complete_sprint_edrr_integration.feature"))


@pytest.fixture
def context():
    class Ctx:
        def __init__(self):
            self.adapter_mapping = None
            self.planning_sections = None
            self.review_sections = None
            self.aligned_planning = None
            self.aligned_review = None

    return Ctx()


# Background
@given("a sprint adapter with default ceremony mappings")
def sprint_adapter_with_defaults(context):
    # Expose the default mapping for assertions if needed
    context.adapter_mapping = CEREMONY_PHASE_MAP


# Scenario: Align sprint planning with EDRR phases
@given("sprint planning sections for planning and review")
def given_planning_sections(context):
    context.planning_sections = {
        "planning": {"goals": ["G1", "G2"]},
        "review": {"criteria": ["C1", "C2"]},
    }


@when("the sections are aligned to EDRR phases")
def when_align_planning(context):
    context.aligned_planning = align_sprint_planning(context.planning_sections)


@then("planning data maps to the Expand phase")
def then_planning_maps_to_expand(context):
    assert Phase.EXPAND in context.aligned_planning
    assert (
        context.aligned_planning[Phase.EXPAND] == context.planning_sections["planning"]
    )


@then("review data maps to the Refine phase")
def then_review_maps_to_refine(context):
    assert Phase.REFINE in context.aligned_planning
    assert context.aligned_planning[Phase.REFINE] == context.planning_sections["review"]


# Scenario: Align sprint review feedback with EDRR phases
@given("sprint review outcomes for the review ceremony")
def given_review_outcomes(context):
    context.review_sections = {
        "review": {"feedback": ["Well done", "Improve tests"]},
        # Include an unmapped/irrelevant ceremony to verify it is ignored
        "demo": {"notes": ["Not a mapped ceremony"]},
    }


@when("the feedback is aligned to EDRR phases")
def when_align_review(context):
    context.aligned_review = align_sprint_review(context.review_sections)


@then("the Refine phase contains the review feedback")
def then_refine_contains_feedback(context):
    assert Phase.REFINE in context.aligned_review
    assert context.aligned_review[Phase.REFINE] == context.review_sections["review"]


@then("unrelated ceremonies are ignored")
def then_unrelated_ignored(context):
    # Only "review" maps to a Phase; ensure no entry was created for "demo"
    assert Phase.EXPAND not in context.aligned_review
    assert Phase.DIFFERENTIATE not in context.aligned_review
    assert Phase.RETROSPECT not in context.aligned_review
