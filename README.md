# stocktrading_datamart_pipeline

## 1. 프로젝트 개요

- 주식거래상황을 모델링하여 데이터베이스, 데이터마트를 운영.
- etl되는 데이터에 대한 데이터 퀄리티 체크, 로깅, 모니터링 구성
  - pydeequ를 이용한 데이터 퀄리티 체크
  - spark history server운영, airflow를 통해
- airflow를 통한 주기적인 데이터 최신화, 데이터 퀄리티 체크를 워크플로로 구성
- bigquery를 데이터마트로 운영하고 tableau로 시각화된 BI 제공

![img](/readme_image/architecture.png)

---

## 2. 구현된 기능 및 성과

### 2.1. 데이터 extract

- yfinance api를 통한 24/12/26 ~ 24/12/28까지의 stock 데이터 흭득

| Datetime                  | Close  | High   | Low    | Open   | Volume  | Company | Ticker |
| ------------------------- | ------ | ------ | ------ | ------ | ------- | ------- | ------ |
| 2024-12-26 14:30:00+00:00 | 258.98 | 259.19 | 258.10 | 258.98 | 1052265 | Apple   | AAPL   |
| 2024-12-26 14:31:00+00:00 | 259.39 | 259.65 | 258.85 | 258.89 | 299504  | Apple   | AAPL   |

- chatgpt를 통해 가상의 고객데이터, 계좌데이터, 거래데이터를 생성해 주식거래상황을 모델링

| ID  | 이름   | 성별 | 나이 | 계좌 ID |
| --- | ------ | ---- | ---- | ------- |
| 1   | 김민수 | 남   | 32   | 100001  |
| 2   | 이영희 | 여   | 27   | 100013  |
| 3   | 박성준 | 남   | 41   | 100024  |
| 4   | 최수정 | 여   | 36   | 100035  |
| 5   | 오세훈 | 남   | 28   | 100046  |

- db erd
  ![img](/readme_image/dberd.png)
- 데이터 퀄리티 체크

```
check = (
    check.isComplete("customer_id", hint="No nulls in id")  # id는 null 값이 없어야 함
    .isUnique("customer_id", hint="Unique id")  # id는 유일해야 함
    # id는 정수여야 함
    .hasDataType("customer_id", ConstrainableDataTypes.Integral, hint="id is an integer")

    .isContainedIn("sex", ["남자", "여자"])

    .isComplete("name", hint="No nulls in name")  # name은 null 값이 없어야 함
    # age는 18보다 크고 150보다 작음
    .satisfies("age > 18 and age < 150", constraintName="age is greater than 18")
    .hasDataType("age", ConstrainableDataTypes.Integral, hint="age is an integer")

    .isComplete("budget_id", hint="No nulls in budget_id")
    .isUnique("budget_id", hint="Unique budget_id")  # id는 유일해야 함
    # budget_id는 정수
    .hasDataType("budget_id", ConstrainableDataTypes.Integral, hint="budget_id is an integer")
)
```

![img](/readme_image/verfication.png)

### 2.2. airflow dag 스케쥴링

![img](/readme_image/airflow_log.png)

- airflow를 통한 순차적인 워크플로 실행
- 각 실행에 대한 로그 관리
- 30분 마다 big-query db와의 연동을 진행행

### 2.3. 데이터마트로 작동하는 bigquery와 tableau를 이용한 시각화

> bigquery와 통해 빠르게 쿼리하고 이를 tableau를 통해 간단히 시각화할 수 있다.

- query1_total_orders_by_day

```
SELECT DATE(t.order_datetime) AS trade_date,
       COUNT(*) AS total_orders
FROM mydataset.trade t
GROUP BY DATE(t.order_datetime)
ORDER BY total_orders DESC
```



<img src="/readme_image/query1_total_order_by_day.png" alt="Query1 Total Order by Day" width="300"/>




- [query3_buy_ticker_percentage_by_age.sql](/sql/query3_buy_AAPL_by_age.sql)
<img src="/readme_image/query3_percertage_by_ticker_agegroup.png" alt="Query1 Total Order by Day" width="500"/>


- [query4_verificationResult_budget.sql](/sql/query4_verificationResult_budget.sql)
<img src="/readme_image/query4_verifcationResults.png" alt="Query1 Total Order by Day" width="500"/>


## 3. 트러블 슈팅

### 3.1. airflow 스파크 실행 | 클러스터 매니저 | 해결

_상황_

- airflow 스파크 서브밋 실행
- 스파크 클러스터 매니저 스탠드얼론은 드라이버 모드로 실행이 안됨
- 클라이언트 모드로만 실행가능 하지만 airflow를 워커가 드라이버가 되는 것을 원치 않음

_해결_

- 도커인도커로 spark-master에 들어가서 spark 실행하는 것으로 변경
  - ex) docker exec sparm-master spark-submit --jar ... somePySpark.py
  - 도커 윈도우 데스크탑의 경우 설정에서 Expose daemon on tcp://localhost:2375 without TLS를 체크하는 것으로 도커인도크 사용 가능!

### 3.2. airflow 스파크 실행 | 의존성 | 해결

_상황_

- pyspark 코드 내부 spark session에서 패키지를 설정해두었음에도 spark-submit할때는 패키지 옵션이 적용되지 않는다.
- 대화형노트북과 달리 spark-submit은 제출시에 spark-session이 적용되기 때문이라고 한다.

_해결_

- spark-sumbit에 필요한 패키지를 명시하는 것으로 해결결

### 3.3. pydeequ, airflow | 해결

_상황_

- airflow에서 docker exec로 실행한 spark-submit이 종료되지 않음

_해결_

- pydeequ가 들어간 코드였고 스택오버플로우와 깃허브를 확인해보니, 명시적으로 shutdown hook을 불러와야한다고 함
  - ex) `spark.sparkContext._gateway.shutdown_callback_server()`

### 3.4. big query 커넥터 연결 | 해결

_상황_

- spark bigquery 커넥터를 이용해 df을 bigquery에 전송하던 중 에러발생

_과정_

- 예상되는 원인은 spark 커넥터와 spark간의 버전 불일치였기에 다시 한번 스파크, 스칼라 버전과 패키지의 버전 호환성을 확인했다.
- 하지만 버전 호환성에 문제가 없는 것을 확인했다.
- 디버그를 하기 위해 쥬피터 노트북을 이용해 spark session에도 패키지를 기재하니 문제 없이 실행되었다.
  - 하지만, 같은 코드를 spark-submit에서 실행해보니 같은 에러가 발생했다.
- airflow를 통해 동일한 설정으로 bigquery에 전송을 하였는데, 1번째, 2번째 전송은 성공했으나, 3번째에 다시 에러가 발생했다.
  - 로그를 확인해 보니, 세번째 실행에 다시 패키지를 다운 받아 실행해 패키지 불일치(jar UID 불일치)가 발생하는듯하였다.
- 이를 해결하기 위해 패키지 설정을 통해 임시 폴더에 받은 ~/.ivy2/jars 의 jar 파일을 따로 저장해 수동으로 jar 파일을 사용하는 방식으로 전환
  - 하지만, 이 방법은 jackson 패키지에서 버전 불일치가 발생해 실패했다.

_해결_

- 도커인도커를 사용하는 과정에서 패키지 충돌이 발생하는 것 같으니 bigquery 커넥터를 jar 파일로 다운 받아 추가 jar 파일로 지정해주었다.
- 패키지 설정을 해제하고 jar파일을 연결하니 에러가 발생하지 않았다.

### 3.5. mysql connector driver 문제 | 해결

_상황_

- mysql connector driver를 package로 설정해도 드라이버를 찾지 못 하는 문제가 발생했다.

_해결_

- jar 파일을 다운받아 config에 명시하니 문제가 사라졌다.

### 3.6. pydeeque can't execute ... 'str' 문제 | 해결

_상황_

- pydeeque의 여러 constraints가 실행되지 않는 문제가 발생하였는다.
- constarint message에 위와 같은 에러가 발생하였다.
- pyspark 세션에서는 에러가 발생하지 않고 dataframe을 직접봐야 알 수 있어 디버깅이 늦었다.

_해결_

- 디버깅 결과 hint argument를 (hint=) 지정하지 않아, 문자열이 assert인자로 인식되어 잘못된 함수호출을 하고 있던 것을 확인했다.
- 인자를 제대로 입력해 에러가 해결했다.

### 3.7. pydeeque 전송 실패 | 해결

_상황_

- 잘 실행되던 transfer_db_to_big.py 의 bigquery 전송이 실패했다.
- 다른 파일에서 bigquery 전송은 잘 되는 상황이라 의아했다.

_해결_

- 여러 테이블 중 stock 테이블 전송에서만 에러가 발생하는 것을 확인.
- db의 stock 테이블의 스키마를 변경했었는데, bigquery에는 여전히 이전 스키마가 있어 여기서 충돌이 발생한 것을 확인
- bigquery의 stock테이블을 삭제한 후 재전송하니 잘 실행되는 것을 확인.
