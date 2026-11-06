
SELECT
    lead_info_system_leadid AS system_lead_id,
    lead_info_full_name AS full_name,
    lead_info_all_primary_clinicians AS all_primary_clinicians,
    treatment_plans_end_date AS end_date,
    treatment_plans_length_of_program AS length_of_program,
    treatment_plans_version_no AS version_no,
    cast(treatment_plans_is_active AS BOOLEAN) AS is_active,
    cast(treatment_plans_is_complete AS BOOLEAN) AS is_complete,
    cast(treatment_plans_is_deleted AS BOOLEAN) AS is_deleted,
    lead_info_is_client AS is_client,
    cast(lead_info_is_deleted AS BOOLEAN) AS lead_is_deleted,
    upper(lead_info_status) AS lead_status
FROM staging.alleva_treatment_plans
