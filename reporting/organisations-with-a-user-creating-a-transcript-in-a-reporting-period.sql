
-- organisations-with-user-creating-transcript-in-reporting-period
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+00')
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+00')
--
-- event types/external data:
-- USER_FIRST_AUTHENTICATED, USER_DELETED, TRANSCRIPTION_RECEIVED
--
-- output columns and units:
-- eligible_organisation_count: int, organisations with at least one eligible user
-- active_organisation_count: int, eligible organisations with at least one user who had a transcription received 
-- active_organisation_percent: numeric, percentage of eligible organisations with at least one transcription received
--
-- inclusion/exclusion rules:
-- active only inside of the reporting period
--
-- duplicate/retried events:
-- uses the earliest USER_FIRST_AUTHENTICATED/USER_DELETED event per evaluation_id
-- counts each organisation at most once for transcription activity, regardless of duplicate/retried TRANSCRIPTION_RECEIVED events


WITH first_authenticated_users AS (
    SELECT DISTINCT ON (evaluation_id)
        evaluation_id,
        organisation_id,
        occurred_datetime AS first_authenticated_at
    FROM analytics_event
    WHERE event_type = 'USER_FIRST_AUTHENTICATED'
      AND evaluation_id IS NOT NULL
      AND organisation_id IS NOT NULL
    ORDER BY evaluation_id, occurred_datetime
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
        fau.organisation_id
    FROM first_authenticated_users fau
    LEFT JOIN deleted_users du USING (evaluation_id)
    WHERE fau.first_authenticated_at < :reporting_period_end
      AND (du.deleted_at IS NULL OR du.deleted_at > :reporting_period_start)
),

eligible_organisations AS (
    SELECT DISTINCT
        organisation_id
    FROM eligible_users
),

active_organisations AS (
    SELECT DISTINCT
        eu.organisation_id
    FROM eligible_users eu
    INNER JOIN analytics_event ae
        ON ae.event_type = 'TRANSCRIPTION_RECEIVED'
       AND ae.evaluation_id = eu.evaluation_id
       AND ae.occurred_datetime >= :reporting_period_start
       AND ae.occurred_datetime < :reporting_period_end
)

SELECT
    COUNT(eo.organisation_id) AS eligible_organisation_count,
    COUNT(ao.organisation_id) AS active_organisation_count,
    100.0 * COUNT(ao.organisation_id) / NULLIF(COUNT(eo.organisation_id), 0)
        AS active_organisation_percent
FROM eligible_organisations eo
LEFT JOIN active_organisations ao USING (organisation_id);
