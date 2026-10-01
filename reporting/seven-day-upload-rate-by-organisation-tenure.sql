-- reporting/seven-day-upload-rate-by-organisation-tenure.sql
--
-- required parameters:
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+01')
--
-- event types/external data:
-- AUDIO_UPLOAD_COMPLETED
-- organisation.created_datetime from the organisation table
--
-- output columns and units:
-- organisation_tenure_weeks: int, weeks between organisation creation and reporting_period_end
-- organisation_count: int, organisations in the tenure bucket
-- active_organisation_count: int, organisations in the tenure bucket with at least one completed upload in the previous 7 days
-- seven_day_upload_rate_percent: numeric, percentage of eligible organisations in the bucket with at least one completed upload in the previous 7 days
--
-- inclusion/exclusion rules:
-- includes organisations created before reporting_period_end
--
-- duplicate/retried events:
-- active organisations are counted once per reporting window using DISTINCT organisation_id


WITH eligible_organisations AS (
    SELECT
        id AS organisation_id,
        FLOOR(
            EXTRACT(EPOCH FROM (:reporting_period_end::timestamptz - created_datetime))
            / (7 * 24 * 60 * 60)
        )::int AS organisation_tenure_weeks
    FROM organisation
    WHERE created_datetime < :reporting_period_end
),

active_organisations AS (
    SELECT DISTINCT
        organisation_id
    FROM analytics_event
    WHERE event_type = 'AUDIO_UPLOAD_COMPLETED'
      AND organisation_id IS NOT NULL
      AND occurred_datetime >= (:reporting_period_end::timestamptz - INTERVAL '7 days')
      AND occurred_datetime < :reporting_period_end
)

SELECT
    eo.organisation_tenure_weeks,
    COUNT(*) AS organisation_count,
    COUNT(ao.organisation_id) AS active_organisation_count,
    100.0 * COUNT(ao.organisation_id) / COUNT(*) AS seven_day_upload_rate_percent
FROM eligible_organisations eo
LEFT JOIN active_organisations ao USING (organisation_id)
GROUP BY eo.organisation_tenure_weeks
ORDER BY eo.organisation_tenure_weeks;