-- Gross settled volume includes subsequently refunded payments; exclude pending from final success denominator.
SELECT * FROM payment_summary;
SELECT * FROM daily_payment_metrics ORDER BY day;
SELECT * FROM country_performance ORDER BY success_rate;
SELECT *,100*failed_value/sum(failed_value) OVER () AS share_of_failed_value FROM failure_analysis ORDER BY failed_value DESC;
SELECT *,100.0*successes/nullif(attempts,0) AS attempt_success_rate FROM retry_performance ORDER BY attempt_number;
SELECT customer_segment, sum(amount_eur) FILTER (WHERE status IN ('successful','recovered','refunded')) AS processed_volume
FROM payment_facts GROUP BY 1 ORDER BY 2 DESC;
-- Week-over-week volume: observed calendar weeks, partial boundary weeks must be interpreted with care.
WITH weekly AS (SELECT date_trunc('week',payment_date) AS week,sum(amount_eur) AS initiated_value FROM payments GROUP BY 1)
SELECT *,100*(initiated_value/nullif(lag(initiated_value) OVER (ORDER BY week),0)-1) AS week_change_pct FROM weekly;
