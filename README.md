# stocktrading_datamart_pipeline

dw

주식거래상황을 모델링하여 db, dw를 운영.
etl되는 데이터에 대한 퀄리티 체크, 로깅, 모니터링 구성
dw에서 태블로로 이어지는 bi 제공

airflow 스파크 실행
스탠드얼론은 드라이버 모드로 실행이 안됨
클라이언트 모드로만 실행가능 하지만 에어플로우 워커가 드라이버가 되는 것을 원치 않음
도커인도커로 spark-master에 들어가서 spark 실행하는 것으로 변경

airflow 스파크 실행2
spark session에 패키지를 설정해두었음에도 spark-submit할때는 패키지 옵션이 적용되지 않는다.
대화형노트북과 달리 spark-submit은 제출시에 spark-session이 적용되기 때문이라고 한다.

check 에서
shutdown hook이 안 불러짐
깃허브에서
spark.sparkContext.\_gateway.shutdown_callback_server()

- big query 커넥터 연결(인줄 알았으나, 실은은)
  big-query 커넥터로 연결이 에러가 발생했다. 예상되는 원인은 spark 커넥터와 spark간의 버전 불일치. 하지만 쥬피터노트북에서 버전 호환성을 확인했기에 의문이었다. 여러 시도를 해보는중 spark session에도 패키지를 기재하니 문제 없이 실행되었다.
  spark-default에 패키지 기재
  spark session엔 미기재상태였는데, spark-session에도 패키지명을

# big query 커넥터 연결(인줄 알았으나, 실은 jar 파일 충돌 문제였던것)

위 방법을 통해 해결한줄 알았던 문제는 프로젝트 진행중에 다시 확인했다. gpt에게 로그 파일을 읽혀본 결과 jar UID 불일치가 발생한다고 한다. 실제로 같은 패키지 설정임에도, 문제 없이 실행되다가 어느 기점에서 또 jar 파일을 받더니 에러가 발생했다. jar 파일의 충돌이 발생한 것으로 추측된다. 현재로서는 어떤 설정으로 해결해야할지 감을 잡지 못 해, 사용하는 패키지를 명시한 후 임시 디렉토리인 ~/.ivy2/jars 의 jar 파일을 저장해 수동으로 jar 파일을 사용하는 방식으로 전환하려고 한다.

### mysql connector driver 문제

mysql connector driver를 package로 설정해도 드라이버를 찾지 못 하는 문제가 발생했다. jar 파일을 다운받아 config에 명시하니 문제가 사라졌다.

### pydeeque can't execute ... 'str' 문제

여러 constraints가 실행되지 않는 문제가 발생하였는다. constarint message에 위와 같은 에러가 발생하였다. pyspark 세션에서는 에러가 발생하지 않고 dataframe을 직접봐야 알 수 있어 디버깅이 늦었다. 디버깅 결과 hint argument를 (hint=) 지정하지 않아, 문자열이 assert인자로 인식되어 잘못된 함수호출을 하고 있던 것을 확인했다.
