-- median-summaries-per-transcript-and-template
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+00')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+00')
--
-- event types/external data:
-- SUMMARY_RECEIVED
--
-- output columns and units:
-- template_id: UUID, template id from SUMMARY_RECEIVED event_metadata
-- transcript_count: numeric, number of transcripts that have been summarised with that template
-- median_summary_count: numeric, median number of times that template summarises a transcript
--
-- inclusion/exclusion rules:
-- SUMMARY_RECEIVED events that occurred within the reporting period
-- default templates have a NULL template_id
--
-- duplicate/retried events:
-- duplicate events prevented by the unique constraint on (event_type, source_id)


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
