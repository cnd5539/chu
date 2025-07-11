import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import concurrent.futures
import random
from datetime import datetime
from bs4 import BeautifulSoup
import threading

# 사용자 에이전트 리스트
USER_AGENTS = [
    "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G998N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G973N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
]

# --- PROXY.CC 프록시 정보를 여기에 입력 ---
# 각 요청마다 IP를 바꿔주는 회전(Rotating) 프록시 게이트웨이 주소입니다.
PROXY_USER = "pcc-cnd5539_area-KR"  # 국가 코드가 포함된 사용자 이름
PROXY_PASS = "cndgml8815"
PROXY_HOST = "gw.proxy.cc"
PROXY_PORT = "4512"
# 프록시 게이트웨이 URL 조합
PROXY_GATEWAY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"

def dc_recommend(gall_id, post_no):
    """
    PROXY.CC 회전 프록시 게이트웨이를 사용하도록 설정된 함수.
    """
    post_url = f"https://m.dcinside.com/board/{gall_id}/{post_no}"
    recommend_url = "https://m.dcinside.com/ajax/recommend"
    
    # 요청마다 다른 IP를 할당받기 위해 동일한 게이트웨이 주소를 사용
    proxies = {"http": PROXY_GATEWAY_URL, "https": PROXY_GATEWAY_URL}
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": post_url
    }
    
    try:
        # 타임아웃을 15초로 설정하여 안정성 확보
        res_get = requests.get(post_url, headers=headers, proxies=proxies, timeout=15)
        soup = BeautifulSoup(res_get.text, 'lxml')
        meta_tag = soup.find('meta', {'name': 'csrf-token'})
        
        if not meta_tag:
            return False, "csrf-token 파싱 실패"
        
        headers['X-CSRF-TOKEN'] = meta_tag['content']
        data = {"type": "recommend_join", "id": gall_id, "no": post_no}
        
        res_post = requests.post(recommend_url, headers=headers, data=data, proxies=proxies, timeout=15)
        
        try:
            resp_json = res_post.json()
            if resp_json.get('result', False):
                return True, resp_json.get('cause', '성공')
            else:
                # DC 서버의 다양한 실패 메시지를 그대로 가져오도록 수정
                return False, resp_json.get('msg') or resp_json.get('cause', str(resp_json))
        except Exception:
            return False, "응답 파싱 오류: " + res_post.text[:120]
            
    except Exception as e:
        return False, f"예외 발생: {e}"

class RecommendGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DC 추천 자동화 GUI (PROXY.CC 최적화)")

        tk.Label(root, text="갤러리ID:").grid(row=0, column=0, sticky='e')
        self.gall_id_entry = tk.Entry(root, width=20)
        self.gall_id_entry.grid(row=0, column=1, sticky='w')

        tk.Label(root, text="글번호:").grid(row=1, column=0, sticky='e')
        self.post_no_entry = tk.Entry(root, width=20)
        self.post_no_entry.grid(row=1, column=1, sticky='w')

        tk.Label(root, text="추천 시도 횟수:").grid(row=2, column=0, sticky='e')
        self.attempt_entry = tk.Entry(root, width=20)
        self.attempt_entry.grid(row=2, column=1, sticky='w')
        self.attempt_entry.insert(0, "25") # 기본값

        self.start_btn = tk.Button(root, text="추천 시작", command=self.start_recommend, bg="#21b3ff")
        self.start_btn.grid(row=3, column=1, sticky='w', pady=5)

        tk.Label(root, text="진행상황:").grid(row=4, column=0, sticky='ne')
        self.progress = tk.StringVar()
        self.progress_label = tk.Label(root, textvariable=self.progress)
        self.progress_label.grid(row=4, column=1, sticky='w')

        tk.Label(root, text="결과 로그:").grid(row=5, column=0, sticky='ne')
        self.log_box = scrolledtext.ScrolledText(root, width=60, height=15, state='disabled')
        self.log_box.grid(row=5, column=1, pady=5)

    def log(self, msg):
        self.log_box['state'] = 'normal'
        self.log_box.insert(tk.END, msg + '\n')
        self.log_box.see(tk.END)
        self.log_box['state'] = 'disabled'

    def start_recommend(self):
        gall_id = self.gall_id_entry.get().strip()
        post_no = self.post_no_entry.get().strip()
        
        try:
            attempts = int(self.attempt_entry.get().strip())
            if attempts <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("입력오류", "추천 시도 횟수는 1 이상의 숫자로 입력하세요.")
            return

        if not gall_id or not post_no:
            messagebox.showwarning("입력오류", "갤러리ID와 글번호를 모두 입력하세요.")
            return
            
        self.start_btn['state'] = 'disabled'
        self.log_box.delete('1.0', tk.END)
        self.progress.set("진행 중...")
        threading.Thread(target=self.run_recommend, args=(gall_id, post_no, attempts), daemon=True).start()

    def run_recommend(self, gall_id, post_no, attempts):
        self.progress.set(f"0 / {attempts} 완료")
        results = []

        def worker(idx):
            now = datetime.now().strftime('%H:%M:%S')
            success, msg = dc_recommend(gall_id, post_no)
            result_text = f"[{now}] [요청 {idx:02d}] {'성공' if success else '실패'} | {msg}"
            self.log(result_text)
            results.append(success)
            self.progress.set(f"{len(results)} / {attempts} 완료")

        with concurrent.futures.ThreadPoolExecutor(max_workers=attempts) as executor:
            executor.map(worker, range(1, attempts + 1))
            
        self.progress.set(f"완료: {results.count(True)} 성공 / {results.count(False)} 실패")
        self.start_btn['state'] = 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = RecommendGUI(root)
    root.mainloop()