SELECT COUNT(*) AS over_60_gmail_users
FROM persons_anonymized
WHERE email like '%gmail%' AND age_group IN ('[60-70]', '[70-80]', '[80-90]', '[90-100]');
