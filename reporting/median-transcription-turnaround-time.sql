-- median transcription turnaround time
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+01')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- AUDIO_UPLOAD_STARTED, TRANSCRIPTION_RECEIVED
--
-- output columns and units:
-- matched_recording_count: int, number of recordings with both valid upload started and transcription received events
-- median_turnaround_seconds: numeric, median seconds between audio upload starting and transcription being received
--
-- inclusion/exclusion rules:
-- includes recordings whose earliest TRANSCRIPTION_RECEIVED event occurred within the reporting period
--
-- duplicate/retried events:
-- uses the earliest AUDIO_UPLOAD_STARTED and earliest TRANSCRIPTION_RECEIVED per recording_id


WITH upload_started AS (
    SELECT
        recording_id,
        MIN(occurred_datetime) AS upload_started_at
    FROM analytics_event
    WHERE event_type = 'AUDIO_UPLOAD_STARTED'
        AND recording_id IS NOT NULL
    GROUP BY recording_id
),

transcription_received AS (
    SELECT
        recording_id,
        MIN(occurred_datetime) AS transcription_received_at
    FROM analytics_event
    WHERE event_type = 'TRANSCRIPTION_RECEIVED'
        AND recording_id IS NOT NULL
    GROUP BY recording_id
),

matched_recordings AS (
    SELECT
        EXTRACT(EPOCH FROM (tr.transcription_received_at - us.upload_started_at)) AS turnaround_seconds
    FROM transcription_received tr
    INNER JOIN upload_started us USING (recording_id)
    WHERE tr.transcription_received_at >= :reporting_period_start
      AND tr.transcription_received_at < :reporting_period_end
)

SELECT
    COUNT(*) AS matched_recording_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY turnaround_seconds) AS median_turnaround_seconds
FROM matched_recordings;
