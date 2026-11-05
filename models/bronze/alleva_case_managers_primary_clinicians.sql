SELECT
    lead_info_system_leadid AS system_lead_id,
    lead_info_full_name AS client_full_name,
    lead_info_case_manager_name AS case_manager_full_name,
    lead_info_primary_clinician AS primary_clinicia_full_name,
    lead_info_is_client AS is_client,
    lead_info_status AS status
FROM staging.alleva_case_managers_primary_clinicians
