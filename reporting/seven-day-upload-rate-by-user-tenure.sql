-- seven-day-upload-rate-by-user-tenure
--
-- required parameters:
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- USER_FIRST_AUTHENTICATED, USER_DELETED, AUDIO_UPLOAD_COMPLETED
--
-- output columns and units:
-- user_tenure_weeks: int, weeks between first authentication and reporting_period_end
-- user_count: int, users in the tenure bucket
-- active_user_count: int, users in the tenure bucket with at least one upload in past 7 days
-- seven_day_upload_rate_percent: numeric, percentage of active users over all users in that bucket
--
-- inclusion/exclusion rules:
-- x
--
-- duplicate/retried events:
-- uses the earliest USER_FIRST_AUTHENTICATED and USER_DELETED event per evaluation_id


WITH first_authenticated_users AS (
    SELECT
        evaluation_id,
        MIN(occurred_datetime) AS first_authenticated_at
    FROM analytics_event
    WHERE event_type = 'USER_FIRST_AUTHENTICATED'
      AND evaluation_id IS NOT NULL
    GROUP BY evaluation_id
),

deleted_users AS (
    SELECT
        evaluation_id,
        MIN(occurred_datetime) AS deleted_at
    FROM analytics_event
    WHERE event_type = 'USER_DELETED'
      AND evaluation_id IS NOT NULL
    GROUP BY evaluation_id
),

eligible_users AS (
    SELECT
        fau.evaluation_id,
        FLOOR(
            EXTRACT(EPOCH FROM (:reporting_period_end::timestamptz - fau.first_authenticated_at))
            / (7 * 24 * 60 * 60)
        )::int AS user_tenure_weeks
    FROM first_authenticated_users fau
    LEFT JOIN deleted_users du USING (evaluation_id)
    WHERE fau.first_authenticated_at < :reporting_period_end
      AND (du.deleted_at IS NULL OR du.deleted_at >= :reporting_period_end)
),

active_users AS (
    SELECT DISTINCT
        evaluation_id
    FROM analytics_event
    WHERE event_type = 'AUDIO_UPLOAD_COMPLETED'
      AND evaluation_id IS NOT NULL
      AND occurred_datetime >= (:reporting_period_end::timestamptz - INTERVAL '7 days')
      AND occurred_datetime < :reporting_period_end
)

SELECT
    eu.user_tenure_weeks,
    COUNT(*) AS user_count,
    COUNT(au.evaluation_id) AS active_user_count,
    100.0 * COUNT(au.evaluation_id) / COUNT(*) AS seven_day_upload_rate_percent
FROM eligible_users eu
LEFT JOIN active_users au USING (evaluation_id)
GROUP BY eu.user_tenure_weeks
ORDER BY eu.user_tenure_weeks;