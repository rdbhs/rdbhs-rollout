WITH cte_pivot AS (
    PIVOT (
        SELECT
            calendar.start_date,
            calendar.end_date,
            calendar.period,
            productivity.provider_full_name,
            productivity.provider_email,
            productivity.attendance_status,
            productivity.appointment_minutes
        FROM silver_appointments.provider_appointments AS productivity
        LEFT JOIN bronze.backoffice_payroll_periods AS calendar
            ON productivity.start_date >= calendar.start_date
            AND productivity.start_date <= calendar.end_date
        WHERE
            nullif(trim(productivity.provider_full_name), '') IS NOT NULL
            AND attendance_status IN ('ATTENDED')
    )
    ON attendance_status
    USING coalesce(sum(appointment_minutes), 0)
    GROUP BY
        start_date,
        end_date,
        period,
        provider_full_name,
        provider_email
),

cte_result AS (
    SELECT
        start_date,
        end_date,
        period,
        provider_full_name,
        provider_email,
        ATTENDED AS "attended_minutes",
        "attended_minutes" * INTERVAL '1 minute' AS "attended_interval",
        format(
            '{:02d}:{:02d}:{:02d}',
            date_part('hour', "attended_interval"),
            date_part('minute', "attended_interval"),
            date_part('second', "attended_interval")
        ) AS "attended"
    FROM cte_pivot
)

SELECT
    start_date,
    end_date,
    period,
    provider_full_name,
    provider_email,
    attended,
    attended_minutes
FROM cte_result
