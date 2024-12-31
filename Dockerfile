FROM bitnami/spark:3.5
USER root
# Jupyter 설치
RUN pip3 install pyspark notebook

# 추가 python package
RUN pip install yfinance pydeequ
ENV SPARK_VERSION "3.5"

# 사용자 권한 조정
RUN mkdir -p /home/bitnami/.local/bin && \
    chown -R 1001:1001 /home/bitnami/.local

# 사용자 변경
USER 1001

# PATH 환경 변수 설정
ENV PATH=$PATH:/home/bitnami/.local/bin
ADD config/spark-defaults.conf /opt/bitnami/spark/conf/spark-defaults.conf
