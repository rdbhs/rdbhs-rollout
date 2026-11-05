WITH cte_activity AS (
    SELECT DISTINCT
        client_id,
        date_trunc('month', start_date)::DATE AS period
    FROM silver_appointments.client_appointments
    WHERE
        client_id IS NOT NULL
        AND start_date IS NOT NULL
        AND start_date >= '2025-05-01'
        AND start_date <= current_date
),

cte_base AS (
    SELECT
        activity.period,
        activity.period AS period_start,
        last_day(activity.period) AS period_end,
        year(activity.period)::INTEGER AS year,
        quarter(activity.period)::INTEGER AS quarter,
        month(activity.period)::INTEGER AS month,
        activity.client_id,
        client.client_full_name,
        client.date_of_birth,
        date_part('year', age(period_end, client.date_of_birth))::INTEGER AS age,
        client.gender,
        client.ethnicity,
        client.identifies_as,
        client.primary_language,
        client.religion,
        client.postal_code,
        client.city,
        client.state,
        client.country
    FROM cte_activity AS activity
    LEFT JOIN silver_clients.clients AS client ON activity.client_id = client.client_id
)

SELECT
    period,
    period_start,
    period_end,
    year,
    quarter,
    month,
    client_id,
    client_full_name,
    date_of_birth,
    age,
    coalesce(age_groups.age_group, 'Not Specified') AS age_group,
    coalesce(age_groups.sort_order, 9) AS age_group_order,
    coalesce(age_groups.age_group_display, 'Not Specified') AS age_group_display,
    gender,
    ethnicity,
    identifies_as,
    primary_language,
    religion,
    postal_code,
    city,
    state,
    country
FROM cte_base
LEFT JOIN bronze.reference_age_groups AS age_groups
    ON (age_groups.min_age IS NULL OR cte_base.age >= age_groups.min_age)
    AND (age_groups.max_age IS NULL OR cte_base.age <= age_groups.max_age)
