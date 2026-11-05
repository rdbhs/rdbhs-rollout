SELECT
    format(
        '{} - {}',
        strftime(start_date, '%b %d, %Y'),
        strftime(end_date, '%b %d, %Y')
    ) AS period,
    start_date,
    end_date,
    payment_date
FROM staging.backoffice_payroll_periods
