# dhapi-docker

## 1. About This Program
이 프로그램은 [비공식 동행복권 API](https://github.com/roeniss/dhlottery-api) 를 docker로 실행하기 위한 Dockerfile 입니다.

### 주요기능
1. 매주 일요일 오전 10시에 로또 1장 구매
2. 원하는 로또 번호로 로또 구매 가능
3. 잘못된 로또 번호 혹은 번호 입력 안할 시 랜덤 번호로 구매
4. 잔액부족 혹은 로또 구매 실패 시 알림 메일 발송

## 2. How to Run the Program
### 2.1. docker-compose.yml과 같은 위치에 .env 파일 생성
```
DH_USERNAME=
DH_PASSWORD=
LOTTO_NUMBERS=
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
LOTTO_NUMBERS=1,2,3,4,5,6         # 구매할 로또 번호
SMTP_SERVER=smtp.gmail.com        # SMTP 서버
SMTP_PORT=587                     # SMTP 포트
SMTP_USER=foo@bar.com             # 작성자 이메일 계정
SMTP_PASSWORD=aaaabbbbccccdddd    # Google 앱 비밀번호(문자열 사이에 빈공간 없어야 함 )
EMAIL_TO=bar@for.com              # 보낼 이메일
```
### 2.2. 도커 빌드 및 실행
```sh
# podman-compose 호환
docker-compose build
docker-compose up -d
```

### 2.3. 결과 확인
* 모든 결과는 ./output 에 기록됩니다.
* 만약 에러가 발생된 경우 주어진 이메일 정보로 이메일을 보냅니다.

### 2.4. Custom
* 스케쥴 수정이 필요한 경우 ./scripts/entrypoint.sh 에서 crontab 설정을 변경.
* 로또 커맨드 수정이 필요한 경우 ./scripts/lotto_generator.py의 22번째 줄 확인.
* .env 파일 대신 외부 환경변수를 사용할 경우 --env-file=$ENV_FILE 같은 옵션 사용.
  * 예) podman-compose --env-file=$ENV_FILE up -d