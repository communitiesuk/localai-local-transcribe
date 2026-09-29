-- median-summaries-per-transcript-and-template
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+01')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- SUMMARY_RECEIVED
--
-- output columns and units:
-- transcript_count: int, median_summary_count: int
--
-- inclusion/exclusion rules:
-- x
--
-- duplicate/retried events:
-- there's a unique constraint on (event_type, source_id), so there should be no duplicated events


WITH summaries_per_transcript AS (
    SELECT
        event_metadata ->> 'template_id' AS template_id,
        COUNT(*) AS summary_count
    FROM analytics_event
    WHERE event_type = 'SUMMARY_RECEIVED'
      AND occurred_datetime >= :reporting_period_start
      AND occurred_datetime < :reporting_period_end
    GROUP BY
        event_metadata ->> 'transcription_id',
        event_metadata ->> 'template_id'
)

SELECT
    template_id,
    COUNT(*) AS transcript_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY summary_count) AS median_summary_count
FROM summaries_per_transcript
GROUP BY template_id
ORDER BY template_id;
