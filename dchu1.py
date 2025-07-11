import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import concurrent.futures
import random
from datetime import datetime
from bs4 import BeautifulSoup
import threading

USER_AGENTS = [
    "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G998N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G973N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
]

def dc_recommend(proxy_url, gall_id, post_no):
    post_url = f"https://m.dcinside.com/board/{gall_id}/{post_no}"
    recommend_url = "https://m.dcinside.com/ajax/recommend"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": post_url
    }
    try:
        res_get = requests.get(post_url, headers=headers, proxies={"http": proxy_url, "https": proxy_url}, timeout=8)
        soup = BeautifulSoup(res_get.text, 'lxml')
        meta_tag = soup.find('meta', {'name': 'csrf-token'})
        if not meta_tag:
            return False, "csrf-token 파싱 실패"
        headers['X-CSRF-TOKEN'] = meta_tag['content']
        data = {
            "type": "recommend_join",
            "id": gall_id,
            "no": post_no
        }
        res_post = requests.post(recommend_url, headers=headers, data=data, proxies={"http": proxy_url, "https": proxy_url}, timeout=7)
        try:
            resp_json = res_post.json()
            if resp_json.get('result', False):
                return True, resp_json
            else:
                return False, resp_json.get('msg', str(resp_json))
        except Exception:
            return False, "응답 파싱 오류: " + res_post.text[:120]
    except Exception as e:
        return False, f"예외 발생: {e}"

class RecommendGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DC 추천 자동화 GUI")

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
        proxies = [p.strip() for p in self.proxy_text.get('1.0', tk.END).splitlines() if p.strip()]
        if not gall_id or not post_no or not proxies:
            messagebox.showwarning("입력오류", "갤러리ID, 글번호, 프록시 모두 입력하세요.")
            return
        self.start_btn['state'] = 'disabled'
        self.log_box['state'] = 'normal'
        self.log_box.delete('1.0', tk.END)
        self.log_box['state'] = 'disabled'
        self.progress.set("진행 중...")
        threading.Thread(target=self.run_recommend, args=(gall_id, post_no, proxies), daemon=True).start()

    def run_recommend(self, gall_id, post_no, proxy_list):
        total = len(proxy_list)
        self.progress.set(f"0 / {total} 완료")
        results = []

        def worker(idx, proxy_url):
            now = datetime.now().strftime('%H:%M:%S')
            success, msg = dc_recommend(proxy_url, gall_id, post_no)
            result_text = f"[{now}] [{idx:02d}] {'성공' if success else '실패'} | {msg}"
            self.log(result_text)
            results.append(success)
            self.progress.set(f"{len(results)} / {total} 완료")

        with concurrent.futures.ThreadPoolExecutor(max_workers=total) as executor:
            executor.map(lambda pair: worker(pair[0]+1, pair[1]), enumerate(proxy_list))
        self.progress.set(f"완료: {results.count(True)} 성공 / {results.count(False)} 실패")
        self.start_btn['state'] = 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = RecommendGUI(root)
    root.mainloop()
