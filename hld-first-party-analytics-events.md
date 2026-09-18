# HLD: First-Party Analytics Event Recording

Status: Draft
Related: ADR-028 (Analytics Tooling)

## 1. Context

ADR-028 decided we'll use a first-party database (alongside Plausible) to record
per-user analytics events, because it avoids the need for a cookie consent banner
(confirmed with data governance) while still letting us measure real-world impact.

This HLD proposes the implementation for capturing the eight events listed in the
ticket. Calculating measures/reports from these events is explicitly **out of
scope**.

## 2. Events to capture

| Event                          | Fields                                                            | Trigger point (existing code)                                                                                     |
|--------------------------------|-------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `USER_INVITED`                 | evaluation_id, time                                               | `backend/api/routes/users.py::create_user` — after a new `User` row is committed by an org admin invite            |
| `USER_AUTHENTICATED`           | evaluation_id, time                                               | `backend/api/dependencies/get_current_user.py::get_current_user` — see §4.2 for de-duplication logic               |
| `USER_DELETED`                 | evaluation_id, time                                               | `backend/api/routes/users.py::delete_user` — after the target user is deleted                                      |
| `AUDIO_UPLOAD_STARTED`         | evaluation_id, recording_id, time                                 | `backend/api/routes/transcriptions.py::create_recording` — after `Recording` row created & presigned URL issued    |
| `AUDIO_UPLOAD_COMPLETED`       | evaluation_id, recording_id, audio_duration_seconds, time         | `backend/api/routes/transcriptions.py::create_transcription` — after `storage_service.check_object_exists()` confirms the file landed in S3, before the job is queued |
| `SUMMARY_RECEIVED`             | evaluation_id, time                                               | `common/services/minute_handler_service.py::process_minute_generation_message` — on successful `JobStatus.COMPLETED` |
| `TRANSCRIPTION_RECEIVED`       | evaluation_id, recording_id, time                                 | `common/services/transcription_handler_service.py::process_transcription` — on successful `JobStatus.COMPLETED`     |
| `TRANSCRIPTION_EDIT_SUBMITTED` | evaluation_id, recording_id, edit_type, time                      | `backend/api/routes/transcriptions.py` speaker/text edit endpoints, after the edit is committed                    |

Note: `AUDIO_UPLOAD_STARTED`/`AUDIO_UPLOAD_COMPLETED` don't correspond to an actual
byte-stream through our backend — the browser PUTs the file directly to S3 using a
presigned URL. "Started" = presigned URL issued; "Completed" = we've confirmed the
object exists in S3 (currently done as a side-effect of starting the transcription
job, which is close enough in time to be a reasonable proxy for "completed").

## 3. Data model

New table, added via an Alembic migration, independent of `user`/`recording` (no
FKs) so events remain valid even after account or recording deletion:

```python
class AnalyticsEventType(StrEnum):
    USER_INVITED = auto()
    USER_AUTHENTICATED = auto()
    USER_DELETED = auto()
    AUDIO_UPLOAD_STARTED = auto()
    AUDIO_UPLOAD_COMPLETED = auto()
    SUMMARY_RECEIVED = auto()
    TRANSCRIPTION_RECEIVED = auto()
    TRANSCRIPTION_EDIT_SUBMITTED = auto()


class AnalyticsEvent(BaseTableMixin, table=True):
    __tablename__ = "analytics_event"
    occurred_datetime: datetime = Field(sa_column=created_datetime_column(), default=None)
    event_type: AnalyticsEventType = Field(sa_column=Column(Enum(AnalyticsEventType, name="analyticseventtype"), nullable=False))
    evaluation_id: str | None = Field(default=None, index=True)  # not a FK — evaluation_id is opaque and user-supplied
    recording_id: UUID | None = Field(default=None, index=True)  # not a FK, for the same reason
    event_metadata: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
```

Index on `(event_type, evaluation_id)` to support future per-user, per-event
reporting queries efficiently.

We deliberately store `evaluation_id` (a string the org admin sets when inviting a
user) rather than `user_id`. This keeps events pseudonymous/decoupled from the
`user` table lifecycle — deleting a user (`DELETE /users/{id}`) does not need to
touch analytics data, and reporting only ever needs to join on evaluation_id.

**Users without an `evaluation_id`**: current invite flow (`UserCreate.evaluation_id`)
requires a non-empty value, so in practice every user created going forward has one.
`User.evaluation_id` remains nullable in the schema for legacy accounts pre-dating
this field. Proposal: skip recording an event for a user with no `evaluation_id`
(there's nothing pseudonymous to report against). **Open question for product/data
governance**: confirm this is acceptable, or whether we still want a null-evaluation_id
row so volumetric events aren't silently dropped from counts.

## 4. Recording service

Add `common/services/analytics_service.py` with a single entry point:

```python
async def record_analytics_event(
    session: AsyncSession,
    event_type: AnalyticsEventType,
    evaluation_id: str | None,
    recording_id: UUID | None = None,
) -> None:
```

Used from both the FastAPI backend (async session) and the Ray worker (sync
session) — a thin sync wrapper will be provided for the worker's `SessionLocal()`
pattern, mirroring how `minute_handler_service`/`transcription_handler_service`
already use sync sessions.

### 4.1 Failure isolation

Analytics recording must never break the primary user journey. The service wraps
its insert in try/except, logs on failure, and swallows the exception. This
matches the existing pattern of best-effort side channels in the codebase (e.g.
`identify_speakers` doesn't fail the transcription if speaker labelling errors).

### 4.2 De-duplicating `USER_AUTHENTICATED`

`get_current_user` runs on **every authenticated request** (it decodes the ALB
OIDC JWT and re-validates each time), not just at login. Recording an event per
request would massively over-count "authentication" and swamp the other events.

Proposal: treat authentication as "new" only if the gap since `User.last_login`
exceeds a session-like window (e.g. 30 minutes — configurable via settings,
consistent with typical browser/ALB session semantics). Compute this **before**
`last_login` is overwritten:

```python
is_new_session = (datetime.now(UTC) - user.last_login) > settings.ANALYTICS_SESSION_GAP
user.last_login = datetime.now(UTC)
...
if is_new_session:
    await record_analytics_event(session, AnalyticsEventType.USER_AUTHENTICATED, user.evaluation_id)
```

**Open question**: confirm the session-gap window with stakeholders — it directly
affects how "authentication" counts are interpreted in reporting.

### 4.3 Which "summary" counts

`minute_handler_service` has two success paths: initial generation
(`process_minute_generation_message`) and AI-edit (`process_minute_edit_message`).
The ticket describes a single "summary received" event; proposal is to fire it
only for **initial generation**, since edits are a different, already-existing
summary being modified rather than a new one being produced.
**Open question**: confirm AI-edited summaries shouldn't also count.

## 5. Non-functional considerations

* **Volume**: bounded by real user/job activity (same order of magnitude as
  `user`/`transcription`/`recording` rows) — no special scaling needed.
* **Privacy**: only `evaluation_id` (an opaque, admin-assigned string) and
  `recording_id` (an opaque UUID) are stored — no email, name, or free-text
  content. Consistent with the "no cookie banner needed" basis in ADR-028.
* **Retention**: not addressed by the ticket. Recommend explicitly deciding a
  retention/deletion policy for `analytics_event` with data governance (e.g. does
  it need to respect `User.data_retention_days`, or does it outlive the account by
  design since it's decoupled from `user_id`?). **Open question**.

## 6. Rollout

1. Alembic migration: add `analytics_event` table + `analyticseventtype` enum.
2. Add `analytics_service.py` with `record_analytics_event`.
3. Instrument the eight call sites listed in §2.
4. Unit tests per call site confirming an event row is written with correct
   fields on success, and that failures in analytics recording don't propagate.
5. No frontend changes required — all instrumentation is server-side.

## 7. Out of scope

* Any dashboard, aggregation, or reporting query against these events.
* Retrofitting historical events for actions that already happened before this
  ships.
