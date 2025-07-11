import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import random
import time
from datetime import datetime
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 11; SM-G991N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G973N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
]

def dc_recommend(proxy_url, gall_id, post_no):
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
        # 모바일 페이지에서 csrf-token 추출
        res_get = s.get(post_url, headers=headers, proxies=proxies, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(res_get.text, 'lxml')
        meta_tag = soup.find("meta", attrs={"name": "csrf-token"})
        if not meta_tag or not meta_tag.get("content"):
            # 토큰이 없으면 에러 메시지와 제목 일부 함께 반환
            title = soup.find("title")
            return False, f"csrf-token 파싱 실패. TITLE: {title.text if title else 'N/A'}"
        csrf_token = meta_tag.get("content")

        # 추천 POST
        headers["X-CSRF-TOKEN"] = csrf_token
        data = {
            "type": "recommend_join",
            "id": gall_id,
            "no": post_no
        }
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

class RecommendGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("디시 모바일 추천 자동화 (0.2초 간격, 30회)")

        tk.Label(root, text="갤러리ID:").grid(row=0, column=0, sticky='e')
        self.gall_id_entry = tk.Entry(root, width=20)
        self.gall_id_entry.grid(row=0, column=1, sticky='w')

        tk.Label(root, text="글번호:").grid(row=1, column=0, sticky='e')
        self.post_no_entry = tk.Entry(root, width=20)
        self.post_no_entry.grid(row=1, column=1, sticky='w')

        tk.Label(root, text="프록시 리스트 (한 줄에 하나):").grid(row=2, column=0, sticky='ne')
        self.proxy_text = scrolledtext.ScrolledText(root, width=60, height=7)
        self.proxy_text.grid(row=2, column=1, pady=5)

        self.start_btn = tk.Button(root, text="추천 시작", command=self.start_recommend, bg="#21b3ff")
        self.start_btn.grid(row=3, column=1, sticky='w', pady=5)

        tk.Label(root, text="진행상황:").grid(row=4, column=0, sticky='ne')
        self.progress = tk.StringVar()
        self.progress.set("")
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
        proxies = []
        for p in self.proxy_text.get('1.0', tk.END).splitlines():
            p = p.strip()
            if not p:
                continue
            if not p.startswith("http"):
                p = "http://" + p
            proxies.append(p)
        if not gall_id or not post_no or not proxies:
            messagebox.showwarning("입력오류", "갤러리ID, 글번호, 프록시 모두 입력하세요.")
            return
        self.start_btn['state'] = 'disabled'
        self.log_box['state'] = 'normal'
        self.log_box.delete('1.0', tk.END)
        self.log_box['state'] = 'disabled'
        self.progress.set("진행 중...")

        import threading
        threading.Thread(target=self.run_recommend, args=(gall_id, post_no, proxies), daemon=True).start()

    def run_recommend(self, gall_id, post_no, proxy_list):
        total = min(30, len(proxy_list))
        proxy_list = proxy_list[:total]
        random.shuffle(proxy_list)  # 순서 무작위

        self.progress.set(f"0 / {total} 완료")
        results = []

        def worker(idx, proxy_url):
            now = datetime.now().strftime('%H:%M:%S')
            success, msg = dc_recommend(proxy_url, gall_id, post_no)
            result_text = f"[{now}] [{idx:02d}] {'성공' if success else '실패'} | {msg}"
            self.log(result_text)
            results.append(success)
            self.progress.set(f"{len(results)} / {total} 완료")

        for idx, proxy_url in enumerate(proxy_list, 1):
            worker(idx, proxy_url)
            time.sleep(random.choice([0.1, 0.2, 0.3]))  # 0.1, 0.2, 0.3초 중 랜덤

        self.progress.set(f"완료: {results.count(True)} 성공 / {results.count(False)} 실패")
        self.start_btn['state'] = 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = RecommendGUI(root)
    root.mainloop()
