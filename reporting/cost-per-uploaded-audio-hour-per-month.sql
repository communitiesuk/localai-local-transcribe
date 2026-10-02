-- cost-per-uploaded-audio-hour-per-month
--
-- required parameters:
-- :reporting_period_start (e.g. '2000-01-01 00:00:00+00'), requires complete months
-- :reporting_period_end (e.g. '2010-01-01 00:00:00+00'), requires complete months
-- :monthly_lt_costs_json e.g:
--   '[
--     {"month": "2025-01-01", "monthly_lt_cost": "1234.56"},
--     {"month": "2025-02-01", "monthly_lt_cost": "2345.67"}
--   ]'
--
-- event types/external data:
-- AUDIO_UPLOAD_COMPLETED
-- external monthly LT costs
--
-- output columns and units:
-- calendar_month: date,
-- monthly_lt_cost: numeric, costs of LT for that month
-- uploaded_audio_hours: numeric, completed audio uploads in hours for that month
-- cost_per_uploaded_audio_hour: numeric, monthly_lt_cost divided by uploaded_audio_hours
--
-- inclusion/exclusion rules:
-- cost per audio hour for months within reporting period
--
-- duplicate/retried events:
-- uses the earliest AUDIO_UPLOAD_COMPLETED event per source_id, including the audio duration from that event

WITH reporting_months AS (
    SELECT
        generate_series(
            date_trunc('month', :reporting_period_start::timestamptz AT TIME ZONE 'UTC'),
            date_trunc('month', (:reporting_period_end::timestamptz - INTERVAL '1 microsecond') AT TIME ZONE 'UTC'),
            INTERVAL '1 month'
        ) AS month_start
),

monthly_lt_costs AS (
    SELECT
        date_trunc('month', monthly_cost.month::date)::date AS calendar_month,
        monthly_cost.monthly_lt_cost::numeric AS monthly_lt_cost
    FROM jsonb_to_recordset(CAST(:monthly_lt_costs_json AS jsonb))
        AS monthly_cost(month text, monthly_lt_cost text)
),

completed_uploads AS (
    SELECT DISTINCT ON (source_id)
        source_id,
        occurred_datetime AS completed_at,
        (event_metadata ->> 'audio_duration_seconds')::numeric AS audio_duration_seconds
    FROM analytics_event
    WHERE event_type = 'AUDIO_UPLOAD_COMPLETED'
      AND source_id IS NOT NULL
      AND event_metadata ? 'audio_duration_seconds'
      AND occurred_datetime < :reporting_period_end
    ORDER BY source_id, occurred_datetime
),

uploaded_audio_hours_per_month AS (
    SELECT
        rm.month_start::date AS calendar_month,
        COALESCE(SUM(cu.audio_duration_seconds), 0) / 3600.0 AS uploaded_audio_hours
    FROM reporting_months rm
    LEFT JOIN completed_uploads cu
        ON cu.completed_at >= GREATEST(rm.month_start AT TIME ZONE 'UTC', :reporting_period_start::timestamptz)
       AND cu.completed_at < LEAST((rm.month_start + INTERVAL '1 month') AT TIME ZONE 'UTC', :reporting_period_end::timestamptz)
    GROUP BY rm.month_start
)

SELECT
    uahpm.calendar_month,
    mlc.monthly_lt_cost,
    uahpm.uploaded_audio_hours,
    mlc.monthly_lt_cost / NULLIF(uahpm.uploaded_audio_hours, 0) AS cost_per_uploaded_audio_hour
FROM uploaded_audio_hours_per_month uahpm
LEFT JOIN monthly_lt_costs mlc USING (calendar_month)
ORDER BY uahpm.calendar_month;
