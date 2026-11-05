WITH cte_periods AS (
    SELECT
        period::DATE AS period,
        last_day(period)::DATE AS period_end
    FROM generate_series(
        (SELECT date_trunc('month', min(created_time))::DATE FROM bronze.alleva_diagnosis),
        date_trunc('month', current_date)::DATE,
        INTERVAL 1 MONTH
    ) AS calendar(period)
),

cte_diagnoses AS (
    SELECT
        period.period,
        period.period AS period_start,
        period.period_end,
        year(period.period)::INTEGER AS year,
        quarter(period.period)::INTEGER AS quarter,
        month(period.period)::INTEGER AS month,
        diagnosis.system_lead_id AS client_id,
        coalesce(nullif(trim(diagnosis.icd10_code), ''), 'Not Specified') AS diagnosis_code,
        coalesce(nullif(trim(diagnosis.diagnosis), ''), 'Not Specified') AS diagnosis_description,
        diagnosis.created_time,
        diagnosis.deleted_time
    FROM bronze.alleva_diagnosis AS diagnosis
    INNER JOIN cte_periods AS period
        ON diagnosis.created_time < period.period_end + INTERVAL 1 DAY
        AND (
            diagnosis.deleted_time IS NULL
            OR diagnosis.deleted_time >= period.period_end + INTERVAL 1 DAY
        )
    WHERE diagnosis.system_lead_id IS NOT NULL
)

SELECT
    diagnosis.period,
    diagnosis.period_start,
    diagnosis.period_end,
    diagnosis.year,
    diagnosis.quarter,
    diagnosis.month,
    diagnosis.client_id,
    diagnosis.diagnosis_code,
    diagnosis.diagnosis_description,
    demographics.gender,
    demographics.age,
    demographics.age_group,
    demographics.age_group_order
FROM cte_diagnoses AS diagnosis
LEFT JOIN gold_demographics.historical_demographics AS demographics
    ON diagnosis.client_id = demographics.client_id
    AND diagnosis.period = demographics.period
QUALIFY row_number() OVER (
    PARTITION BY diagnosis.period, diagnosis.client_id, diagnosis.diagnosis_code
    ORDER BY diagnosis.created_time DESC, diagnosis.deleted_time DESC NULLS LAST
) = 1
