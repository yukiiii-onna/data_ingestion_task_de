SELECT
  country,
  COUNT(*) AS gmail_user_count,
  DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS rank
FROM persons_anonymized
WHERE email LIKE '%gmail%'
GROUP BY country
QUALIFY rank <= 3;

