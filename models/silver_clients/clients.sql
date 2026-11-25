WITH cte_clients AS (
    SELECT
        *,
        date_part('year', age(current_date, date_of_birth_date))::INTEGER AS age
    FROM bronze.alleva_leads
    WHERE is_client = TRUE
)

SELECT
    -- Identifiers
    client.system_lead_id AS client_id,
    client.system_client_id AS source_client_id,

    -- Identity
    client.full_name AS client_full_name,
    client.first_name,
    client.middle_name,
    client.last_name,

    -- Demographics
    client.date_of_birth_date AS date_of_birth,
    client.age AS age,
    coalesce(age_groups.age_group, 'Not Specified') AS age_group,
    coalesce(age_groups.sort_order, 9) AS age_group_order,
    coalesce(age_groups.age_group_display, 'Not Specified') AS age_group_display,
    coalesce(client.gender, 'Not Specified') AS gender,
    coalesce(client.ethnicity, 'Not Specified') AS ethnicity,
    client.identifies_as,
    coalesce(client.primary_language, 'Not Specified') AS primary_language,
    client.religion,

    -- Contact and geography
    coalesce(client.postal_code, 'Not Specified') AS postal_code,
    client.address1,
    client.address2,
    client.city,
    client.state,
    client.country,
    client.home_number,
    client.mobile_number,
    client.email_address,

    -- Client lifecycle
    client.status AS client_status,
    client.prospect_status,
    client.admission_date,
    client.discharge_date,
    client.age_at_admission,
    client.count_of_admissions,
    client.level_of_care,
    client.is_discharge,
    client.is_deleted::BOOLEAN AS is_deleted,

    -- Care management
    client.case_manager_name,

    -- Referral
    client.referral_company,
    client.referral_contact,
    client.relation AS referral_relation,

    -- Clinical / admission milestones
    client.completed_bps::BOOLEAN AS has_completed_bps,
    client.bps_created AS bps_completed_date,
    client.completed_face_to_face::BOOLEAN AS has_completed_face_to_face,
    client.completed_hp_tab::BOOLEAN AS has_completed_hp_tab,
    client.completed_nursing_tab::BOOLEAN AS has_completed_nursing_tab,
    client.completed_psych_eval_tab::BOOLEAN AS has_completed_psych_eval_tab,
    client.completed_admission_screen::BOOLEAN AS has_completed_admission_screen,
    client.completed_billing_intake::BOOLEAN AS has_completed_billing_intake,

    -- Operational metadata
    client.created_date,
    client.last_modified_date,
    client.created_time,
    client.last_modified_time,
    client.approved_time,
    client.approved_status,
    client.client_converted_time,
    client.created_by,
    client.time_to_convert,
    client.last_timestamp

FROM cte_clients AS client
LEFT JOIN bronze.reference_age_groups AS age_groups
    ON (age_groups.min_age IS NULL OR client.age >= age_groups.min_age)
    AND (age_groups.max_age IS NULL OR client.age <= age_groups.max_age)
