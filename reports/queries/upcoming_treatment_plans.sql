SELECT
    client_id,
    client_full_name,
    all_primary_clinicians,
    end_date,
    version_number,
    case_manager_full_name
FROM silver_treatment_plans.treatment_plans
WHERE end_date BETWEEN ? AND ?
ORDER BY
    end_date,
    client_full_name,
    client_id,
    version_number
