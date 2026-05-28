# End-to-end integration testing

Automated integration tests for the full builder pipeline without manual MongoDB or Redis setup.

## Test harness

- `tests/integration/e2e_fixtures.py` — in-memory workflow runs, mock email provider, campaign/workflow fixtures
- `tests/integration/conftest.py` — Celery `task_always_eager` for synchronous task chains
- Patches `workflow_execution_service`, `workflow_run_repository`, and worker DB wrappers

## Scenarios

### Scenario 1 — Campaign → email sent

1. Campaign state with product + generated workflow
2. Review approval (`apply_review_approve`)
3. Workflow activation
4. Celery executes first `send_email` step
5. Assert initial email recorded on mock provider

### Scenario 2 — No reply → follow-up

1. Execute initial send → wait
2. Resume after wait with no reply (`condition_result=False`)
3. Follow-up branch email sent
4. Run completes

### Scenario 3 — Reply → auto response

1. Inbound reply processed
2. Intent classified (`need_more_info`)
3. Company knowledge tool selected
4. Auto-response email sent via `EmailService`

### Scenario 4 — Email failure → retry → success

1. Mock provider fails first send
2. `send_email_task` Celery retry on `retry_queue`
3. Second attempt succeeds

## Run

```bash
cd backend && uv run pytest tests/integration/test_e2e_scenarios.py -v
```

## Check when done

- [x] All four scenarios pass
- [x] No manual DB changes required
