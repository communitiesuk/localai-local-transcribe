-- organisation-readiness-to-tenth-authentication-time
--
-- required parameters:
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+00')
-- :ready_dates_json e.g:
--   '[
--     {"organisation_id": "xxx", "ready_at": "2025-01-01 00:00:00+00"},
--     {"organisation_id": "xxx", "ready_at": "2025-01-15 00:00:00+00"}
--   ]' 
--
-- event types/external data:
-- USER_FIRST_AUTHENTICATED
-- external organisation ready dates
--
-- output columns and units:
-- organisation_id: UUID, ID for the organisation
-- organisation_ready_at: timestamptz, external ready timestamp for the organisation
-- tenth_user_authenticated_at: timestamptz, timestamp at which the tenth distinct user first authenticated
-- readiness_to_tenth_authentication_seconds: numeric, seconds between organisation_ready_at and tenth_user_authenticated_at
--
-- inclusion/exclusion rules:
-- NULL if fewer than 10 users authenticated before reporting_period_end
--
-- duplicate/retried events:
-- uses the earliest USER_FIRST_AUTHENTICATED event per organisation_id and evaluation_id


WITH ready_dates AS (
    SELECT
        ready_date.organisation_id::uuid,
        ready_date.ready_at::timestamptz AS organisation_ready_at
    FROM jsonb_to_recordset(CAST(:ready_dates_json AS jsonb))
        AS ready_date(organisation_id text, ready_at text)
),

first_authenticated_users AS (
    SELECT
        organisation_id,
        evaluation_id,
        MIN(occurred_datetime) AS first_authenticated_at
    FROM analytics_event
    WHERE event_type = 'USER_FIRST_AUTHENTICATED'
      AND organisation_id IS NOT NULL
      AND evaluation_id IS NOT NULL
      AND occurred_datetime < :reporting_period_end
    GROUP BY organisation_id, evaluation_id
),

ranked_authenticated_users AS (
    SELECT
        organisation_id,
        evaluation_id,
        first_authenticated_at,
        ROW_NUMBER() OVER (
            PARTITION BY organisation_id
            ORDER BY first_authenticated_at, evaluation_id
        ) AS authentication_rank
    FROM first_authenticated_users
),

tenth_user_authentications AS (
    SELECT
        organisation_id,
        first_authenticated_at AS tenth_user_authenticated_at
    FROM ranked_authenticated_users
    WHERE authentication_rank = 10
)

SELECT
    rd.organisation_id,
    rd.organisation_ready_at,
    tua.tenth_user_authenticated_at,
    EXTRACT(EPOCH FROM (tua.tenth_user_authenticated_at - rd.organisation_ready_at))
        AS readiness_to_tenth_authentication_seconds
FROM ready_dates rd
LEFT JOIN tenth_user_authentications tua USING (organisation_id)
ORDER BY rd.organisation_id;
