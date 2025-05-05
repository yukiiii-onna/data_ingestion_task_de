SELECT COUNT(*) as unique_count FROM (
    SELECT DISTINCT country, city, age_group, email
    FROM persons_anonymized
);
