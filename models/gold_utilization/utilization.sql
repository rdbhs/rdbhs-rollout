WITH cte_base AS (
    SELECT
        code.service_code_group,
        code.service_code,
        code.payment_basis,
        code.usage_limit,
        code.usage_unit,
        code.minutes_per_unit,
        service.system_lead_id AS client_id,
        service.service_date,
        service.days_or_units,
        CASE
            WHEN code.usage_unit = 'HOURS'
                THEN service.days_or_units * code.minutes_per_unit
        END AS usage_minutes,
        CASE
            WHEN code.usage_unit = 'HOURS'
                THEN service.days_or_units * code.minutes_per_unit / 60.0
            WHEN code.usage_unit = 'DAYS'
                THEN service.days_or_units
        END AS usage
    FROM bronze.alleva_services AS service
    INNER JOIN bronze.alleva_service_codes AS code
        ON service.service_code = code.service_code
    WHERE
        service.service_date >= '2026-07-01'
        AND service.encounter_status = 'SubmittedToClearinghouse'
),

cte_agg AS (
    SELECT
        service_code_group,
        payment_basis,
        usage_limit,
        usage_unit,
        client_id,
        sum(usage) AS usage,
        sum(usage_minutes) AS usage_minutes
    FROM cte_base
    GROUP BY
        service_code_group,
        payment_basis,
        usage_limit,
        usage_unit,
        client_id
),

cte_metrics AS (
    SELECT
        service_code_group,
        payment_basis,
        usage,
        usage_unit,
        usage_limit,
        CASE
            WHEN usage_unit = 'HOURS'
                THEN usage_minutes * INTERVAL '1 minute'
        END AS usage_interval,
        CASE
            WHEN usage_unit = 'HOURS' AND date_part('minute', usage_interval) = 0 THEN
                format(
                    '{:02d} hours',
                    date_part('hour', usage_interval)
                )
            WHEN usage_unit = 'HOURS' THEN
                format(
                    '{:02d} hours, {:02d} minutes',
                    date_part('hour', usage_interval),
                    date_part('minute', usage_interval)
                )
            WHEN usage_unit = 'DAYS' THEN
                usage::INTEGER::VARCHAR || ' days'
        END AS usage_display,
        usage / usage_limit AS utilization,
        client_id
    FROM cte_agg
    WHERE utilization >= 0.3
)

SELECT
    metrics.service_code_group,
    client.client_full_name,
    metrics.payment_basis,
    metrics.usage,
    metrics.usage_unit,
    metrics.usage_limit,
    metrics.usage_interval,
    metrics.usage_display,
    metrics.utilization,
    metrics.client_id
FROM cte_metrics AS metrics
LEFT JOIN silver_clients.clients AS client
    ON metrics.client_id = client.client_id
