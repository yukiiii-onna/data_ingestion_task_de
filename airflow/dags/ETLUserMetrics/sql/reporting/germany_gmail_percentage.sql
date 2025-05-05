SELECT
  ROUND(
    100.0 * SUM(CASE WHEN country = 'Germany' AND email like '%gmail%' THEN 1 ELSE 0 END) 
    / COUNT(*), 2
  ) AS germany_gmail_percentage
FROM persons_anonymized;
