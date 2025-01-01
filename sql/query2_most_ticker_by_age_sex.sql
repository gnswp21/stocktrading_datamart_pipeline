WITH trade_counts AS (
  SELECT
    -- 연령대 분류
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
    c.sex,
    s.ticker,
    COUNT(*) AS trade_count
  FROM mydataset.trade t
  JOIN mydataset.customer c
    ON t.customer_id = c.customer_id
  JOIN mydataset.stocks s
    ON t.stock_id = s.stock_id
  WHERE t.trade_type = '매수'  -- 매수만 집계
  GROUP BY 1, 2, 3
),
ranked AS (
  SELECT
    age_group,
    sex,
    ticker,
    trade_count,
    ROW_NUMBER() OVER (
      PARTITION BY age_group, sex
      ORDER BY trade_count DESC
    ) AS rn
  FROM trade_counts
)
SELECT
  age_group,
  sex,
  ticker,
  trade_count
FROM ranked
WHERE rn = 1  -- 각 (나이대, 성별) 그룹에서 거래 건수가 가장 많은 종목만
ORDER BY age_group, sex;
