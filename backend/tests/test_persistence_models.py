"""Compile-time checks for Beanie documents and Pydantic persistence schemas."""


def test_beanie_document_models_import() -> None:
    from app.models import BEANIE_DOCUMENT_MODELS

    assert len(BEANIE_DOCUMENT_MODELS) == 9


def test_persistence_schemas_import() -> None:
    from app.schemas import (
        CampaignStatus,
        LeadStatus,
        CampaignCreate,
        ExecutionRead,
        WorkflowVersionRead,
    )

    assert CampaignStatus.DRAFT.value == "draft"
    assert LeadStatus.BOOKED_DEMO.value == "booked_demo"
    assert CampaignCreate(name="Test", user_id="u1").name == "Test"
    assert ExecutionRead.model_json_schema()["properties"]["workflow_id"]
    assert WorkflowVersionRead.model_json_schema()["properties"]["version"]
