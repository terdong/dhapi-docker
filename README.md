# dhapi-docker

## 1. About This Program
이 프로그램은 [비공식 동행복권 API](https://github.com/roeniss/dhlottery-api) 를 docker로 실행하기 위한 Dockerfile 입니다.

### 주요기능
1. 매주 일요일 오전 10시에 자동 로또 구매
2. 원하는 로또 번호로 로또 구매 가능
3. 로또 구매 결과(구매 성공, 구매 실패, 잔액 부족 등등) 알림을 알림 메일 발송(Google 계정만 지원)

## 2. How to Run the Program
### 2.1. docker-compose.yml과 같은 위치에 .env 파일 생성
```
DH_USERNAME=
DH_PASSWORD=
LOTTO_BUY_COUNT=
LOTTO_NUMBER1=
LOTTO_NUMBER2=
LOTTO_NUMBER3=
LOTTO_NUMBER4=
LOTTO_NUMBER5=
SMTP_SERVER=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
EMAIL_TO=
```
예시
```
DH_USERNAME=abcd                  # 동행복권 사이트 아이디
DH_PASSWORD=passwd                # 동행복권 사이트 비밀번호
LOTTO_BUY_COUNT=1                 # 구매 개수(1 ~ 5)
LOTTO_NUMBER1=1,2,3,4,5,6         # 구매할 첫번째 로또 번호
LOTTO_NUMBER2=11,22,33            # 구매할 두번째 로또 번호(부분 번호만 입력 가능)
LOTTO_NUMBER3=                    # 구매할 세번째 로또 번호(입력 안할 시 랜덤 번호 배정)
LOTTO_NUMBER4=                    # 구매할 네번째 로또 번호
LOTTO_NUMBER5=                    # 구매할 다섯번째 로또 번호
SMTP_SERVER=smtp.gmail.com        # SMTP 서버
SMTP_PORT=587                     # SMTP 포트
SMTP_USER=foo@bar.com             # 작성자 이메일 계정(기본적으로 이 부분이 비었으면 메일 발송 안함)
SMTP_PASSWORD=aaaabbbbccccdddd    # Google 앱 비밀번호(**문자열 사이에 빈공간 없어야 함**)
EMAIL_TO=bar@for.com              # 보낼 이메일
```
### 2.2. 도커 빌드 및 실행
docker-compose.yml에 필요한 내용을 기입

```sh
docker-compose build
```
혹은 docker-compose.yml에서 아래와 같이 변경
```yaml
services:
  dhapi-lotto:
    #build:
      #context: .
      #dockerfile: Dockerfile
   image: docker.io/terdong/dhapi-lotto:latest
   restart: unless-stopped #옵션
```
이후 실행
```sh
docker-compose up -d
```

### 2.3. 결과 확인
* 모든 결과는 ./output 에 기록됩니다.
* 또한, 이메일 설정을 한 경우 이메일을 보냅니다.

### 2.4. Custom
* 스케쥴 수정이 필요한 경우 ./scripts/entrypoint.sh 에서 crontab 설정을 변경.
* 로또 커맨드 수정이 필요한 경우 ./scripts/lotto_generator.py 확인.
* .env 파일 대신 외부 환경변수를 사용할 경우 --env-file=$ENV_FILE 같은 옵션 사용.
  * 예) docker-compose --env-file=$ENV_FILE up -d