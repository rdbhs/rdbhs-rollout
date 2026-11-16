SELECT
    system_lead_id AS client_id,
    full_name AS  client_full_name,
    all_primary_clinicians,
    end_date,
    length_of_program,
    version_no AS version_number,
    is_active,
    is_complete,
    is_deleted,
    is_client,
    lead_is_deleted,
    lead_status
FROM bronze.alleva_treatment_plans
WHERE
    is_client = TRUE
    AND lead_is_deleted = FALSE
    AND lead_status = 'ACTIVE'
    AND is_active = TRUE
    AND is_complete = TRUE
    AND is_deleted = FALSE
