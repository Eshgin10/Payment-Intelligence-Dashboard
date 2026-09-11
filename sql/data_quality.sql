-- Every violation count should be zero after a successful pipeline run.
SELECT 'duplicate payment IDs' AS check_name, count(*)-count(DISTINCT payment_id) AS violations FROM payments
UNION ALL SELECT 'nonpositive amounts',count(*) FROM payments WHERE amount<=0 OR amount_eur<=0
UNION ALL SELECT 'attempt count mismatch',count(*) FROM payments p WHERE attempt_count<>(SELECT count(*) FROM payment_attempts a WHERE a.payment_id=p.payment_id)
UNION ALL SELECT 'attempt precedes payment',count(*) FROM payment_attempts a JOIN payments p USING(payment_id) WHERE a.attempt_date<p.payment_date
UNION ALL SELECT 'currency mismatch',count(*) FROM payments p JOIN countries c USING(country_code) WHERE p.currency<>c.currency;
