-- tenth-user-authentication-date-per-organisation
--
-- required parameters:
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+00')
--
-- event types/external data:
-- USER_FIRST_AUTHENTICATED
--
-- output columns and units:
-- organisation_id: UUID, ID for the organisation
-- organisation_name: text, name of the organisation
-- tenth_user_authenticated_at: timestamptz, timestamp of when the tenth user first authenticated
--
-- inclusion/exclusion rules:
-- authentications before reporting_period_end
-- NULL if fewer than 10 distinct users authenticated before reporting_period_end
--
-- duplicate/retried events:
-- uses the earliest USER_FIRST_AUTHENTICATED event per organisation_id and evaluation_id


WITH first_authenticated_users AS (
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

authenticated_organisations AS (
    SELECT DISTINCT organisation_id
    FROM first_authenticated_users
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
)

SELECT
    ao.organisation_id,
    rau.first_authenticated_at AS tenth_user_authenticated_at
FROM authenticated_organisations ao
LEFT JOIN ranked_authenticated_users rau
  ON rau.organisation_id = ao.organisation_id
 AND rau.authentication_rank = 10
ORDER BY ao.organisation_id;
