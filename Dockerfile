FROM docker.io/library/python:3.13.3-slim

# 작업디렉토리 설정
WORKDIR /app

# pip 업그레이드
RUN pip install --upgrade pip

# dhapi 설치
RUN pip install dhapi

# returns 설치
RUN pip install returns

# 작업 디렉토리 설정 및 cron 설치
RUN apt-get update && apt-get install -y cron

# 스크립트 파일들 복사
COPY ./scripts/* .

# sh 파일 실행 권한 부여
RUN chmod +x entrypoint.sh
RUN chmod +x run_with_env.sh

# 진입 스크립트 시작
CMD ["/app/entrypoint.sh"]
