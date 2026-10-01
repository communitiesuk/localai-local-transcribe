-- median-summaries-per-transcript-and-template
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+01')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- USER_INVITED, USER_FIRST_AUTHENTICATED
--
-- output columns and units:
-- matched_user_count: int, number of users that have been invited
-- median_invitation_to_first_authentication_seconds: int, how long before a user authenticates from first login
--
-- inclusion/exclusion rules:
-- x
--
-- duplicate/retried events:
-- uses the earliest event for USER_INVITED and USER_FIRST_AUTHENTICATED


WITH invited_users AS (
    SELECT
        evaluation_id,
        MIN(occurred_datetime) AS invited_at
    FROM analytics_event
    WHERE event_type = 'USER_INVITED'
      AND evaluation_id IS NOT NULL
    GROUP BY evaluation_id
),

first_authenticated_users AS (
    SELECT
        evaluation_id,
        MIN(occurred_datetime) AS first_authenticated_at
    FROM analytics_event
    WHERE event_type = 'USER_FIRST_AUTHENTICATED'
      AND evaluation_id IS NOT NULL
    GROUP BY evaluation_id
),

matched_users AS (
    SELECT
        EXTRACT(EPOCH FROM (fau.first_authenticated_at - iu.invited_at))
            AS invitation_to_first_authentication_seconds
    FROM first_authenticated_users fau
    INNER JOIN invited_users iu USING (evaluation_id)
    WHERE fau.first_authenticated_at >= :reporting_period_start
      AND fau.first_authenticated_at < :reporting_period_end
)

SELECT
    COUNT(*) AS matched_user_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY invitation_to_first_authentication_seconds) 
        AS median_invitation_to_first_authentication_seconds
FROM matched_users;