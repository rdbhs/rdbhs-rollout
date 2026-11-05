SELECT
    id,
    effective_from,
    effective_to,
    appointment_cutoff_days,
    appointment_cutoff_time,
    timezone
FROM backoffice_source.public.core_companysettings
