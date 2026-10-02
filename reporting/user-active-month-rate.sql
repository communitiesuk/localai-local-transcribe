-- user-active-month-rate
--
-- required parameters:
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- USER_FIRST_AUTHENTICATED, USER_DELETED, TRANSCRIPTION_RECEIVED
--
-- output columns and units:
-- active_month_rate_bucket: numeric, buckets for what percentage of months user has been active for
-- user_count: int, number of users in the active-month rate bucket
--
-- inclusion/exclusion rules:
-- events within reporting perdiod
-- users authenticated and not deleted within reporting period
--
-- duplicate/retried events:
-- uses the earliest USER_FIRST_AUTHENTICATED and earliest USER_DELETED event per evaluation_id
-- any TRANSCRIPTION_RECEIVED event counts towards monthly activity


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
        fau.first_authenticated_at,
        LEAST(
            COALESCE(du.deleted_at, :reporting_period_end::timestamptz),
            :reporting_period_end::timestamptz
        ) AS active_until
    FROM first_authenticated_users fau
    LEFT JOIN deleted_users du USING (evaluation_id)
    WHERE fau.first_authenticated_at < :reporting_period_end
),

user_denominators AS (
    SELECT
        evaluation_id,
        first_authenticated_at,
        active_until,
        (
            (
                EXTRACT(YEAR FROM age(
                    date_trunc('month', active_until - INTERVAL '1 microsecond'),
                    date_trunc('month', first_authenticated_at)
                )) * 12
            )
            + EXTRACT(MONTH FROM age(
                date_trunc('month', active_until - INTERVAL '1 microsecond'),
                date_trunc('month', first_authenticated_at)
            ))
            + 1
        )::int AS calendar_month_count
    FROM eligible_users
    WHERE active_until > first_authenticated_at
),

user_active_months AS (
    SELECT
        ud.evaluation_id,
        COUNT(DISTINCT date_trunc('month', ae.occurred_datetime)) AS active_month_count
    FROM user_denominators ud
    LEFT JOIN analytics_event ae
        ON ae.event_type = 'TRANSCRIPTION_RECEIVED'
       AND ae.evaluation_id = ud.evaluation_id
       AND ae.occurred_datetime >= ud.first_authenticated_at
       AND ae.occurred_datetime < ud.active_until
    GROUP BY ud.evaluation_id
),

user_active_month_rates AS (
    SELECT
        ud.evaluation_id,
        uam.active_month_count,
        ud.calendar_month_count,
        100.0 * uam.active_month_count / ud.calendar_month_count AS active_month_rate_percent
    FROM user_denominators ud
    INNER JOIN user_active_months uam USING (evaluation_id)
)

SELECT
    FLOOR(active_month_rate_percent / 10) * 10 AS active_month_rate_bucket,
    COUNT(*) AS user_count
FROM user_active_month_rates
GROUP BY active_month_rate_bucket
ORDER BY active_month_rate_bucket;
