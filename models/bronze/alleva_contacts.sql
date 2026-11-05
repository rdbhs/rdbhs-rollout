SELECT
    roi_contacts_lead_id AS system_lead_id,
    roi_contacts_name AS name,
    roi_contacts_relationship AS relationship,
    roi_contacts_address1 AS address1,
    roi_contacts_address2 AS address2,
    roi_contacts_postal_code AS postal_code,
    roi_contacts_city AS city,
    roi_contacts_state AS state,
    roi_contacts_home_number AS home_number,
    roi_contacts_mobile AS mobile,
    roi_contacts_is_primary AS is_primary,
    roi_contacts_email_address AS email_address,
    roi_contacts_is_emergency_contact AS is_emergency_contact,
    roi_contacts_is_deleted AS is_deleted,
    roi_contacts_is_roi AS is_roi,
    roi_contacts_note AS note,
    roi_contacts_created_time AS created_time,
    roi_contacts_modified_time AS modified_time,
    roi_contacts_deleted_time AS deleted_time,
    roi_contacts_client_id AS client_id,
    roi_contacts_country AS country,
    roi_contacts_valid_to_time AS valid_to_time,
    roi_contacts_valid_from_time AS valid_from_time,
    roi_contacts_responsibility AS responsibility,
    greatest(
        roi_contacts_created_time,
        greatest(
            roi_contacts_modified_time,
            roi_contacts_deleted_time
        )
    ) AS last_timestamp
FROM staging.alleva_contacts
