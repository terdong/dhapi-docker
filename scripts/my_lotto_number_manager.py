import json

def append_list_with_title(filename, title_number, list_of_lists):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({'title_number': title_number, 'list': list_of_lists})

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

def load_list_with_title(filename, title_number=None):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data:
                return None, None

            if title_number is None:
                # 마지막 항목 반환
                return data[-1]['title_number'], data[-1]['list']
            else:
                # 해당 타이틀넘버를 가진 첫 항목 반환 (여러 개면 첫 번째)
                for entry in data:
                    if entry['title_number'] == title_number:
                        return entry['title_number'], entry['list']
                # 없으면 None 반환
                return None, None
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None

def compare_lists(list1, list2):
    return list1 == list2

def main():
    # 사용 예시
    filename = 'lotto_number_history.json'

    # 데이터 누적 저장
    append_list_with_title(filename, 1132, [[1,3,5,6,7,8],[2,7,14,22,23,24]])
    append_list_with_title(filename, 1172, [[1,2,3,4,5,6]])

    # 마지막 데이터 불러오기 및 비교
    last_title, last_list = load_list_with_title(filename)
    given_list = [[1,2,3,4,5,6]]
    result = compare_lists(last_list, given_list)

    print(f"마지막 타이틀넘버: {last_title}")
    print(f"마지막 리스트: {last_list}")
    print(f"동일한가? {result}")

    last_title2, last_list2 = load_list_with_title(filename)
    print(f"마지막 타이틀넘버: {last_title2}, 리스트: {last_list2}")

    # 특정 타이틀넘버(예: 1132)의 리스트 불러오기
    title, lst = load_list_with_title(filename, 1132)
    print(f"타이틀넘버 1132의 리스트: {lst}")

if __name__ == "__main__":
    main()
