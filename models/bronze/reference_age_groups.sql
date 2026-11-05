SELECT
    age_group_id,
    age_group,
    min_age,
    max_age,
    sort_order,
    CASE
        WHEN min_age IS NULL THEN age_group || ' (under ' || (max_age + 1)::VARCHAR || ')'
        WHEN max_age IS NULL THEN min_age::VARCHAR || '+'
        WHEN age_group IN ('Adolescent', 'Young Adult')
            THEN age_group || ' (' || min_age::VARCHAR || '-' || max_age::VARCHAR || ')'
        ELSE min_age::VARCHAR || '-' || max_age::VARCHAR
    END AS age_group_display
FROM (
    VALUES
    (1, 'Child', NULL::INTEGER, 11, 1),
    (2, 'Adolescent', 12, 17, 2),
    (3, 'Young Adult', 18, 24, 3),
    (4, '25-34', 25, 34, 4),
    (5, '35-44', 35, 44, 5),
    (6, '45-54', 45, 54, 6),
    (7, '55-64', 55, 64, 7),
    (8, '65+', 65, NULL::INTEGER, 8)
) AS groups (
    age_group_id,
    age_group,
    min_age,
    max_age,
    sort_order
)
