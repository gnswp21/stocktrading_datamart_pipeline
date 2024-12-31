SELECT DATE(t.order_datetime) AS trade_date,
       COUNT(*) AS total_orders
FROM mydataset.trade t
GROUP BY DATE(t.order_datetime)
ORDER BY total_orders DESC