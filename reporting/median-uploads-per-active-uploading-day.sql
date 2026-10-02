-- median uploads per active uploading day per user
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+00')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+00')
--
-- event types/external data:
-- AUDIO_UPLOAD_COMPLETED
--
-- output columns and units:
-- active_user_day_count: int, number of days with at least one completed upload
-- median_completed_uploads_per_active_user_day: numeric, median number of completed uploads per active uploading day per user
--
-- inclusion/exclusion rules:
-- AUDIO_UPLOAD_COMPLETED events that occurred within the reporting period
--
-- duplicate/retried events:
-- counts distinct source_id values as one completed upload


WITH completed_uploads_per_user_day AS (
    SELECT
        evaluation_id,
        (occurred_datetime AT TIME ZONE 'UTC')::date AS upload_day,
        COUNT(DISTINCT source_id) AS completed_upload_count
    FROM analytics_event
    WHERE event_type = 'AUDIO_UPLOAD_COMPLETED'
      AND evaluation_id IS NOT NULL
      AND source_id IS NOT NULL
      AND occurred_datetime >= :reporting_period_start
      AND occurred_datetime < :reporting_period_end
    GROUP BY
        evaluation_id,
        (occurred_datetime AT TIME ZONE 'UTC')::date
)

SELECT
    COUNT(*) AS active_user_day_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY completed_upload_count) 
        AS median_completed_uploads_per_active_user_day
FROM completed_uploads_per_user_day;
