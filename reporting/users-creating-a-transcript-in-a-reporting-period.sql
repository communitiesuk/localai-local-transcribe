-- users-creating-transcript-in-reporting-period
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+01')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- USER_FIRST_AUTHENTICATED, USER_DELETED, TRANSCRIPTION_RECEIVED
--
-- output columns and units:
-- eligible_user_count: int, active users within the reporting period
-- users_with_transcription_count: int, eligible users with at least one transcription received in the reporting period
-- users_with_transcription_percent: numeric, percentage of eligible users with at least one transcription received
--
-- inclusion/exclusion rules:
-- active only inside of the reporting period
--
-- duplicate/retried events:
-- uses the earliest USER_FIRST_AUTHENTICATED/USER_DELETED event per evaluation_id
-- counts each user at most once for transcription activity, regardless of duplicate TRANSCRIPTION_RECEIVED events


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
        fau.evaluation_id
    FROM first_authenticated_users fau
    LEFT JOIN deleted_users du USING (evaluation_id)
    WHERE fau.first_authenticated_at < :reporting_period_end
      AND (du.deleted_at IS NULL OR du.deleted_at > :reporting_period_start)
),

users_with_transcription AS (
    SELECT DISTINCT
        evaluation_id
    FROM analytics_event
    WHERE event_type = 'TRANSCRIPTION_RECEIVED'
      AND evaluation_id IS NOT NULL
      AND occurred_datetime >= :reporting_period_start
      AND occurred_datetime < :reporting_period_end
)

SELECT
    COUNT(*) AS eligible_user_count,
    COUNT(uwt.evaluation_id) AS users_with_transcription_count,
    100.0 * COUNT(uwt.evaluation_id) / NULLIF(COUNT(*), 0)
        AS users_with_transcription_percent
FROM eligible_users eu
LEFT JOIN users_with_transcription uwt USING (evaluation_id);
