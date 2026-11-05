SELECT *
FROM (
    VALUES
    ('H2019', 'H2017-H2019', 'PER_UNIT', 50, 'HOURS', 15),
    ('H2017', 'H2017-H2019', 'PER_UNIT', 50, 'HOURS', 15),
    ('H0036', 'H0036', 'PER_UNIT', 50, 'HOURS', 15),
    ('H2020', 'H2020', 'PER_DIEM', 30, 'DAYS', NULL),
    ('H0036HQ', 'H0036HQ', 'PER_UNIT', 30, 'HOURS', 15),
    ('H2019HQ', 'H2019HQ', 'PER_UNIT', 30, 'HOURS', 15),
    ('H2012', 'H2012', 'PER_UNIT', 50, 'HOURS', 15)
) AS codes (
    service_code,
    service_code_group,
    payment_basis,
    usage_limit,
    usage_unit,
    minutes_per_unit
)
