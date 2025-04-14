import os
import sys
import datetime
import random
import subprocess
import re
import smtplib
from email.mime.text import MIMEText
from returns.result import Result, Success, Failure, safe
from returns.pipeline import flow
from returns.pipeline import is_successful
from returns.pointfree import bind
from typing import Union

# "잔액이 부족합니다" 예외 타입
class BalanceInsufficientError(Exception):
    pass

# 메일 알림을 위한 추가 메시지
post_script=""

def get_lotto_buy_count() -> int:
    lotto_buy_count_str = os.getenv("LOTTO_BUY_COUNT")
    if lotto_buy_count_str is None:
        raise ValueError("환경 변수 'LOTTO_BUY_COUNT'가 설정되어 있지 않습니다.")
    return int(lotto_buy_count_str)

@safe(exceptions=(subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception))
def run_dhapi_command(command_list) -> str:
    return subprocess.run(
        ["/usr/local/bin/dhapi"] + command_list,
        capture_output=True,
        text=True,
        check=True,
        timeout=30
    ).stdout

@safe(exceptions=(BalanceInsufficientError, Exception))
def process_balance(result: str) -> str:
    lines = result.splitlines()
    error_msg = "process_balance 파싱 실패"
    # 데이터 행 찾기 (테이블의 두 번째 데이터 행, 보통 │로 시작)
    for line in lines:
        if line.strip().startswith('│'):
            # 첫 번째 열 값 추출
            # │로 시작하고, 값을 공백과 원 단위로 분리
            columns = [col.strip() for col in line.split('│') if col.strip()]
            if columns:  # 비어 있지 않은 경우
                column = columns[0]  # 첫 번째 열 (총예치금)
                # "X 원"에서 숫자만 추출
                match = re.match(r'([\d,]+)\s*원', column)
                if match:
                    total_deposit_str = match.group(1)  # 숫자 부분만
                    total_deposit_num = int(total_deposit_str.replace(',', ''))
                    lotto_buy_amount = get_lotto_buy_count() * 1000
                    if total_deposit_num >= lotto_buy_amount:
                        if total_deposit_num - lotto_buy_amount < lotto_buy_amount:
                            global post_script
                            post_script = f"\n\np.s. 다음 구매 예정 금액이 부족합니다. 총 예치금: {total_deposit_str} 원, 필요한 금액: {lotto_buy_amount:,} 원"
                        return total_deposit_str
                    else:
                        error_msg = f"잔액이 부족합니다. 총 예치금: {total_deposit_str} 원, 필요한 금액: {lotto_buy_amount:,} 원"
                        break
    raise BalanceInsufficientError(error_msg)

@safe
def process_lotto(_:str):
    lotto_buy_count = get_lotto_buy_count()
    lotto_number_list = ["buy-lotto645", "-y"]
    for i in range(lotto_buy_count):
        is_valid = True
        lotto_number_str = os.getenv(f"LOTTO_NUMBER{i+1}")
        # 1. 형식 검증
        if lotto_number_str is None or not re.match(r"^\d+(,\d+)*$", lotto_number_str):
            is_valid = False
        else:
            splited_number = lotto_number_str.split(',')
            # 2. 숫자 범위 및 중복 숫자 검증
            if not (len(splited_number) <= 6 and all((num.isdigit() and 1 <= int(num) <= 45) for num in splited_number)) or len(splited_number) != len(set(splited_number)):
                is_valid = False

        lotto_number = lotto_number_str if is_valid else ",".join(map(str, sorted(random.sample(range(1, 45), 6))))
        lotto_number_list.append(lotto_number)
    # print(f"lotto_buy_count: {lotto_buy_count}\nlotto_number_list: {lotto_number_list}")
    return lotto_number_list

@safe
def send_mail(subject:str, body:str) -> None:
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    EMAIL_TO = os.getenv("EMAIL_TO")

    if SMTP_USER is not None:
        msg = MIMEText(body)
        msg["Subject"] = f"[dhapi] {subject}"
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_TO
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())
    return None

def process_result(result):
    match result:
        case Success(value):
            return ("로또 구매 성공",str(value))
        case Failure(BalanceInsufficientError() as e):
            return ("잔액 부족 알림",str(e))
        case Failure(subprocess.TimeoutExpired() as e):
            return ("Timeout: dhapi 실행 응답을 기다리는 중 시간이 초과되었습니다",str(e))
        case Failure(Exception() as e):
            return ("로또 구매 실패",str(e))

# 메인 로직
def main():
    flow_result = flow(
        ["show-balance"],
        run_dhapi_command,
        bind(process_balance),
        bind(process_lotto),
        bind(run_dhapi_command)
    )
    # 결과 메일로 전송
    subject, body = process_result(flow_result)
    mail_result = send_mail(subject, body+post_script).alt(lambda e: f"메일전송 실패: {str(e)}")

    # 로그데이터 생성
    result = mail_result if not is_successful(mail_result) else flow_result

    # 로그파일 생성
    now = datetime.datetime.now()
    month = now.strftime("%Y-%m")
    log_file = f"lotto_{month}.log"

    # 결과 저장
    log_entry = f"{now.strftime('%Y-%m-%d %H:%M:%S')} - {result}\n"
    with open(f"/app/output/{log_file}", "a") as f:
        f.write(log_entry)

    # 결과 출력 for crontab log
    print(log_entry)

if __name__ == "__main__":
    main()