-- analytics-events
--
-- required parameters: none (exports every event, all dates)
--
-- output columns and units:
-- id: UUID as text, analytics_event primary key
-- occurred_datetime: timestamp (UTC, no offset), when the event occurred
-- event_type: text, analytics_event type name
-- evaluation_id: text, opaque per-evaluation identifier
-- organisation_id: UUID as text ('' when the event has no organisation)
-- recording_id: UUID as text ('' when the event has no recording)
-- source_id: UUID as text ('' when the event has no idempotency key)
-- edit_type: text, event_metadata edit_type ('' when not captured)
-- recording_source: text, event_metadata recording_source ('' when not captured)
-- template_id: text, event_metadata template_id ('' when not captured)
-- transcription_id: text, event_metadata transcription_id ('' when not captured)
-- audio_duration_seconds: numeric, event_metadata audio_duration_seconds (null when not captured)
--
-- inclusion/exclusion rules: none, full export
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
    COALESCE(event_metadata ->> 'edit_type', '') AS edit_type,
    COALESCE(event_metadata ->> 'recording_source', '') AS recording_source,
    COALESCE(event_metadata ->> 'template_id', '') AS template_id,
    COALESCE(event_metadata ->> 'transcription_id', '') AS transcription_id,
    (event_metadata ->> 'audio_duration_seconds')::numeric AS audio_duration_seconds
FROM analytics_event
ORDER BY occurred_datetime;
