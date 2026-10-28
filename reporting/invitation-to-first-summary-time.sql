-- invitation-to-first-summary-time
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+00')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+00')
--
-- event types/external data:
-- USER_INVITED, SUMMARY_RECEIVED
--
-- output columns and units:
-- matched_user_count: int, number of invited users whose first summary was received within the reporting period
-- median_invitation_to_first_summary_received_seconds: numeric, median seconds between invitation and first summary received
--
-- inclusion/exclusion rules:
-- users who have summarised within the reporting period
--
-- duplicate/retried events:
-- uses the earliest event for USER_INVITED and SUMMARY_RECEIVED

WITH invited_users AS (
    SELECT
        evaluation_id,
        MIN(occurred_datetime) AS invited_at
    FROM analytics_event
    WHERE event_type = 'USER_INVITED'
      AND evaluation_id IS NOT NULL
    GROUP BY evaluation_id
),

first_summary_received_users AS (
    SELECT
        evaluation_id,
        MIN(occurred_datetime) AS first_summary_received_at
    FROM analytics_event
    WHERE event_type = 'SUMMARY_RECEIVED'
      AND evaluation_id IS NOT NULL
    GROUP BY evaluation_id
),

matched_users AS (
    SELECT
        EXTRACT(EPOCH FROM (fsru.first_summary_received_at - iu.invited_at))
            AS invitation_to_first_summary_received_seconds
    FROM first_summary_received_users fsru
    INNER JOIN invited_users iu USING (evaluation_id)
    WHERE fsru.first_summary_received_at >= :reporting_period_start
      AND fsru.first_summary_received_at < :reporting_period_end
)

SELECT
    COUNT(*) AS matched_user_count,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY invitation_to_first_summary_received_seconds)
        AS median_invitation_to_first_summary_received_seconds
FROM matched_users;
