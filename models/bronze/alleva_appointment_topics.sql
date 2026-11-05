SELECT *
FROM (
    VALUES
    ('TBS Office', 'H2019'),
    ('TBS Service Community', 'H2019'),
    ('PSR Community', 'H2017'),
    ('CPST Individual H0036', 'H0036'),
    ('Day Treatment More than 2.5', 'H2020'),
    ('CPST Group', 'H0036HQ'),
    ('Day Treatment Less than 2.5', 'H2012'),
    ('TBS Group', 'H2019HQ')
) AS codes (
    appointment_topic,
    service_code
)
