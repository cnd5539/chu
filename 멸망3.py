import asyncio
import dc_api
import os
from datetime import datetime
import random
import itertools

# --- 1. 사용자 설정 ---

# ▼▼▼▼▼ 이곳에 IP:PORT 목록을 그대로 복사-붙여넣기 하세요 ▼▼▼▼▼
raw_proxy_list = """
115.144.43.155:5259
115.144.4.78:5389
121.126.204.247:5715
124.198.49.144:6095
115.144.91.207:5533
49.254.1.218:5178
49.254.122.8:5624
115.144.30.39:5358
121.126.89.32:5912
125.7.143.152:6294
115.144.184.139:5180
121.126.38.24:5792
121.126.129.148:5252
49.254.213.11:6760
183.78.134.74:6367
124.198.29.12:6035
121.126.38.28:5796
49.254.97.52:7036
115.144.195.132:5228
115.144.52.9:5621
203.109.9.7:6450
203.109.9.5:6448
49.254.186.135:6661
121.126.92.193:5241
115.144.148.88:5200
115.144.4.76:5387
115.144.133.167:5056
115.144.117.247:5024
121.126.48.214:5846
121.126.170.68:5680
49.254.152.238:6589
121.126.129.147:5251
"""
# ▲▲▲▲▲ 여기까지 ▲▲▲▲▲

# ▼▼▼▼▼ 작성할 글의 '기본 템플릿'을 이곳에 입력하세요 ▼▼▼▼▼
posts_to_write = [
    {"title": "노드크라이 오픈과 원신 주년이 동시에 망했네", "content": "ㅋㅋ ㅁㅇㅇㅇ"},
    {"title": "노드크라이 오픈도 망하고 원신 주년도 망하고", "content": "ㅈ망했네 ㅋㅋ"},
    {"title": "노드크라이 오픈일이 원신 주년인데 둘 다 망한 거 실화냐", "content": "진짜임?"},
    {"title": "노드크라이 오픈 기념 원신 주년 멸망 파티", "content": "파티 시작!"},
    {"title": "원신 주년 망한 거 노드크라이 오픈 탓이었음", "content": "진짜였네"},
    {"title": "노드크라이가 오픈하자마자 망해서 원신 주년도 망한 듯", "content": "그럴 줄 알았다"},
    {"title": "노드크라이 오픈은 망하고 원신 주년은 더 망했다", "content": "둘 다 망했네"},
    {"title": "원신 주년 보니까 노드크라이 오픈이 선녀였음", "content": "갓겜이네"},
    {"title": "노드크라이 오픈 망해서 원신 주년 유저 다 돌아옴", "content": "ㅋㅋㅋㅋㅋ"},
    {"title": "노드크라이 오픈과 원신 주년의 멸망 콜라보", "content": "와 콜라보"},
    {"title": "노드크라이 오픈 망한 게 원신 주년 때문이라고?", "content": "이게 말이되나"},
    {"title": "원신 주년 망한 거 보니까 노드크라이 오픈 생각나네", "content": "그때 생각나네"},
    {"title": "노드크라이 오픈 날에 원신 주년 망했다는 소문이 돔", "content": "소문이 사실"},
    {"title": "노드크라이 오픈 망한 거 원신 주년에 묻어가려 했네", "content": "뻔했네"},
    {"title": "원신 주년이라 좋아했는데 노드크라이 오픈이 망해서 현타옴", "content": "현타 제대로"},
    {"title": "노드크라이 오픈하고 원신 주년 떡락 가나", "content": "떡락 확정"},
    {"title": "원신 주년 망하고 노드크라이 오픈도 망했다", "content": "쌍으로 망함"},
    {"title": "노드크라이 오픈하고 원신 주년 파티 망했음", "content": "파티 망함"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 섭섭함", "content": "아쉽다"},
    {"title": "노드크라이 오픈 망했으니 원신 주년에도 할 게 없다", "content": "할 거 없네"},
    {"title": "노드크라이 오픈 망해서 원신 주년이 더 돋보인다", "content": "더 좋아보여"},
    {"title": "원신 주년인데 노드크라이 오픈이 망해서 기분 좋음", "content": "기분좋다"},
    {"title": "노드크라이 오픈과 원신 주년이 쌍으로 망했다", "content": "진짜 망했다"},
    {"title": "원신 주년 망해서 노드크라이 오픈으로 갈아탔는데 거기도 망했네", "content": "운도 없네"},
    {"title": "노드크라이 오픈 망하고 원신 주년까지 멸망", "content": "싹 다 망함"},
    {"title": "원신 주년과 노드크라이 오픈, 둘 다 망했으니 이제 겜 접음", "content": "겜 접자"},
    {"title": "노드크라이 오픈 망해서 원신 주년에도 불타는 중", "content": "불타는 중"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 웃음벨이네", "content": "웃음벨"},
    {"title": "노드크라이 오픈이 망하니 원신 주년도 망할 듯", "content": "다음은 원신"},
    {"title": "원신 주년 망한 거 노드크라이 오픈 때문이라고 우기는 중", "content": "억지 부리지마"},
    {"title": "노드크라이 오픈은 망했는데 원신 주년은 멀쩡함", "content": "그나마 다행"},
    {"title": "원신 주년 보상 보니까 노드크라이 오픈이 더 나았다", "content": "오픈이 낫네"},
    {"title": "노드크라이 오픈 망한 기념 원신 주년 복귀각", "content": "복귀한다"},
    {"title": "원신 주년인데 노드크라이 오픈이 왜 망했냐고", "content": "궁금하다"},
    {"title": "노드크라이 오픈 망해서 원신 주년 이벤트에 집중함", "content": "이벤트만 한다"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 갤러리 멸망", "content": "갤러리 망함"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년은 성공하겠지", "content": "성공하겠지"},
    {"title": "원신 주년인데 노드크라이 오픈이 망해서 할 얘기가 많다", "content": "할 얘기 많다"},
    {"title": "노드크라이 오픈 망한 거 원신 주년에 묻고 가자", "content": "묻고 가자"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 다행이다", "content": "다행이다"},
    {"title": "노드크라이 오픈이 망해서 원신 주년도 폭망", "content": "폭망했다"},
    {"title": "원신 주년인데 노드크라이 오픈이 망해서 기분 묘하다", "content": "기분이 묘하네"},
    {"title": "노드크라이 오픈 망했으니 원신 주년이나 즐겨라", "content": "이거나 즐기자"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 멘탈 나감", "content": "멘탈 나감"},
    {"title": "노드크라이 오픈 망한 거 원신 주년에 터뜨리자", "content": "터뜨려 버리자"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 짜증남", "content": "짜증난다"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년은 그냥 축제지", "content": "축제다 축제"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 할 얘기가 없네", "content": "할 말이 없네"},
    {"title": "노드크라이 오픈 망했으니 원신 주년이나 즐겨라", "content": "즐기러 간다"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 섭섭하다", "content": "섭섭하다"},
    {"title": "노드크라이 오픈 망한 거 원신 주년 때문이었다", "content": "네탓이야"},
    {"title": "원신 주년과 노드크라이 오픈, 둘 중 뭐가 더 망했나", "content": "승자는 누구"},
    {"title": "노드크라이 오픈 망해서 원신 주년에도 불타는 중", "content": "활활 불탄다"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 눈물난다", "content": "눈물나"},
    {"title": "노드크라이 오픈 망한 거 원신 주년에 누가 그랬냐", "content": "누가 그랬어"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 기분 꿀꿀함", "content": "꿀꿀해"},
    {"title": "노드크라이 오픈 망했다고 해서 원신 주년에 돌아왔다", "content": "복귀했다"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 울고 싶다", "content": "울고싶다"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년은 더 성공적일 것", "content": "성공각"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 웃겨 죽겠네", "content": "웃겨 죽겠다"},
    {"title": "노드크라이 오픈 망했으니 원신 주년은 대박일 것", "content": "대박일 듯"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 할 말 없음", "content": "할 말 없음"},
    {"title": "노드크라이 오픈 망한 기념으로 원신 주년 파티 가자", "content": "파티 간다"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 웃음밖에 안 나옴", "content": "웃음만 나와"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년에는 더 좋은 보상 줘야 함", "content": "보상 더줘"},
    {"title": "원신 주년인데 노드크라이 오픈 망했다는 소식 듣고 옴", "content": "소식 듣고옴"},
    {"title": "노드크라이 오픈 망하고 원신 주년은 전성기 맞을 듯", "content": "전성기 시작"},
    {"title": "원신 주년인데 노드크라이 오픈 망한 거 축하함", "content": "축하해"},
    {"title": "노드크라이 오픈 망해서 원신 주년 이벤트에 집중함", "content": "이벤트만 하자"},
    {"title": "원신 주년인데 노드크라이는 왜 망한 거냐", "content": "왜 망했냐"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년은 더 성공하겠지", "content": "더 성공할 듯"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 할 얘기가 많다", "content": "할말이 많아"},
    {"title": "노드크라이 오픈 망한 거 보니 원신 주년도 오래 못 갈 듯", "content": "곧 망할 듯"},
    {"title": "원신 주년인데 노드크라이 오픈 망한 거 실화냐", "content": "이거 실화임?"},
    {"title": "노드크라이 오픈 망한 기념 원신 주년 복귀각", "content": "복귀각 잡는다"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 갤러리 멸망", "content": "갤러리 멸망"},
    {"title": "노드크라이 오픈 망해서 원신 주년에도 불타는 중", "content": "불타는 중"},
    {"title": "원신 주년인데 노드크라이 오픈 망했다고 누가 그랬냐", "content": "누가 말했어"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년에는 좋은 일만 있을 듯", "content": "좋은 일만"},
    {"title": "원신 주년인데 노드크라이 오픈이 망해서 슬픔", "content": "슬프다"},
    {"title": "노드크라이 멸망 원신 주년 파티", "content": "멸망 파티"},
    {"title": "노드크라이 오픈이 망하고 원신 주년이 왔다", "content": "왔다"},
    {"title": "원신 주년 축하 겸 노드크라이 오픈 멸망 파티", "content": "멸망 파티"},
    {"title": "노드크라이 오픈 망했으니 이제 원신 주년이나 보자", "content": "이제 보자"},
    {"title": "원신 주년인데 노드크라이 오픈 망한 거 왜 아무도 말 안 해줌?", "content": "왜 말 안해줘"},
    {"title": "노드크라이 오픈 망한 거 원신 주년 때문임", "content": "니탓이야"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 할 말 없음", "content": "할말 없다"},
    {"title": "노드크라이 오픈 망했으니 원신 주년은 대박날 것", "content": "대박 날 것"},
    {"title": "원신 주년인데 노드크라이 오픈 망했다는 거 팩트임?", "content": "팩트 체크"},
    {"title": "노드크라이 오픈 망해서 원신 주년 이벤트만 기다림", "content": "이벤트 기다려"},
    {"title": "원신 주년인데 노드크라이는 왜 망했냐고", "content": "대체 왜"},
    {"title": "노드크라이 오픈 망한 거 원신 주년에 묻고 가자", "content": "묻고 가자"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 다행이다", "content": "다행이다"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년은 평화롭겠지", "content": "평화롭겠지"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 잠 못 잠", "content": "잠 못자"},
    {"title": "노드크라이 오픈 망한 거 원신 주년 이벤트로 잊자", "content": "잊자"},
    {"title": "원신 주년인데 노드크라이 오픈 망해서 웃음벨이네", "content": "웃음벨"},
    {"title": "노드크라이 오픈 망했으니 원신 주년에는 갓겜 소리 듣자", "content": "갓겜 소리"},
    {"title": "원신 주년인데 노드크라이 오픈 망했다는 거 믿기 싫다", "content": "믿기 싫다"},
    {"title": "노드크라이 오픈이 망했으니 원신 주년에는 행복한 일만", "content": "행복한 일"}
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
        
        title = base_post['title']
        content = base_post['content']
        
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
                    print(f"글 작성 성공! (ID: {doc_id})\r\n")
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