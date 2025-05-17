import requests
from bs4 import BeautifulSoup

url = "https://dhlottery.co.kr/common.do?method=main&mainMode=default"
html = requests.get(url).text
soup = BeautifulSoup(html, "lxml")

def last_round():
    last_numb = soup.find(name="strong", attrs={"id": "lottoDrwNo"}).text
    return int(last_numb)

def get_last_lotto_number():
    numbers = []
    for i in range(1, 7):
        number = soup.find(id=f"drwtNo{i}").text
        numbers.append(int(number))
    bonus_number = soup.find(id="bnusNo").text
    numbers.append(int(bonus_number))
    return numbers

def get_lotto_numbers(round_number):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_number}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get('returnValue') == 'success':
            lotto_numbers = [data.get(f'drwtNo{i}') for i in range(1, 7)]
            bonus_number = data.get('bnusNo')
            return lotto_numbers + [bonus_number]
        else:
            return None
    else:
        return None

def main():
    print(last_round())
    print(get_last_lotto_number())

    round_num = 1171
    result = get_lotto_numbers(round_num)
    print(result)  # [3, 6, 7, 11, 12, 17, 19]
if __name__ == '__main__':
    main()