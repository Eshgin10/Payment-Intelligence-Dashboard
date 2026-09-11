CREATE OR REPLACE VIEW payment_facts AS
SELECT p.*, c.customer_name, c.customer_segment, c.risk_level, co.country_name,
 m.name AS payment_method, me.merchant_name, f.name AS failure_reason,
 fi.name AS initial_failure_reason
FROM payments p JOIN customers c USING(customer_id) JOIN countries co ON p.country_code=co.country_code
JOIN payment_methods m USING(payment_method_id) JOIN merchants me USING(merchant_id)
LEFT JOIN failure_reasons f ON p.failure_reason_id=f.failure_reason_id
LEFT JOIN failure_reasons fi ON p.initial_failure_reason_id=fi.failure_reason_id;

CREATE OR REPLACE VIEW payment_summary AS
SELECT count(*) AS total_payments,
 coalesce(sum(amount_eur) FILTER (WHERE status IN ('successful','recovered','refunded')),0) AS processed_volume,
 100.0 * count(*) FILTER (WHERE status IN ('successful','recovered','refunded')) / nullif(count(*) FILTER (WHERE status <> 'pending'),0) AS success_rate,
 coalesce(sum(amount_eur) FILTER (WHERE status='failed'),0) AS failed_value,
 coalesce(sum(amount_eur) FILTER (WHERE status='recovered'),0) AS recovered_value
FROM payments;

CREATE OR REPLACE VIEW daily_payment_metrics AS
SELECT (payment_date AT TIME ZONE 'UTC')::date AS day, count(*) AS payments,
 coalesce(sum(amount_eur) FILTER (WHERE status IN ('successful','recovered','refunded')),0) AS processed_volume,
 coalesce(sum(amount_eur) FILTER (WHERE status='failed'),0) AS failed_value
FROM payments GROUP BY 1;

CREATE OR REPLACE VIEW country_performance AS
SELECT country_code,country_name,count(*) AS payments,
 100.0 * count(*) FILTER (WHERE status IN ('successful','recovered','refunded')) / nullif(count(*) FILTER (WHERE status<>'pending'),0) AS success_rate,
 sum(amount_eur) AS initiated_value FROM payment_facts GROUP BY 1,2;

CREATE OR REPLACE VIEW failure_analysis AS
SELECT failure_reason, count(*) AS payments, sum(amount_eur) AS failed_value
FROM payment_facts WHERE status='failed' GROUP BY 1;

CREATE OR REPLACE VIEW retry_performance AS
SELECT a.attempt_number, count(*) AS attempts,
 count(*) FILTER (WHERE a.status='successful') AS successes,
 coalesce(sum(p.amount_eur) FILTER (WHERE a.status='successful' AND a.attempt_number>1),0) AS recovered_value
FROM payment_attempts a JOIN payments p USING(payment_id) GROUP BY 1;
