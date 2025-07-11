import tkinter as tk
from tkinter import scrolledtext, messagebox
from curl_cffi import requests as cffi_requests
import concurrent.futures
import random
import time
from datetime import datetime
from bs4 import BeautifulSoup
import threading

# (변경) 최신 브라우저 및 기기 환경을 반영한 10개의 새로운 User-Agent
USER_AGENTS = [
    # Windows + Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Windows + Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    # Windows + Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    # macOS + Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    # macOS + Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Android + Chrome
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    # Android + Samsung Browser
    "Mozilla/5.0 (Linux; Android 14; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36",
    # iPhone + Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    # iPad + Safari
    "Mozilla/5.0 (iPad; CPU OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    # Linux + Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
]

BROWSER_PROFILES = ["chrome120", "chrome116", "safari17_0", "chrome124"]

def dc_recommend(proxy_url, gall_id, post_no):
    """
    (변경) 각 요청을 완벽히 격리하기 위해 cffi_requests.Session 객체를 사용합니다.
    세션은 이 함수가 실행될 때마다 새로 생성되고, 끝나면 파기됩니다.
    """
    post_url = f"https://m.dcinside.com/board/{gall_id}/{post_no}"
    recommend_url = "https://m.dcinside.com/ajax/recommend"
    timeout = 15

    try:
        # with 구문을 사용하여 함수 종료 시 세션이 자동으로 닫히고 모든 쿠키/세션 정보가 파기되도록 보장합니다.
        with cffi_requests.Session(
            proxies={"http": proxy_url, "https": proxy_url}, 
            impersonate=random.choice(BROWSER_PROFILES),
            headers={"User-Agent": random.choice(USER_AGENTS)} # 세션에 기본 User-Agent 설정
        ) as session:

            # 1. GET 요청으로 페이지에 접근하여 쿠키와 CSRF 토큰 획득
            # 세션에 Referer 헤더 추가
            session.headers["Referer"] = post_url
            res_get = session.get(post_url, timeout=timeout)
            
            if res_get.status_code != 200:
                return False, f"페이지 로딩 실패 (상태코드: {res_get.status_code})"
            if not res_get.text or res_get.text.isspace():
                return False, f"페이지 로딩 실패 (상태코드: {res_get.status_code}, 응답 내용 없음)"

            soup = BeautifulSoup(res_get.text, 'lxml')
            meta_tag = soup.find('meta', {'name': 'csrf-token'})
            
            if not meta_tag or not meta_tag.get('content'):
                page_title = soup.find('title')
                title_text = page_title.text.strip() if page_title else "타이틀 없음"
                return False, f"csrf-token 파싱 실패 (페이지 제목: '{title_text}')"
            
            # 2. POST 요청을 위해 획득한 토큰과 추가 헤더를 세션에 설정
            session.headers.update({
                "X-CSRF-TOKEN": meta_tag['content'],
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01"
            })
            
            data = {"type": "recommend_join", "id": gall_id, "no": post_no}
            
            # 동일한 세션을 통해 POST 요청 (획득한 쿠키가 자동으로 함께 전송됨)
            res_post = session.post(recommend_url, data=data, timeout=timeout)
            
            try:
                resp_json = res_post.json()
                return (True, resp_json) if resp_json.get('result') else (False, resp_json.get('msg', str(resp_json)))
            except Exception:
                return False, "응답 파싱 오류: " + res_post.text[:120]
            
    except Exception as e:
        return False, f"세션/네트워크 예외 발생: {e}"


class RecommendGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DC 추천 자동화 GUI (v1.3 - 세션 격리)")

        tk.Label(root, text="갤러리ID:").grid(row=0, column=0, sticky='e', padx=5, pady=2)
        self.gall_id_entry = tk.Entry(root, width=20)
        self.gall_id_entry.grid(row=0, column=1, sticky='w', padx=5, pady=2)

        tk.Label(root, text="글번호:").grid(row=1, column=0, sticky='e', padx=5, pady=2)
        self.post_no_entry = tk.Entry(root, width=20)
        self.post_no_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)

        tk.Label(root, text="프록시 리스트 (한 줄에 하나):").grid(row=2, column=0, sticky='ne', padx=5, pady=2)
        self.proxy_text = scrolledtext.ScrolledText(root, width=60, height=7)
        self.proxy_text.grid(row=2, column=1, pady=5, padx=5)

        self.start_btn = tk.Button(root, text="추천 시작", command=self.start_recommend, bg="#21b3ff", fg="white", relief="groove")
        self.start_btn.grid(row=3, column=1, sticky='w', pady=5, padx=5)

        tk.Label(root, text="진행상황:").grid(row=4, column=0, sticky='ne', padx=5, pady=2)
        self.progress = tk.StringVar()
        self.progress.set("대기 중")
        self.progress_label = tk.Label(root, textvariable=self.progress)
        self.progress_label.grid(row=4, column=1, sticky='w', padx=5, pady=2)

        tk.Label(root, text="결과 로그:").grid(row=5, column=0, sticky='ne', padx=5, pady=2)
        self.log_box = scrolledtext.ScrolledText(root, width=60, height=15, state='disabled', bg='#f0f0f0')
        self.log_box.grid(row=5, column=1, pady=5, padx=5)

    def log(self, msg):
        self.root.after(0, self._log_update, msg)

    def _log_update(self, msg):
        self.log_box['state'] = 'normal'
        self.log_box.insert(tk.END, msg + '\n')
        self.log_box.see(tk.END)
        self.log_box['state'] = 'disabled'

    def set_progress(self, msg):
        self.root.after(0, self.progress.set, msg)

    def start_recommend(self):
        gall_id = self.gall_id_entry.get().strip()
        post_no = self.post_no_entry.get().strip()
        proxies = [p.strip() for p in self.proxy_text.get('1.0', tk.END).splitlines() if p.strip()]
        
        if not all([gall_id, post_no, proxies]):
            messagebox.showwarning("입력 오류", "갤러리ID, 글번호, 프록시를 모두 입력하세요.")
            return
            
        self.start_btn['state'] = 'disabled'
        self.log_box['state'] = 'normal'
        self.log_box.delete('1.0', tk.END)
        self.log_box['state'] = 'disabled'
        self.set_progress("진행 중...")
        
        threading.Thread(target=self.run_recommend, args=(gall_id, post_no, proxies), daemon=True).start()

    def run_recommend(self, gall_id, post_no, proxy_list):
        total = len(proxy_list)
        self.set_progress(f"0 / {total} 완료")
        
        results_lock = threading.Lock()
        results = []

        def worker(idx, proxy_url):
            time.sleep(random.uniform(0.1, 0.5))
            
            now = datetime.now().strftime('%H:%M:%S')
            success, msg = dc_recommend(proxy_url, gall_id, post_no)
            result_text = f"[{now}] [프록시 {idx:02d}] {'성공' if success else '실패'} | {msg}"
            self.log(result_text)
            
            with results_lock:
                results.append(success)
                self.set_progress(f"{len(results)} / {total} 완료")

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(total, 50)) as executor:
            executor.map(lambda p: worker(p[0]+1, p[1]), enumerate(proxy_list))
        
        success_count = results.count(True)
        fail_count = total - success_count
        self.set_progress(f"완료: {success_count} 성공 / {fail_count} 실패")
        self.start_btn['state'] = 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = RecommendGUI(root)
    root.mainloop()