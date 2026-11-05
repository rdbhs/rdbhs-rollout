WITH cte_diagnoses AS (
    SELECT
        diagnosis_code,
        max(diagnosis_description) AS diagnosis_description,
        count(DISTINCT client_id) AS total_clients
    FROM silver_clients.client_diagnoses
    WHERE
        coalesce(is_active, FALSE)
        AND NOT coalesce(is_deleted, FALSE)
        AND NOT coalesce(is_rule_out, FALSE)
        AND diagnosis_code <> 'Not Specified'
    GROUP BY
        diagnosis_code
),

cte_ranked AS (
    SELECT
        diagnosis_code,
        diagnosis_description,
        total_clients,
        row_number() OVER (
            ORDER BY
                total_clients DESC,
                diagnosis_code
        ) AS diagnosis_rank
    FROM cte_diagnoses
)

SELECT
    diagnosis_code,
    diagnosis_description,
    total_clients,
    diagnosis_rank
FROM cte_ranked
WHERE diagnosis_rank <= 10
