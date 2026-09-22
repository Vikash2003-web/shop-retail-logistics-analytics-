-- ============================================================================
-- UAE Retail & Logistics Analytics — Business Queries
-- Each query answers a real question a BA/DA would be asked at an MNC.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1. Monthly Revenue & Order Volume Trend
-- ----------------------------------------------------------------------------
SELECT
    strftime('%Y-%m', o.order_date)              AS order_month,
    COUNT(DISTINCT o.order_id)                    AS total_orders,
    ROUND(SUM(oi.line_total_aed), 2)              AS total_revenue_aed,
    ROUND(SUM(oi.line_total_aed) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value_aed
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY order_month
ORDER BY order_month;


-- ----------------------------------------------------------------------------
-- Q2. Revenue by Emirate (where is the business actually strong?)
-- ----------------------------------------------------------------------------
SELECT
    c.emirate,
    COUNT(DISTINCT o.order_id)          AS orders,
    ROUND(SUM(oi.line_total_aed), 2)    AS revenue_aed,
    ROUND(SUM(oi.line_total_aed) * 100.0 / SUM(SUM(oi.line_total_aed)) OVER (), 2) AS pct_of_total_revenue
FROM orders o
JOIN customers c   ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY c.emirate
ORDER BY revenue_aed DESC;


-- ----------------------------------------------------------------------------
-- Q3. Top Categories by Revenue and Margin Proxy (discount as inverse margin signal)
-- ----------------------------------------------------------------------------
SELECT
    p.category,
    COUNT(*)                              AS units_sold,
    ROUND(SUM(oi.line_total_aed), 2)      AS revenue_aed,
    ROUND(AVG(oi.discount_pct), 2)        AS avg_discount_pct
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY revenue_aed DESC;


-- ----------------------------------------------------------------------------
-- Q4. RFM Customer Segmentation (Recency, Frequency, Monetary)
-- Classic technique for identifying VIP / at-risk / churned customers
-- ----------------------------------------------------------------------------
WITH customer_orders AS (
    SELECT
        o.customer_id,
        MAX(o.order_date)                    AS last_order_date,
        COUNT(DISTINCT o.order_id)            AS frequency,
        SUM(oi.line_total_aed)                AS monetary
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    GROUP BY o.customer_id
),
scored AS (
    SELECT
        customer_id,
        CAST(julianday('2025-12-31') - julianday(last_order_date) AS INTEGER) AS recency_days,
        frequency,
        ROUND(monetary, 2) AS monetary,
        NTILE(4) OVER (ORDER BY julianday(last_order_date) DESC) AS recency_score,
        NTILE(4) OVER (ORDER BY frequency ASC)                   AS frequency_score,
        NTILE(4) OVER (ORDER BY monetary ASC)                    AS monetary_score
    FROM customer_orders
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    (recency_score + frequency_score + monetary_score) AS rfm_total,
    CASE
        WHEN (recency_score + frequency_score + monetary_score) >= 10 THEN 'Champions / VIP'
        WHEN (recency_score + frequency_score + monetary_score) >= 7  THEN 'Loyal Customers'
        WHEN (recency_score + frequency_score + monetary_score) >= 5  THEN 'At Risk'
        ELSE 'Churned / Low Value'
    END AS rfm_segment
FROM scored
ORDER BY rfm_total DESC;


-- ----------------------------------------------------------------------------
-- Q5. Monthly Cohort Retention (signup month -> repeat purchase behavior)
-- ----------------------------------------------------------------------------
WITH first_purchase AS (
    SELECT
        customer_id,
        MIN(strftime('%Y-%m', order_date)) AS cohort_month
    FROM orders
    GROUP BY customer_id
),
orders_with_cohort AS (
    SELECT
        o.customer_id,
        fp.cohort_month,
        strftime('%Y-%m', o.order_date) AS order_month,
        (CAST(strftime('%Y', o.order_date) AS INT) * 12 + CAST(strftime('%m', o.order_date) AS INT))
        - (CAST(substr(fp.cohort_month,1,4) AS INT) * 12 + CAST(substr(fp.cohort_month,6,2) AS INT)) AS month_index
    FROM orders o
    JOIN first_purchase fp ON fp.customer_id = o.customer_id
)
SELECT
    cohort_month,
    month_index,
    COUNT(DISTINCT customer_id) AS active_customers
FROM orders_with_cohort
GROUP BY cohort_month, month_index
ORDER BY cohort_month, month_index;


-- ----------------------------------------------------------------------------
-- Q6. Delivery Performance by Emirate & Courier (logistics KPI)
-- ----------------------------------------------------------------------------
SELECT
    w.emirate,
    d.courier,
    COUNT(*)                                                    AS total_deliveries,
    SUM(CASE WHEN d.on_time = 1 THEN 1 ELSE 0 END)              AS on_time_deliveries,
    ROUND(100.0 * SUM(CASE WHEN d.on_time = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_pct,
    ROUND(AVG(julianday(d.delivery_date) - julianday(d.dispatch_date)), 2)      AS avg_delivery_days
FROM deliveries d
JOIN warehouses w ON w.warehouse_id = d.warehouse_id
WHERE d.delivery_status = 'Delivered'
GROUP BY w.emirate, d.courier
ORDER BY on_time_pct DESC;


-- ----------------------------------------------------------------------------
-- Q7. Supplier Lead Time Impact on Delivery Delays
-- (Does a slow overseas supplier actually cause late deliveries downstream?)
-- ----------------------------------------------------------------------------
SELECT
    s.country                                    AS supplier_country,
    ROUND(AVG(s.avg_lead_time_days), 1)           AS avg_supplier_lead_days,
    COUNT(DISTINCT d.delivery_id)                 AS deliveries,
    ROUND(100.0 * SUM(CASE WHEN d.on_time = 1 THEN 1 ELSE 0 END) / COUNT(DISTINCT d.delivery_id), 2) AS on_time_pct
FROM deliveries d
JOIN orders o        ON o.order_id = d.order_id
JOIN order_items oi  ON oi.order_id = o.order_id
JOIN products p      ON p.product_id = oi.product_id
JOIN suppliers s      ON s.supplier_id = p.supplier_id
WHERE d.delivery_status = 'Delivered'
GROUP BY s.country
ORDER BY on_time_pct ASC;


-- ----------------------------------------------------------------------------
-- Q8. Channel Performance: Online App vs Website vs In-Store
-- ----------------------------------------------------------------------------
SELECT
    o.channel,
    COUNT(DISTINCT o.order_id)                            AS orders,
    ROUND(SUM(oi.line_total_aed), 2)                      AS revenue_aed,
    ROUND(SUM(oi.line_total_aed) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value_aed,
    ROUND(COUNT(DISTINCT o.order_id) * 100.0 / (SELECT COUNT(*) FROM orders), 2) AS pct_of_orders
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY o.channel
ORDER BY revenue_aed DESC;


-- ----------------------------------------------------------------------------
-- Q9. Customer Segment Value (Regular vs Premium vs VIP)
-- ----------------------------------------------------------------------------
SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_id)                          AS customers,
    COUNT(DISTINCT o.order_id)                             AS orders,
    ROUND(SUM(oi.line_total_aed), 2)                       AS revenue_aed,
    ROUND(SUM(oi.line_total_aed) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer_aed
FROM customers c
JOIN orders o        ON o.customer_id = c.customer_id
JOIN order_items oi  ON oi.order_id = o.order_id
GROUP BY c.customer_segment
ORDER BY revenue_per_customer_aed DESC;


-- ----------------------------------------------------------------------------
-- Q10. Top 10 Best-Selling Products
-- ----------------------------------------------------------------------------
SELECT
    p.product_name,
    p.category,
    SUM(oi.quantity)                    AS units_sold,
    ROUND(SUM(oi.line_total_aed), 2)    AS revenue_aed
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id
ORDER BY revenue_aed DESC
LIMIT 10;
