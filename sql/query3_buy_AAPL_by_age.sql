SELECT 
  CASE
    WHEN c.age BETWEEN 10 AND 19 THEN '10대'
    WHEN c.age BETWEEN 20 AND 29 THEN '20대'
    WHEN c.age BETWEEN 30 AND 39 THEN '30대'
    WHEN c.age BETWEEN 40 AND 49 THEN '40대'
    WHEN c.age BETWEEN 50 AND 59 THEN '50대'
    WHEN c.age BETWEEN 60 AND 69 THEN '60대'
    WHEN c.age >= 70 THEN '70대 이상'
    ELSE '미확인'
  END AS age_group,
  COUNT(*) AS total_count
FROM mydataset.trade t
JOIN mydataset.customer c
  ON t.customer_id = c.customer_id
JOIN mydataset.stocks s
  ON t.stock_id = s.stock_id
WHERE s.ticker = 'AAPL'
  AND t.trade_type = '매수'  -- AAPL 종목의 매수 건만 추출
GROUP BY age_group
ORDER BY age_group;
