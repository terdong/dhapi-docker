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
import my_lotto_number_manager as my_lotto
import lotto_info_manager as lotto_manager

# "잔액이 부족합니다" 예외 타입
class BalanceInsufficientError(Exception):
    pass

OUTPUT_DIR_PATH="/app/output"
LOTTO_NUMBERS_FILE_PATH = f"{OUTPUT_DIR_PATH}/lotto_number_history.json"

# 메일 알림을 위한 추가 메시지
post_scripts=[]

# 구매한 로또 번호 리스트
purchased_lotto_numbers=[]

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
                            global post_scripts
                            post_scripts.append(f"다음 구매 예정 금액이 부족합니다. 총 예치금: {total_deposit_str} 원, 필요한 금액: {lotto_buy_amount:,} 원")
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
        purchased_lotto_numbers.append([int(x.strip()) for x in lotto_number.split(',')])
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

# 로그파일에 로그 쓰기
def write_log(log_file, log_data):
    now = datetime.datetime.now()
    month = now.strftime("%Y-%m")
    log_entry = f"{now.strftime('%Y-%m-%d %H:%M:%S')} - {log_data}\n"
    with open(f"{OUTPUT_DIR_PATH}/{log_file}", "a") as f:
        f.write(log_entry)

# 로또 당첨 여부 확인
def check_lotto_win(purchased_lotto_numbers: list, winning_lotto_numbers: list) -> int:
    main_numbers = winning_lotto_numbers[:6]  # 당첨 번호 6개
    bonus_number = winning_lotto_numbers[6]   # 보너스 번호(7번째 요소)

    match_count = len(set(purchased_lotto_numbers) & set(main_numbers))  # 일치하는 번호 개수

    if match_count == 6:
        return 1  # 1등
    elif match_count == 5 and bonus_number in purchased_lotto_numbers:
        return 2  # 2등
    elif match_count == 5:
        return 3  # 3등
    elif match_count == 4:
        return 4  # 4등
    elif match_count == 3:
        return 5  # 5등
    else:
        return 0  # 당첨 없음

def convert_fomatted_numbers(numbers):
    return ' '.join(f'{n:02d}' for n in numbers)

# 메인 로직
def main():
    flow_result = flow(
        ["show-balance"],
        run_dhapi_command,
        bind(process_balance),
        bind(process_lotto),
        bind(run_dhapi_command)
    )

    # 지난 로또 결과 확인
    last_round = lotto_manager.last_round()
    (my_last_round, my_last_lottos) = my_lotto.load_list_with_title(LOTTO_NUMBERS_FILE_PATH, last_round)
    if my_last_round == last_round:
        last_week_winning_lotto_number = lotto_manager.get_last_lotto_number()
        result_strings = [f"{last_round}회차 당첨번호는 {convert_fomatted_numbers(last_week_winning_lotto_number[:6])}(보너스번호: {last_week_winning_lotto_number[6]})이며,"]
        for numbers in my_last_lottos:
            result_number = check_lotto_win(numbers, last_week_winning_lotto_number)
            result_strings.append(f"구매한 {convert_fomatted_numbers(numbers)} 의 당첨결과는 \"{str(result_number) + '등' if result_number != 0 else '꽝'}\" 입니다. {'축하합니다!!' if result_number > 0 else ''}")
        post_scripts.append('\n'.join(result_strings))

    # 결과 메일로 전송
    subject, body = process_result(flow_result)
    post_scripts_body = "\n\n" + '\n'.join([f"p.s. {s}" for s in post_scripts])
    total_body = body + post_scripts_body
    mail_result = send_mail(subject, total_body).alt(lambda e: f"메일전송 실패: {str(e)}")

    # 구매한 로또 번호 저장
    if is_successful(flow_result):
        my_lotto.append_list_with_title(LOTTO_NUMBERS_FILE_PATH, last_round+1, purchased_lotto_numbers)

    # 로그데이터 생성
    log_data = (mail_result if not is_successful(mail_result) else flow_result) + post_scripts_body

    # 로그파일 생성 및 쓰기
    log_file = f"lotto_{month}.log"
    write_log(log_file, log_data)

    # 결과 출력 for crontab log
    #print(log_data)

if __name__ == "__main__":
    main()