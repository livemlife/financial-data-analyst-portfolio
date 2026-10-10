-- Customer profitability and retention mart.
-- Demonstrates CTEs, conditional aggregation, joins and NTILE window functions.
WITH history AS (
    SELECT
        customer_id,
        AVG(transaction_count) AS avg_monthly_transactions,
        AVG(deposit_balance_jpy) AS avg_deposit_balance_jpy,
        SUM(fee_revenue_jpy + interest_revenue_jpy) AS annualized_revenue_jpy,
        SUM(service_cost_jpy + rewards_cost_jpy + expected_credit_loss_jpy) AS annualized_cost_jpy,
        SUM(complaint_count) AS complaint_count,
        AVG(digital_login_count) AS avg_digital_logins,
        AVG(CASE WHEN month_no BETWEEN 1 AND 3 THEN transaction_count END) AS txn_first_3m,
        AVG(CASE WHEN month_no BETWEEN 9 AND 11 THEN transaction_count END) AS txn_last_3m
    FROM monthly_activity
    WHERE month_no <= 11
    GROUP BY customer_id
),
target AS (
    SELECT customer_id, CASE WHEN active_flag = 0 THEN 1 ELSE 0 END AS churned
    FROM monthly_activity
    WHERE month_no = 12
),
base AS (
    SELECT
        p.customer_id,
        p.age_band,
        p.region,
        p.tenure_years,
        p.primary_channel,
        h.*,
        (h.annualized_revenue_jpy - h.annualized_cost_jpy) AS contribution_margin_jpy,
        (h.txn_last_3m - h.txn_first_3m) / NULLIF(h.txn_first_3m, 0) AS transaction_trend,
        t.churned
    FROM customer_profile p
    JOIN history h USING (customer_id)
    JOIN target t USING (customer_id)
)
SELECT
    *,
    NTILE(5) OVER (ORDER BY contribution_margin_jpy DESC) AS profitability_rank
FROM base;

