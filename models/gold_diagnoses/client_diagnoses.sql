SELECT
    diagnosis.client_id,
    diagnosis.diagnosis_code,
    diagnosis.diagnosis_description,
    diagnosis.is_primary,
    diagnosis.is_active,
    diagnosis.is_deleted,
    diagnosis.is_discharge_diagnosis,
    diagnosis.is_rule_out,
    diagnosis.created_time,
    diagnosis.modified_time,
    diagnosis.deleted_time,
    diagnosis.date_resloved_time,
    diagnosis.priority,
    diagnosis.gender,
    diagnosis.age,
    diagnosis.age_group,
    diagnosis.age_group_display,
    diagnosis.age_group_order
FROM silver_clients.client_diagnoses AS diagnosis
INNER JOIN gold_diagnoses.top_diagnoses AS top_10 ON diagnosis.diagnosis_code = top_10.diagnosis_code
