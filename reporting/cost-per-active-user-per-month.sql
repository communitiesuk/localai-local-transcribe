-- cost-per-active-user-per-month
--
-- required parameters:
-- :reporting_period_start (e.g. '2020-01-01 00:00:00+00'), requires complete months
-- :reporting_period_end (e.g. '2025-01-01 00:00:00+00'), requires complete months
-- :monthly_lt_costs_json e.g:
--   '[
--     {"month": "2025-01-01", "monthly_lt_cost": "1234.56"},
--     {"month": "2025-02-01", "monthly_lt_cost": "2345.67"}
--   ]'
--
-- event types/external data:
-- USER_FIRST_AUTHENTICATED, USER_DELETED
-- external monthly LT costs
--
-- output columns and units:
-- calendar_month: date, first day of the calendar month
-- monthly_lt_cost: numeric, cost of LT for that month
-- active_user_days: int, total user-days in the month where users has authenticated and not been deleted
-- average_active_users: numeric, active_user_days divided by the number of calendar days in the month
-- cost_per_active_user: numeric, monthly_lt_cost divided by average_active_users
--
-- inclusion/exclusion rules:
-- data within reporting period for users not deleted before reporting period end
--
-- duplicate/retried events:
-- uses the earliest USER_FIRST_AUTHENTICATED and earliest USER_DELETED event per evaluation_id


WITH reporting_months AS (
    SELECT
        generate_series(
            date_trunc('month', :reporting_period_start::timestamptz AT TIME ZONE 'UTC'),
            date_trunc('month', (:reporting_period_end::timestamptz - INTERVAL '1 microsecond') AT TIME ZONE 'UTC'),
            INTERVAL '1 month'
        ) AS month_start
),

reporting_days AS (
    SELECT
        rm.month_start,
        generate_series(
            GREATEST(rm.month_start, date_trunc('day', :reporting_period_start::timestamptz AT TIME ZONE 'UTC')),
            LEAST(
                rm.month_start + INTERVAL '1 month',
                date_trunc('day', (:reporting_period_end::timestamptz - INTERVAL '1 microsecond') AT TIME ZONE 'UTC') + INTERVAL '1 day'
            ) - INTERVAL '1 day',
            INTERVAL '1 day'
        ) AS day_start
    FROM reporting_months rm
),

monthly_lt_costs AS (
    SELECT
        date_trunc('month', monthly_cost.month::date)::date AS calendar_month,
        monthly_cost.monthly_lt_cost::numeric AS monthly_lt_cost
    FROM jsonb_to_recordset(CAST(:monthly_lt_costs_json AS jsonb))
        AS monthly_cost(month text, monthly_lt_cost text)
),

first_authenticated_users AS (
    SELECT
        evaluation_id,
        MIN(occurred_datetime) AS first_authenticated_at
    FROM analytics_event
    WHERE event_type = 'USER_FIRST_AUTHENTICATED'
      AND evaluation_id IS NOT NULL
      AND occurred_datetime < :reporting_period_end
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

user_active_periods AS (
    SELECT
        fau.evaluation_id,
        fau.first_authenticated_at,
        COALESCE(du.deleted_at, :reporting_period_end::timestamptz) AS active_until
    FROM first_authenticated_users fau
    LEFT JOIN deleted_users du USING (evaluation_id)
    WHERE fau.first_authenticated_at < COALESCE(du.deleted_at, :reporting_period_end::timestamptz)
),

active_user_days_per_month AS (
    SELECT
        rd.month_start::date AS calendar_month,
        COUNT(uap.evaluation_id) AS active_user_days
    FROM reporting_days rd
    LEFT JOIN user_active_periods uap
        ON uap.first_authenticated_at < ((rd.day_start + INTERVAL '1 day') AT TIME ZONE 'UTC')
       AND uap.active_until > (rd.day_start AT TIME ZONE 'UTC')
    GROUP BY rd.month_start
),

calendar_month_lengths AS (
    SELECT
        rm.month_start::date AS calendar_month,
        EXTRACT(
            DAY FROM (
                rm.month_start + INTERVAL '1 month' - rm.month_start
            )
        )::int AS calendar_days_in_month
    FROM reporting_months rm
)

SELECT
    audpm.calendar_month,
    mlc.monthly_lt_cost,
    audpm.active_user_days,
    audpm.active_user_days::numeric / cml.calendar_days_in_month AS average_active_users,
    mlc.monthly_lt_cost
        / NULLIF(audpm.active_user_days::numeric / cml.calendar_days_in_month, 0)
        AS cost_per_active_user
FROM active_user_days_per_month audpm
INNER JOIN calendar_month_lengths cml USING (calendar_month)
LEFT JOIN monthly_lt_costs mlc USING (calendar_month)
ORDER BY audpm.calendar_month;
