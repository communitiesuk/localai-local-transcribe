-- median-edits-per-transcript
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+01')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- TRANSCRIPTION_RECEIVED, TRANSCRIPTION_EDIT_SUBMITTED
--
-- output columns and units:
-- transcript_count: int, number of transcripts whose first received event falls within the reporting period
-- median_edit_count: numeric, median number of submitted edits per transcript
--
-- inclusion/exclusion rules:
-- includes transcripts with a TRANSCRIPTION_RECEIVED event within the reporting period
--
-- duplicate/retried events:
-- uses the earliest TRANSCRIPTION_RECEIVED event per source_id/recording_id, for which every TRANSCRIPTION_EDIT_SUBMITTED is counted

WITH first_transcription_received AS (
    SELECT
        source_id AS transcription_id,
        recording_id,
        MIN(occurred_datetime) AS transcription_received_at
    FROM analytics_event
    WHERE event_type = 'TRANSCRIPTION_RECEIVED'
      AND source_id IS NOT NULL
      AND recording_id IS NOT NULL
    GROUP BY source_id, recording_id
),

transcripts_in_period AS (
    SELECT
        transcription_id,
        recording_id
    FROM first_transcription_received
    WHERE transcription_received_at >= :reporting_period_start
      AND transcription_received_at < :reporting_period_end
),

edits_per_transcript AS (
    SELECT
        tip.transcription_id,
        COUNT(ae.id) AS edit_count
    FROM transcripts_in_period tip
    LEFT JOIN analytics_event ae
        ON ae.event_type = 'TRANSCRIPTION_EDIT_SUBMITTED'
       AND ae.recording_id = tip.recording_id
    GROUP BY tip.transcription_id
)

SELECT
    COUNT(*) AS transcript_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY edit_count) AS median_edit_count
FROM edits_per_transcript;
