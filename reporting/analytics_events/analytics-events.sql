-- analytics-events
--
-- required parameters: none (exports every event up to the last full UTC day)
--
-- output columns and units:
-- id: UUID as text, analytics_event primary key
-- occurred_datetime: timestamp (UTC, no offset), when the event occurred
-- event_type: text, analytics_event type name
-- evaluation_id: text, opaque per-evaluation identifier
-- organisation_id: UUID as text ('' when the event has no organisation)
-- recording_id: UUID as text ('' when the event has no recording)
-- source_id: UUID as text ('' when the event has no idempotency key)
-- event_metadata: JSONB serialised as text ('' when the event has no metadata). Exported whole rather than
--   flattened into a column per key, so new keys appear in the export without a query change. Keys are
--   event-type specific - see AnalyticsEventMetadata in common/database/postgres_models.py.
--
-- inclusion/exclusion rules:
-- events on the current (partial) UTC day are excluded, so the last day in the export is always a full
-- 24 hours and per-day counts are not misread as a drop-off
--
-- duplicate/retried events:
-- relies on the unique (event_type, source_id) constraint, so retried events are already de-duplicated

SELECT
    id::text AS id,
    occurred_datetime AT TIME ZONE 'UTC' AS occurred_datetime,
    event_type::text AS event_type,
    evaluation_id,
    COALESCE(organisation_id::text, '') AS organisation_id,
    COALESCE(recording_id::text, '') AS recording_id,
    COALESCE(source_id::text, '') AS source_id,
    -- NULLIF catches JSONB holding the JSON value 'null' (how a Python None is serialised into the column),
    -- which ::text would otherwise export as the literal string 'null'. COALESCE catches a SQL NULL column.
    COALESCE(NULLIF(event_metadata::text, 'null'), '') AS event_metadata
FROM analytics_event
WHERE occurred_datetime < date_trunc('day', now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
ORDER BY occurred_datetime;
