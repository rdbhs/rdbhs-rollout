SELECT
    client_full_name,
    service_code_group,
    usage,
    usage_unit,
    usage_limit,
    utilization,
    client_id
FROM gold_utilization.utilization
WHERE year = ?
    AND utilization > ?
ORDER BY
    utilization DESC,
    client_full_name,
    service_code_group,
    usage_unit,
    usage_limit,
    payment_basis,
    usage
