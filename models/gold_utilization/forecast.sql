WITH cte_base AS (
    SELECT DISTINCT
        productivity.appointment_id,
        productivity.start_date,
        productivity.client_full_name,
        productivity.appointment_type,
        productivity.appointment_topic,
        productivity.appointment_minutes,
        topic.service_code,
        code.service_code_group,
        code.payment_basis,
        code.usage_unit,
        code.usage_limit
    FROM silver_appointments.client_appointments AS productivity
    INNER JOIN bronze.alleva_appointment_topics AS topic
        ON productivity.appointment_topic = topic.appointment_topic
    INNER JOIN bronze.alleva_service_codes AS code
        ON topic.service_code = code.service_code
    WHERE
        productivity.start_date >= '2026-07-01'
        AND productivity.attendance_status = 'ATTENDED'
),

cte_agg AS (
    SELECT
        service_code_group,
        client_full_name,
        payment_basis,
        usage_unit,
        usage_limit,
        appointment_type,
        service_code,
        appointment_topic,
        count(DISTINCT appointment_id) AS total_appointments,
        count(DISTINCT start_date) AS total_days,
        sum(appointment_minutes) AS total_minutes
    FROM cte_base
    GROUP BY
        service_code_group,
        client_full_name,
        payment_basis,
        usage_unit,
        usage_limit,
        appointment_type,
        service_code,
        appointment_topic
)

SELECT
    service_code_group,
    client_full_name,
    payment_basis,
    usage_unit,
    usage_limit,
    appointment_type,
    service_code,
    appointment_topic,
    total_appointments,
    total_minutes,
    total_minutes * INTERVAL '1 minute' AS usage_forecast_interval,
    CASE
        WHEN usage_unit = 'HOURS'
            THEN total_minutes / 60.0
        WHEN usage_unit = 'DAYS'
            THEN total_days
    END AS usage_forecast,
    CASE
        WHEN usage_unit = 'HOURS' AND date_part('minute', usage_forecast_interval) = 0 THEN
            format(
                '{:02d} hours',
                date_part('hour', usage_forecast_interval)
            )
        WHEN usage_unit = 'HOURS' THEN
            format(
                '{:02d} hours, {:02d} minutes',
                date_part('hour', usage_forecast_interval),
                date_part('minute', usage_forecast_interval)
            )
        WHEN usage_unit = 'DAYS' THEN
            usage_forecast::INTEGER::VARCHAR || ' days'
    END AS usage_forecast_display,
    CASE
        WHEN usage_unit = 'HOURS'
            THEN (total_minutes / 60.0) / usage_limit
        WHEN usage_unit = 'DAYS'
            THEN total_days::DOUBLE / usage_limit
    END AS utilization_forecast
FROM cte_agg
WHERE utilization_forecast >= 0.3
