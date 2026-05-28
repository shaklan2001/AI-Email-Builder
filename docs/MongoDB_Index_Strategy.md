# MongoDB Index Strategy

# AI-Driven Email Workflow Builder

**Version:** MVP v1  
**Purpose:** Production-oriented indexes aligned with Celery workers, API queries, and deduplication requirements.

---

## 1. Design principles

1. **Every repository query has a supporting index** — no collection scans on hot paths.
2. **Compound indexes** follow equality → sort/range field order (MongoDB ESR rule).
3. **Unique indexes** enforce business invariants (duplicate recipients, duplicate webhooks).
4. **Partial indexes** where useful to shrink working set (e.g. only `status: "waiting"` runs).
5. Create indexes at deploy via migration script or `createIndexes` in `core/database.py` startup hook.

---

## 2. Collection index reference

### `users`

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_users_clerk_user_id` | `{ clerk_user_id: 1 }` | `unique: true` | JWT → user lookup on every authenticated request |

```javascript
db.users.createIndex(
  { clerk_user_id: 1 },
  { unique: true, name: "idx_users_clerk_user_id" }
);
```

---

### `conversations`

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_conversations_user_id` | `{ user_id: 1, updated_at: -1 }` | — | List conversations for user |
| `idx_conversations_workflow_id` | `{ workflow_id: 1 }` | `sparse: true` | Load chat by workflow |

```javascript
db.conversations.createIndex(
  { user_id: 1, updated_at: -1 },
  { name: "idx_conversations_user_id" }
);

db.conversations.createIndex(
  { workflow_id: 1 },
  { sparse: true, name: "idx_conversations_workflow_id" }
);
```

---

### `workflows`

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_workflows_user_status` | `{ user_id: 1, status: 1 }` | — | Dashboard: list campaigns by status |
| `idx_workflows_user_updated` | `{ user_id: 1, updated_at: -1 }` | — | Dashboard: recent first |

```javascript
db.workflows.createIndex(
  { user_id: 1, status: 1 },
  { name: "idx_workflows_user_status" }
);

db.workflows.createIndex(
  { user_id: 1, updated_at: -1 },
  { name: "idx_workflows_user_updated" }
);
```

**Authorization:** Always query `{ _id: workflow_id, user_id: user_id }` using `_id` primary key + `user_id` filter.

---

### `email_templates`

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_templates_workflow_step_version` | `{ workflow_id: 1, step_id: 1, version: -1 }` | — | Fetch latest template per step |
| `idx_templates_workflow` | `{ workflow_id: 1 }` | — | List all templates for workflow |

```javascript
db.email_templates.createIndex(
  { workflow_id: 1, step_id: 1, version: -1 },
  { name: "idx_templates_workflow_step_version" }
);
```

**Application pattern:** `find({ workflow_id, step_id }).sort({ version: -1 }).limit(1)`

---

### `recipients`

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_recipients_workflow_email` | `{ workflow_id: 1, email: 1 }` | `unique: true` | **Prevents duplicate emails per workflow** |
| `idx_recipients_workflow_status` | `{ workflow_id: 1, status: 1 }` | — | Count valid recipients at activation |
| `idx_recipients_workflow_reply` | `{ workflow_id: 1, reply_received: 1 }` | — | Condition evaluation / analytics |

```javascript
db.recipients.createIndex(
  { workflow_id: 1, email: 1 },
  { unique: true, name: "idx_recipients_workflow_email" }
);

db.recipients.createIndex(
  { workflow_id: 1, status: 1 },
  { name: "idx_recipients_workflow_status" }
);
```

**CSV upload:** Check duplicate with `find_one({ workflow_id, email })` before insert.

---

### `workflow_runs` (critical for Celery)

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_runs_due_execution` | `{ next_execution_at: 1, status: 1 }` | — | **Worker: which runs are due now** |
| `idx_runs_workflow_recipient` | `{ workflow_id: 1, recipient_id: 1 }` | `unique: true` | One run per recipient per workflow |
| `idx_runs_workflow_status` | `{ workflow_id: 1, status: 1 }` | — | Pause / analytics / debugging |
| `idx_runs_status_updated` | `{ status: 1, updated_at: 1 }` | `partialFilterExpression: { status: "failed" }` | Ops: failed run sweep (optional) |

```javascript
// PRIMARY worker scheduler index
db.workflow_runs.createIndex(
  { next_execution_at: 1, status: 1 },
  { name: "idx_runs_due_execution" }
);

db.workflow_runs.createIndex(
  { workflow_id: 1, recipient_id: 1 },
  { unique: true, name: "idx_runs_workflow_recipient" }
);

db.workflow_runs.createIndex(
  { workflow_id: 1, status: 1 },
  { name: "idx_runs_workflow_status" }
);
```

**Scheduler query (Celery beat or polling worker):**

```javascript
db.workflow_runs.find({
  status: { $in: ["queued", "waiting"] },
  next_execution_at: { $lte: ISODate() }
}).limit(500);
```

> MVP may enqueue on activation instead of global poller; index still required for `resume_workflow_task` after `eta`.

---

### `analytics`

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_analytics_workflow_id` | `{ workflow_id: 1 }` | `unique: true` | One aggregate doc per workflow |

```javascript
db.analytics.createIndex(
  { workflow_id: 1 },
  { unique: true, name: "idx_analytics_workflow_id" }
);
```

**Updates:** `updateOne({ workflow_id }, { $inc: { opened: 1 } }, { upsert: true })`

---

### `webhook_events`

| Index name | Keys | Options | Query pattern |
|---|---|---|---|
| `idx_webhook_event_id` | `{ event_id: 1 }` | `unique: true`, `sparse: true` | **Idempotent webhook processing** |
| `idx_webhook_resend_message_id` | `{ resend_message_id: 1 }` | — | Lookup run by provider message |
| `idx_webhook_processed` | `{ processed: 1, received_at: 1 }` | — | Retry unprocessed events |
| `idx_webhook_workflow` | `{ workflow_id: 1, event_type: 1 }` | — | Debug / audit per campaign |

```javascript
// Resend sends unique event id in payload — store as event_id
db.webhook_events.createIndex(
  { event_id: 1 },
  { unique: true, sparse: true, name: "idx_webhook_event_id" }
);

db.webhook_events.createIndex(
  { resend_message_id: 1 },
  { name: "idx_webhook_resend_message_id" }
);

db.webhook_events.createIndex(
  { processed: 1, received_at: 1 },
  { name: "idx_webhook_processed" }
);
```

**Insert pattern:**

```python
try:
    await webhook_repo.insert_one({ "event_id": payload["id"], ... })
except DuplicateKeyError:
    return  # already processed — ack webhook
```

**Schema addition for LLD:** Add `event_id: str` to `webhook_events` document (Resend event UUID).

---

## 3. Index summary matrix

| Collection | Critical index | Why |
|---|---|---|
| `workflow_runs` | `{ next_execution_at: 1, status: 1 }` | Delayed step execution |
| `recipients` | `{ workflow_id: 1, email: 1 }` unique | Duplicate prevention |
| `webhook_events` | `{ event_id: 1 }` unique | Duplicate webhook prevention |
| `workflows` | `{ user_id: 1, status: 1 }` | Dashboard + auth scope |
| `users` | `{ clerk_user_id: 1 }` unique | Auth |

---

## 4. TTL indexes (optional — post-MVP)

Not required for assignment MVP. Future:

```javascript
// Raw webhook payloads older than 90 days
db.webhook_events.createIndex(
  { received_at: 1 },
  { expireAfterSeconds: 7776000, name: "idx_webhook_ttl" }
);
```

---

## 5. Startup script (Python)

```python
# app/core/database.py — call once on startup or via CLI

INDEX_SPECS = [
    ("users", [("clerk_user_id", 1)], {"unique": True, "name": "idx_users_clerk_user_id"}),
    ("workflows", [("user_id", 1), ("status", 1)], {"name": "idx_workflows_user_status"}),
    ("workflow_runs", [("next_execution_at", 1), ("status", 1)], {"name": "idx_runs_due_execution"}),
    ("recipients", [("workflow_id", 1), ("email", 1)], {"unique": True, "name": "idx_recipients_workflow_email"}),
    ("webhook_events", [("event_id", 1)], {"unique": True, "sparse": True, "name": "idx_webhook_event_id"}),
    # ... remaining from sections above
]

async def ensure_indexes(db):
    for collection, keys, options in INDEX_SPECS:
        await db[collection].create_index(keys, **options)
```

---

## 6. Explain plan checklist (before ship)

Run `explain("executionStats")` on:

- [ ] Dashboard workflow list by `user_id`
- [ ] Due `workflow_runs` query
- [ ] Recipient duplicate check on CSV row
- [ ] Latest `email_templates` by step
- [ ] Webhook insert with duplicate `event_id`

Target: `totalDocsExamined` ≈ `nReturned` on hot paths.
