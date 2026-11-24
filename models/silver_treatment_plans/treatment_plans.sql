WITH case_managers AS (
    SELECT
        system_lead_id,
        STRING_AGG(
            DISTINCT NULLIF(TRIM(case_manager_full_name), ''),
            ', '
            ORDER BY NULLIF(TRIM(case_manager_full_name), '')
        ) AS case_manager_full_name
    FROM bronze.alleva_case_managers_primary_clinicians
    GROUP BY system_lead_id
)

SELECT
    plan.system_lead_id AS client_id,
    plan.full_name AS client_full_name,
    manager.case_manager_full_name,
    plan.all_primary_clinicians,
    plan.end_date,
    plan.length_of_program,
    plan.version_no AS version_number,
    plan.is_active,
    plan.is_complete,
    plan.is_deleted,
    plan.is_client,
    plan.lead_is_deleted,
    plan.lead_status
FROM bronze.alleva_treatment_plans AS plan
LEFT JOIN case_managers AS manager
    ON plan.system_lead_id = manager.system_lead_id
WHERE
    plan.is_client = TRUE
    AND plan.lead_is_deleted = FALSE
    AND plan.lead_status = 'ACTIVE'
    AND plan.is_active = TRUE
    AND plan.is_complete = TRUE
    AND plan.is_deleted = FALSE
