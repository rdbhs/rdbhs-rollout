WITH cte_diagnoses AS (
    SELECT
        diagnosis.system_lead_id AS client_id,
        coalesce(nullif(trim(diagnosis.icd10_code), ''), 'Not Specified') AS diagnosis_code,
        coalesce(nullif(trim(diagnosis.diagnosis), ''), 'Not Specified') AS diagnosis_description,
        diagnosis.is_primary,
        diagnosis.is_active::BOOLEAN AS is_active,
        diagnosis.is_deleted::BOOLEAN AS is_deleted,
        diagnosis.is_discharge_diagnosis::BOOLEAN AS is_discharge_diagnosis,
        diagnosis.is_rule_out::BOOLEAN AS is_rule_out,
        diagnosis.created_time,
        diagnosis.modified_time,
        diagnosis.deleted_time,
        diagnosis.date_resloved_time,
        diagnosis.priority,
        client.gender,
        client.age,
        client.age_group,
        client.age_group_display,
        client.age_group_order
    FROM bronze.alleva_diagnosis AS diagnosis
    INNER JOIN silver_clients.clients AS client ON diagnosis.system_lead_id = client.client_id
    WHERE diagnosis.system_lead_id IS NOT NULL
),

cte_ranked AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY client_id, diagnosis_code
            ORDER BY
                (coalesce(is_active, FALSE) AND NOT coalesce(is_deleted, FALSE)) DESC,
                created_time DESC NULLS LAST,
                modified_time DESC NULLS LAST,
                deleted_time DESC NULLS LAST
        ) AS row_number
    FROM cte_diagnoses
)

SELECT * EXCLUDE (row_number)
FROM cte_ranked
WHERE row_number = 1
