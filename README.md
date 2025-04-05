# stocktrading_datamart_pipeline

## 프로젝트 개요

주식거래 서비스의 데이터마트 운영을 모델링한 프로젝트입니다. 특히, DB에서 데이터마트로의 전송, 그 과정에서의 정합성 검증이 주요 목표입니다.

<div align="center">
  <img src="/readme_image/architecture.png" alt="img" width="550">
</div>

1. 주식거래서비스를 모델링한 초기 DB 생성
2. 초기 DB(Mysql)에서 데이터 마트(Bigquery)로 주기적 데이터 전송 (By Spark, Airflow)
3. 전송되는 데이터에 대한 데이터 퀄리티 체크, 로깅, 모니터링단 구성
  - pydeequ를 이용한 데이터 퀄리티 체크
  - spark history server운영
  - airflow 통해 주기적인 데이터 마트 최신화
4. Bigquery를 데이터마트로 운영하고 tableau로 시각화된 BI 제공



## 구현된 기능 및 성과

### 데이터 extract

- `yfinance api`를 통한 24/12/26 ~ 24/12/28까지의 stock 데이터 흭득
- chatgpt를 통해 가상의 `customer.csv, budget.csv, trade.csv, stocks.csv` 생성해 주식거래 서비스를 모델링

- db erd
<div align="center">
  <img src="/readme_image/dberd.png" alt="img" width="550">
</div>

### Airflow dag로 관리되는 주요 워크플로
<div align="center">
  <img src="/readme_image/airflow_log.png" alt="img" width="600">
</div>

- **초기 db 생성, db에 저장된 데이터에 대한 퀄리티 검사 후 데이터 마트(Bigquery)로 전송**
- airflow를 통한 순차적인 워크플로 실행
- 각 실행에 대한 로그 관리
- 30분 마다 Bigquery-db간의 연동을 진행


### 데이터 퀄리티 및 정합성 체크
다음처럼 `Pydeequ`를 이용해 `Spark` 기반으로 데이터 퀄리티 및 정합성을 체크합니다.

```
check = (
    # id는 null 값이 없어야 함
    check.isComplete("customer_id", hint="No nulls in id") 
    # id는 유일해야 함
    .isUnique("customer_id", hint="Unique id")  
    # id는 정수여야 함
    .hasDataType("customer_id", ConstrainableDataTypes.Integral, hint="id is an integer")
    # 성별은 남성 혹은 여성
    .isContainedIn("sex", ["남자", "여자"])
    # name은 null 값이 없어야 함
    .isComplete("name", hint="No nulls in name")  
    # age는 18보다 크고 150보다 작음
    .satisfies("age > 18 and age < 150", constraintName="age is greater than 18")
    .hasDataType("age", ConstrainableDataTypes.Integral, hint="age is an integer")
    # budget_id는 null이 없음
    .isComplete("budget_id", hint="No nulls in budget_id")
    # budget_id는 유일해야 함
    .isUnique("budget_id", hint="Unique budget_id")  
    # budget_id는 정수
    .hasDataType("budget_id", ConstrainableDataTypes.Integral, hint="budget_id is an integer")
)
```

<div align="center">
  <img src="/readme_image/verfication.png" alt="img" width="700">
</div>





### 데이터마트로 작동하는 Bigquery와 tableau를 이용한 시각화

`bigquery`를 통해 **빠르게 쿼리**하고 이를 `tableau`를 통해 간단히 시각화할 수 있습니다.

- query1_total_orders_by_day.sql : 날짜별 총 주문의 수

<div align="center">
  <img src="/readme_image/query1_total_order_by_day.png" alt="img" width="200">
</div>

  
```
SELECT DATE(t.order_datetime) AS trade_date,
       COUNT(*) AS total_orders
FROM mydataset.trade t
GROUP BY DATE(t.order_datetime)
ORDER BY total_orders DESC
```




- [query3_buy_ticker_percentage_by_age.sql](/sql/query3_buy_AAPL_by_age.sql) : 나이대별 Apple 종목의 거래 횟수
<div align="center">
  <img src="/readme_image/query3_percertage_by_ticker_agegroup.png" alt="img" width="500">
</div>



- [query4_verificationResult_budget.sql](/sql/query4_verificationResult_budget.sql) : 데이터 퀄리티(constraints) 검증 결과를 조회

<div align="center">
  <img src="/readme_image/query4_verifcationResults.png" alt="img" width="500">
</div>


### 구성

**input :** DB에 저장되는 초기 데이터가 담긴 디렉토리입니다.
- **stock :** `yfinacne.ipynb`를 통해 extract한 주식(ticker) 데이터
- **budget.csv, ./customer.csv, ./stocks.csv, ./trade.csv :**  `chatgpt`를 통해 생성해낸 가상의 고객 데이터


**airflow/dags :** 두가지 dag를 통해 관리되며, `spark-submit`을 실행하는 bash operator로 구성되어 있습니다.
- **init_database_dag.py :** input에 저장된 csv 파일들을 `mysql db에 저장`
- **db_to_dw_dag.py :** mysql에 저장된 table을 `데이터 퀄리티 검증 후 bigquery로 전송`


**jars :** `spark-submit` 에 제출되는 jar 파일, PySpark 애플리케이션
- **constraints :** 각 테이블에 대한 퀄리티 및 정합성 검사 후 검사 결과를 bigquery에 저장하는 코드가 담긴 디렉토리 . `Pydeequ`를 통해 spark 기반으로 검사부터 저장까지 이루어짐
- get_df_profiles.py : 데이터 프로필을 검사 후 저장
- init_db.py : csv 파일을 읽어와 db에 저장하는 spark 코드
- **transfer_db_to_big.py :** db에 저장된 기존 테이블을 dm로 전송하는 spark 코드
- **packages_jars :** spark에 제출하는 mysql, bigquery 용 jar 파일
- spark2big-992917168560.json (git ignored) :  Bigquery credential로 `transfer_db_to_big.py`에 사용

**sql :** `Bigquery`에서 실행되는 sql 쿼리입니다. 
- query_1_... : 날짜별 총 주문의 수
- query_2_... : 나이대, 성별 그룹의 가장 많이 구매된 종목
- query_3_... : 나이대별 Apple 종목의 거래 횟수
- query_4_... : 데이터 퀄리티(constraints) 검증 결과를 조회


**Dockerfile, Dockerfile-airflow :** 각각 spark, airflow를 위한 도커 파일입니다.
**docker-compose.yaml :** 스파크 드라이버, 2개의 스파크 워커, 스파크 히스토리 서버, airflow가 구성된 도커 컴포즈입니다.


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
