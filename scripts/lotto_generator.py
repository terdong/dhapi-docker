import os
import sys
import datetime
import random
import subprocess
import smtplib
from email.mime.text import MIMEText

# 외부에서 받은 로또 번호 검증 및 할당
is_valid = False
if len(sys.argv) > 1:
    input_str = sys.argv[1]
    numbers = input_str.split(',')

    if len(numbers) == 6 and all(num.isdigit() for num in numbers):
        is_valid = True
lotto_number = sys.argv[1] if is_valid else ",".join(map(str, random.sample(range(1, 45), 6)))

try:
    # dhapi 명령어 실행, 응답 완료까지 대기
    result = subprocess.run(
        ["/usr/local/bin/dhapi", "buy-lotto645","-y", lotto_number],
        capture_output=True,  # stdout과 stderr 캡처
        text=True,           # 문자열로 출력
        check=True,          # 오류 발생 시 예외抛출
        timeout=30           # 최대 30초 대기 (필요 시 조정)
    ).stdout
except subprocess.TimeoutExpired:
    result = "Timeout: 응답을 기다리는 중 시간이 초과되었습니다."
except subprocess.CalledProcessError as e:
    result = f"Error: {e.stderr}"

# 로그파일 생성
now = datetime.datetime.now()
month = now.strftime("%Y-%m")
log_file = f"lotto_{month}.log"

# 작업 실패 시 에러 원인 이메일로 전송
if "RuntimeError" in result:
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    EMAIL_TO = os.getenv("EMAIL_TO")

    subject = f"로또 구매 실패: {lotto_numbers}\n"
    body = f"dhapi buy-lotto645 실행 중 오류 발생:\n\n{result}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())
    except Exception as e:
        result = result + f"이메일 전송 실패: {e}"

# 결과 저장
log_entry = f"{now.strftime('%Y-%m-%d %H:%M:%S')} - {lotto_numbers} - {result.strip()}\n"
with open(f"/app/output/{log_file}", "a") as f:
    f.write(log_entry)