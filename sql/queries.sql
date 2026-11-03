-- Q1: customers with more than 8000 in large completed orders
SELECT customer_id,
       COUNT(*) AS n_orders,
       ROUND(SUM(order_amount), 2) AS total
FROM orders
WHERE status = 'completed' AND order_amount > 500
GROUP BY customer_id
HAVING SUM(order_amount) > 8000
ORDER BY total DESC;