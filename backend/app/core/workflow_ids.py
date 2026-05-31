RESERVED_WORKFLOW_IDS = frozenset({"new"})


def assert_valid_workflow_id(workflow_id: str) -> None:
    if workflow_id in RESERVED_WORKFLOW_IDS:
        msg = f"Invalid workflow_id: {workflow_id!r}"
        raise ValueError(msg)
