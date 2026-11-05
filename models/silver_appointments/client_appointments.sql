SELECT
    appointment.appointment_id,
    appointment.start_date,
    appointment.start_datetime,
    appointment.end_datetime,
    appointment.appointment_type,
    appointment.service_location,
    appointment.attendance_status,
    appointment.appointment_topic,
    appointment.appointment_status,
    appointment.system_client_id,
    appointment.system_lead_id AS client_id,
    appointment.full_name AS client_full_name,
    appointment.user AS provider_full_name,
    appointment.user_email AS provider_email,
    appointment.appointment_minutes,
    appointment.is_deleted,
    appointment.created_time,
    appointment.modified_time,
    appointment.deleted_time,
    appointment.created_time_est,
    appointment.modified_time_est,
    appointment.deleted_time_est,
    appointment.last_timestamp
FROM bronze.alleva_appointments AS appointment
WHERE
    appointment.appointment_type <> 'STAFF'
    AND appointment.appointment_status = 'COMPLETED'
    AND appointment.is_deleted = FALSE
    AND appointment.attendance_status <> 'DELETED'
