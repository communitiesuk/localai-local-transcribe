-- late-invitations-per-organisation
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+01')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- USER_INVITED
--
-- output columns and units:
-- organisation_id: UUID, ID for inviting organisation
-- late_invitation_count: int, number of users invited during the reporting period at least 14 days after the organisation's first invitation
--
-- inclusion/exclusion rules:
-- data within the reporting period
--
-- duplicate/retried events:
-- uses the earliest USER_INVITED event per user


WITH invited_users AS (
    SELECT
        organisation_id,
        evaluation_id,
        MIN(occurred_datetime) AS invited_at
    FROM analytics_event
    WHERE event_type = 'USER_INVITED'
      AND organisation_id IS NOT NULL
      AND evaluation_id IS NOT NULL
      AND occurred_datetime < :reporting_period_end
    GROUP BY organisation_id, evaluation_id
),

first_organisation_invitations AS (
    SELECT
        organisation_id,
        MIN(invited_at) AS first_invited_at
    FROM invited_users
    GROUP BY organisation_id
),

late_invitations AS (
    SELECT
        iu.organisation_id,
        iu.evaluation_id
    FROM invited_users iu
    INNER JOIN first_organisation_invitations foi USING (organisation_id)
    WHERE iu.invited_at >= :reporting_period_start
      AND iu.invited_at < :reporting_period_end
      AND iu.invited_at >= foi.first_invited_at + INTERVAL '14 days'
)

SELECT
    foi.organisation_id,
    COUNT(li.evaluation_id) AS late_invitation_count
FROM first_organisation_invitations foi
LEFT JOIN late_invitations li USING (organisation_id)
GROUP BY foi.organisation_id
ORDER BY foi.organisation_id;
