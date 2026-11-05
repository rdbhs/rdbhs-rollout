SELECT
    appointments_appointment_id AS appointment_id,
    appointments_start_date AS start_date,
    appointments_start_datetime AS start_datetime,
    appointments_end_datetime AS end_datetime,
    upper(appointments_appointment_type) AS appointment_type,
    appointments_service_location AS service_location,
    upper(appointments_attendance_status) AS attendance_status,
    appointments_appointment_topic AS appointment_topic,
    upper(appointments_appointment_status) AS appointment_status,
    appointments_system_client_id AS system_client_id,
    appointments_system_lead_id AS system_lead_id,
    appointments_full_name AS full_name,
    appointments_user AS user,
    appointments_user_email AS user_email,
    appointments_appointment_minutes AS appointment_minutes,
    appointments_is_deleted AS is_deleted,
    appointments_created_time AS "created_time",
    appointments_modified_time AS "modified_time",
    try_cast(appointments_deleted_time AS DATETIME) AS "deleted_time",
    "created_time" AT TIME ZONE 'America/New_York' AS created_time_est,
    "modified_time" AT TIME ZONE 'America/New_York' AS modified_time_est,
    "deleted_time" AT TIME ZONE 'America/New_York' AS deleted_time_est,
    greatest(
        created_time,
        greatest(
            modified_time,
            deleted_time
        )
    ) AS last_timestamp
FROM staging.alleva_appointments
