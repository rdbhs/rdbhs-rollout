WITH cte_appointments AS (
    SELECT
        appointment.appointment_id,
        appointment.start_date,
        appointment.start_datetime,
        appointment.end_datetime,
        appointment.appointment_type,
        appointment.service_location,
        appointment.attendance_status,
        appointment.appointment_topic,
        appointment.provider_full_name,
        appointment.provider_email,
        appointment.appointment_minutes,
        appointment.is_deleted,
        appointment.created_time,
        appointment.modified_time,
        appointment.deleted_time,
        appointment.created_time_est,
        appointment.modified_time_est,
        appointment.deleted_time_est,
        appointment.last_timestamp,
        row_number() OVER (
            PARTITION BY appointment.appointment_id, appointment.attendance_status
        ) AS rn
    FROM silver_appointments.client_appointments AS appointment
)

SELECT
    appointment_id,
    start_date,
    start_datetime,
    end_datetime,
    appointment_type,
    service_location,
    attendance_status,
    appointment_topic,
    provider_full_name,
    provider_email,
    appointment_minutes,
    is_deleted,
    created_time,
    modified_time,
    deleted_time,
    created_time_est,
    modified_time_est,
    deleted_time_est,
    last_timestamp
FROM cte_appointments
WHERE rn = 1
