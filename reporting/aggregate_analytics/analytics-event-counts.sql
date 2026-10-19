-- analytics-event-counts
--
-- required parameters (SQLAlchemy bind parameters):
-- :start (inclusive date)
-- :end (inclusive date)
--
-- event types/external data:
-- TRANSCRIPTION_RECEIVED, SUMMARY_RECEIVED
--
-- output columns and units:
-- event_type: text, analytics_event type name
-- recording_source: text, event_metadata recording_source ('' when not captured)
-- organisation_id: UUID as text ('' when the event has no organisation)
-- month: text, UTC calendar month as YYYY-MM
-- event_count: int, number of events in that group
--
-- inclusion/exclusion rules:
-- events whose occurred_datetime is within [start 00:00 UTC, end + 1 day 00:00 UTC)
--
-- duplicate/retried events:
-- relies on the unique (event_type, source_id) constraint, so retried events are already de-duplicated

SELECT
    event_type::text AS event_type,
    COALESCE(event_metadata ->> 'recording_source', '') AS recording_source,
    COALESCE(organisation_id::text, '') AS organisation_id,
    to_char(date_trunc('month', occurred_datetime AT TIME ZONE 'UTC'), 'YYYY-MM') AS month,
    count(*) AS event_count
FROM analytics_event
WHERE event_type IN ('TRANSCRIPTION_RECEIVED', 'SUMMARY_RECEIVED')
  AND occurred_datetime >= CAST(:start AS date)::timestamp AT TIME ZONE 'UTC'
  AND occurred_datetime < (CAST(:end AS date) + 1)::timestamp AT TIME ZONE 'UTC'
GROUP BY 1, 2, 3, 4
ORDER BY 4, 1, 3, 2;
