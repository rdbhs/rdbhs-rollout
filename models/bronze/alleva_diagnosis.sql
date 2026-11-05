SELECT
    lead_info_system_leadid AS system_lead_id,
    client_diagnosis_diagnosis AS diagnosis,
    client_diagnosis_is_primary AS is_primary,
    client_diagnosis_icd10_code AS icd10_code,
    client_diagnosis_is_active AS is_active,
    client_diagnosis_is_deleted AS is_deleted,
    client_diagnosis_is_discharge_diagnosis AS is_discharge_diagnosis,
    client_diagnosis_created_time AS created_time,
    client_diagnosis_deleted_time AS deleted_time,
    client_diagnosis_is_rule_out AS is_rule_out,
    client_diagnosis_modified_time AS modified_time,
    client_diagnosis_priority AS priority,
    client_diagnosis_problem AS problem,
    client_diagnosis_problem_group AS problem_group,
    client_diagnosis_reason AS reason,
    client_diagnosis_date_resloved_time AS date_resloved_time,
    greatest(
        client_diagnosis_created_time,
        greatest(
            client_diagnosis_modified_time,
            client_diagnosis_deleted_time
        )
    ) AS last_timestamp
FROM staging.alleva_diagnosis
