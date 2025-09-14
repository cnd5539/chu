import asyncio
import dc_api
import os
from datetime import datetime
import random
import itertools

# --- 1. 사용자 설정 ---

# ▼▼▼▼▼ 이곳에 IP:PORT 목록을 그대로 복사-붙여넣기 하세요 ▼▼▼▼▼
raw_proxy_list = """
12aad38ee30b948d905e__cr.kr:8e29ed9ef8bdcb4b@gw.dataimpulse.com:823
"""
# ▲▲▲▲▲ 여기까지 ▲▲▲▲▲

# ▼▼▼▼▼ 작성할 글의 '기본 템플릿'을 이곳에 입력하세요 ▼▼▼▼▼
posts_to_write = [
    {"title": "원신 주년 좆망했네", "content": "zzzz"},
    {"title": "개좆신 노드크라이 쓰레기촌 멸망ㅋㅋ", "content": "ㅋㅋㅋㅋㅋㅋ"},
    {"title": "벽돌견들 6.0 개씹쳐망함ㅋㅋㅋ", "content": "피분수ㅋㅋㅋㅋ"},
]

# --- 봇 설정 (수정 가능) ---
BOARD_ID = 'projectnike'
USERNAME = 'ㅇㅇ'
PASSWORD = '5539'
ARTICLE_INTERVAL = 2  # 글 작성 간격 (초 단위)
MEMORY_PATH = 'Data/'

# --- 핵심 로직 (수정 불필요) ---

# 위 raw_proxy_list를 자동으로 http 포맷으로 변환
PROXY_LIST = [f"http://{line.strip()}" for line in raw_proxy_list.strip().split('\n') if line.strip()]
# '직접 연결' 옵션을 사용하지 않으므로 관련 코드를 제거했습니다.

def save_data(board_id, doc_id, doc_title):
    """글 작성 성공 시 파일에 기록하는 함수"""
    if not os.path.exists(MEMORY_PATH):
        os.makedirs(MEMORY_PATH)
    data_file_path = os.path.join(MEMORY_PATH, "data.txt")
    try:
        with open(data_file_path, 'a', encoding='utf-8') as f:
            f.write(f"갤러리: {board_id}, 글 작성 성공! (ID: {doc_id}) 제목: {doc_title}\n")
        print("-> 작성 기록 저장 완료")
    except Exception as e:
        print(f"-> 데이터 저장 실패: {e}")

async def run_posting_loop():
    """설정에 따라 글 작성을 무한 반복하는 메인 루프"""
    if not PROXY_LIST:
        print("오류: PROXY_LIST가 비어있습니다. raw_proxy_list에 프록시를 추가해주세요.")
        return
        
    print(f"총 {len(PROXY_LIST)}개의 프록시와 {len(posts_to_write)}개의 글 템플릿으로 작성을 시작합니다.")
    print(f"글 작성 간격: {ARTICLE_INTERVAL}초")
    print("=" * 50)
    
    proxy_cycler = itertools.cycle(PROXY_LIST)
    post_cycler = itertools.cycle(posts_to_write)
    
    post_count = 0
    while True:
        current_proxy = next(proxy_cycler)
        base_post = next(post_cycler)
        
        random_number = random.randint(1000, 9999)
        title = f"{base_post['title']} {random_number}"
        content = f"{base_post['content']} {random_number}"
        
        now_str = datetime.now().strftime("%H:%M:%S")
        post_count += 1
        
        print(f"\n--- [{now_str}] {post_count}번째 글 작성 시도 ---")
        print(f"사용 프록시: {current_proxy}")
        print(f"생성된 제목: {title}")

        try:
            async with dc_api.API(proxy=current_proxy, timeout=15) as api:
                doc_id = await api.write_document(
                    board_id=BOARD_ID,
                    title=title,
                    contents=content,
                    name=USERNAME,
                    password=PASSWORD
                )

                if doc_id:
                    print(f"글 작성 성공! (ID: {doc_id})")
                    save_data(BOARD_ID, doc_id, title)
                else:
                    print("글 작성 실패: API에서 문서 ID를 반환하지 않음 (게시판 정책 또는 차단 가능성)")

        except Exception as e:
            print(f"오류 발생: {e}")
            print("-> 다음 프록시로 계속 진행합니다.")

        await asyncio.sleep(ARTICLE_INTERVAL)


# --- 프로그램 실행 ---
if __name__ == "__main__":
    try:
        asyncio.run(run_posting_loop())
    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"\n프로그램 오류: {e}")