import requests
import random
import time
from datetime import datetime
from bs4 import BeautifulSoup
import sys

# --- 기본 설정 (수정됨) ---
# 갤러리 ID를 'projectnike'로 고정합니다.
GALL_ID = "projectnike"

# 프록시 리스트를 제공된 목록으로 고정합니다.
# 동일한 프록시가 여러 개 있어도 각각 하나의 요청으로 처리됩니다.
PROXY_LIST = [
    "http://8bb8321af8854f27963f__cr.kr:b098b997ccbfe40a@gw.dataimpulse.com:823",
    "http://8bb8321af8854f27963f__cr.kr:b098b997ccbfe40a@gw.dataimpulse.com:823",
    "http://8bb8321af8854f27963f__cr.kr:b098b997ccbfe40a@gw.dataimpulse.com:823",
    "http://8bb8321af8854f27963f__cr.kr:b098b997ccbfe40a@gw.dataimpulse.com:823",
    "http://8bb8321af8854f27963f__cr.kr:b098b997ccbfe40a@gw.dataimpulse.com:823",
    "http://8bb8321af8854f27963f__cr.kr:b098b997ccbfe40a@gw.dataimpulse.com:823",
    "http://8bb8321af8854f27963f__cr.kr:b098b997ccbfe40a@gw.dataimpulse.com:823",
]

# 한 번에 실행할 최대 추천 수를 7로 제한합니다.
RECOMMEND_LIMIT = 7

# --- 기존 핵심 로직 (유지) ---
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 11; SM-G991N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G973N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
]

def dc_recommend(proxy_url, gall_id, post_no):
    """지정된 게시물에 프록시를 통해 추천을 시도하는 함수"""
    post_url = f"https://m.dcinside.com/board/{gall_id}/{post_no}"
    recommend_url = "https://m.dcinside.com/ajax/recommend"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": post_url,
        "Connection": "close"
    }
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        s = requests.Session()
        res_get = s.get(post_url, headers=headers, proxies=proxies, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(res_get.text, 'lxml')
        meta_tag = soup.find("meta", attrs={"name": "csrf-token"})
        if not meta_tag or not meta_tag.get("content"):
            title = soup.find("title")
            return False, f"csrf-token 파싱 실패. TITLE: {title.text if title else 'N/A'}"
        csrf_token = meta_tag.get("content")

        headers["X-CSRF-TOKEN"] = csrf_token
        data = { "type": "recommend_join", "id": gall_id, "no": post_no }
        res_post = s.post(recommend_url, headers=headers, data=data, proxies=proxies, timeout=8)
        
        try:
            if "application/json" in res_post.headers.get("Content-Type", ""):
                resp_json = res_post.json()
            else:
                resp_json = {}
            if resp_json.get('result', False):
                return True, resp_json
            elif res_post.text:
                return False, res_post.text[:120]
            else:
                return False, "추천 실패(응답 없음)"
        except Exception:
            return False, "추천 결과 파싱 오류: " + res_post.text[:120]
    except Exception as e:
        return False, f"예외 발생: {e}"

def main():
    """메인 실행 함수"""
    print("--- DCinside 자동 추천 프로그램 (CLI 버전) ---")
    
    # 글번호 입력받기
    post_no = input("추천할 글번호를 입력하세요: ").strip()
    if not post_no.isdigit():
        print("오류: 글번호는 숫자로만 입력해야 합니다.", file=sys.stderr)
        sys.exit(1)

    # 사용할 프록시 리스트 준비 (최대 7개)
    proxies_to_use = PROXY_LIST[:RECOMMEND_LIMIT]
    random.shuffle(proxies_to_use)
    total = len(proxies_to_use)

    print(f"\n갤러리: {GALL_ID}, 글번호: {post_no}")
    print(f"총 {total}개의 프록시로 추천을 시작합니다.")
    
    success_count = 0
    failure_count = 0

    for idx, proxy_url in enumerate(proxies_to_use, 1):
        now = datetime.now().strftime('%H:%M:%S')
        print(f"[{now}] [{idx:02d}/{total:02d}] 추천 시도 중...", end='\r')
        
        success, msg = dc_recommend(proxy_url, GALL_ID, post_no)
        
        # 줄바꿈으로 이전 줄 덮어쓰기
        print(" " * 50, end='\r') 
        
        if success:
            success_count += 1
            print(f"[{now}] [{idx:02d}/{total:02d}] ✅ 성공 | {msg}")
        else:
            failure_count += 1
            print(f"[{now}] [{idx:02d}/{total:02d}] ❌ 실패 | {msg}")
            
        time.sleep(random.choice([0.1, 0.2, 0.3]))

    print("\n--- 작업 완료 ---")
    print(f"✅ 성공: {success_count}건")
    print(f"❌ 실패: {failure_count}건")

if __name__ == "__main__":
    main()