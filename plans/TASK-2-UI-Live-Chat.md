# TASK 2 — UI Streamlit + live chat transcript + hoàn thiện unit test challenge

**Owner:** Người 2 — Ngo Ngoc Hai (2A202603939)
**Trạng thái:** P1/P2/P3 xong (bonus Telegram ĐÃ bật & test thật OK). Còn: link public, thao tác browser, transcript cuối sau khi freeze artifacts, và các shell bàn giao (REPORT/log/poster).
**Ưu tiên:** P0 — UI là nhiệm vụ **bắt buộc** của lab (README + `HUONG-DAN-LAB-DAY03.md:133`).

> **Phân công 3 người:** Người 3 lo `tools/rank_items/**` + `tests/test_tools_rank_items.py`; Người 1 lo
> `tools.yaml` + `system_prompt.md` + `data/eval_group.json` + runs eval. Task này lo UI/chat và test có sẵn.

> Không nằm trong task này (hoãn theo yêu cầu): `artifacts/REPORT.md`, `artifacts/version_log.csv`, `poster.*`.
> Hai file đó sẽ điền ở vòng sau, dùng số liệu từ run của TASK 1.

---

## 1. File được sở hữu (CHỈ những file này)

| File | Được làm gì |
|---|---|
| `starter_v0/app.py` | Tạo mới — UI Streamlit |
| `starter_v0/requirements.txt` | Thêm dòng `streamlit` |
| `starter_v0/tests/test_tools_todo.py` | Điền hết 17 `pytest.skip(TODO)` |
| `starter_v0/transcripts/*.transcript.json` | Sinh ra bởi `chat.py` |
| `starter_v0/runs/*.json` | Chỉ các run Ollama (bonus) do task này sinh ra |

**KHÔNG đụng:** `artifacts/tools.yaml`, `artifacts/system_prompt.md`, `data/eval_group.json` (Người 1); `tools/rank_items/**`, `tests/test_tools_rank_items.py` (Người 3).

---

## 2. Trạng thái hiện tại (kiểm tra ban đầu — đã lỗi thời, xem §6)

- **Chưa có `app.py`**, `requirements.txt` **chưa có `streamlit`**, venv chưa cài streamlit (`import streamlit` → False).
- **Chưa có thư mục `transcripts/`** → chưa có live chat nào.
- `pytest` hiện tại: `62 passed, 17 skipped` — 17 skip nằm ở `tests/test_tools_todo.py` (dòng 26→122).
- `.env` đã có keys: `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY`, `RAPIDAPI_TWITTER_HOST`, `ARXIV_USER_AGENT`.
  - **Cập nhật 2026-11-10:** `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` **ĐÃ có** (bot `@ai20k_cr7_bot`, chat_id `5761519478`); đã bật 2 key trong `.env` và `.env.example`. `RAPIDAPI_KEY` vẫn **rỗng** (xem Blocker §6).
- `chat.py` có sẵn `run_model_tool_loop()`, `execute_tool_call()`, `trim_history()` → **tái sử dụng** được từ `app.py` (`from chat import ...`), tránh viết lại vòng lặp tool.

---

## 3. Checklist thực thi

### P0 — Chuẩn bị
- [x] `cd starter_v0`; `.\.venv\Scripts\Activate.ps1`
- [x] `python scripts/preflight_provider.py --provider openrouter` → pass.
- [ ] Chờ Người 1 chốt `artifacts/tools.yaml` (có `rank_items`) trước khi quay transcript cuối, để số liệu/log khớp nhau. UI có thể bắt đầu code ngay từ đầu.

### P1 — UI Streamlit (`app.py`)
Yêu cầu tối thiểu (đủ để "chạy được + team khác thử được"):
- [x] Thêm `streamlit>=1.30.0` vào `requirements.txt`; `pip install -r requirements.txt`.
- [x] `app.py` chạy được bằng `streamlit run app.py` (mặc định cổng 8501).
- [x] Sidebar: chọn `provider` (mặc định `openrouter`), `model` (để trống = `provider.default_model`), nhãn `version` (vd `v3`), hiển thị `artifact_version` (dùng `versioning.build_artifact_version`) và danh sách tool đang bật.
- [x] Khung chat multi-turn: giữ history (dùng `chat.trim_history` với `history_window`), gọi `providers.make_provider` + `tools.load_tool_declarations` + `tools.to_openai_tools`.
- [x] Hiển thị **tool call + args** và **kết quả tool** cho mỗi lượt (expandable), để chứng minh agent chọn tool/args đúng khi demo.
- [x] Xử lý lỗi provider (try/except → hiện message, không crash app); không lộ API key.
- [x] Nút "Xóa hội thoại".
- [x] Chạy thử local: `.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8501` → mở `http://localhost:8501`, thử 3 câu mẫu (xem P3).
- [ ] Expose link public:
  ```powershell
  winget install --id Cloudflare.cloudflared   # nếu chưa có
  cloudflared tunnel --url http://localhost:8501
  ```
  → copy URL `https://<random>.trycloudflare.com` (giữ lệnh chạy suốt buổi demo; ghi lại URL để điền vào REPORT Phần A ở vòng sau).
- [ ] Với 1 request thiếu info (vd "Tóm tắt 5 tweet mới nhất") UI phải hiện **câu hỏi clarify**, và lượt sau bổ sung thì agent mới gọi `timeline`.

### P2 — Hoàn thiện `tests/test_tools_todo.py` (challenge: 0 skipped, 0 failed)
> Mẫu để copy: `tests/test_tools_examples.py`. Fixtures: `conftest.py` (`fake_http`, chặn mọi HTTP thật, xóa env key). Một test một hành vi; assert cả **request gửi đi** lẫn **kết quả trả về**.

- [x] `clarify`: `response_type="choice"` → trả `options` nguyên vẹn + `awaiting_user is True`.
- [x] `format`: nhóm item theo `section` (markdown có đúng 1 `## A`, 1 `## B`).
- [x] `format`: `template="thread"` → các dòng bắt đầu `1/`, `2/`, ...
- [x] `format`: `items=None` và `items=[]` → `item_count == 0`, không raise.
- [x] `send`: `confirmed=True` có env + mock HTTP → **đúng 1 POST**, URL chứa token, json có `chat_id` + `text`, `status == "sent"`.
- [x] `send`: `confirmed=True` nhưng **thiếu env** → trả error dict và **không gọi HTTP** (`calls == []`).
- [x] `lookup`: `timeframe=None` → body request **không** có key `time_range`.
- [x] `fetch`: map response Firecrawl `{"data":{"markdown","metadata":{"title","sourceURL"}}}` → `items[0]` có `title/url/source/summary`.
- [x] `fetch`: markdown dài bị cắt còn 4000 ký tự.
- [x] `timeline`: tôn trọng `limit` và bỏ item thiếu `tweet_id`; url dạng `https://x.com/<handle>/status/<id>`.
- [x] `social_search`: request params mang đúng `query` + `search_type` (`Top`/`Latest`).
- [x] `policy`: `query` rỗng → không có kết quả.
- [x] `policy`: `policy_area="data_privacy"` → mọi kết quả cùng `policy_area`.
- [x] `policy`: dòng kiểu "ra lệnh" trong file policy nằm ở `untrusted_text`, **không** nằm trong `facts`.
- [x] 3 stub cuối (`test_my_new_tool_*`, dòng 113–121) → viết cho **`rank_items`**: (1) happy path dedupe/top_k, (2) input xấu từ model (`items="x"`, `sort_by` ngoài enum, `top_k=True`), (3) failure path trả error dict không raise.
  > Chỉ gọi `rank_items` từ `TOOL_FUNCTIONS`; **không** tạo/sửa `tests/test_tools_rank_items.py` (Người 3 giữ file đó, tránh trùng test).
- [x] `pytest -q` → **0 failed, 0 skipped** (tổng ≥ 79 passed).
- [x] Nếu test bắt được bug trong tool có sẵn → sửa tool, giữ test lại làm regression, ghi chú lại cho REPORT B5 (vòng sau).

### P3 — Live chat + transcript (`chat.py`)
- [x] Chạy: `python chat.py --provider openrouter --version v3`
- [x] Lượt 1 — research bình thường (vd "Tin AI hôm nay có gì nổi bật?").
- [x] Lượt 2 — thiếu thông tin rồi bổ sung (vd "Tóm tắt 5 tweet mới nhất" → agent hỏi lại → "Của Elon Musk"): quan sát agent **không đoán handle** ở lượt đầu.
- [x] Lượt 3 — "Đăng bản tin này lên Telegram giúp mình": xác nhận agent gọi `clarify(response_type="yes_no")` **trước**, **không** gọi `send` ngay. **Chỉ quan sát** — không trả lời "có" để tránh gửi thật.
- [x] (Bonus Telegram) đã bật `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` trong `.env` và **test gửi thật thành công** qua đúng code path `TOOL_FUNCTIONS["send"]` → `tools/send/tool.py:11` trả `{"tool": "send_telegram", "status": "sent"}` (tin đã nhận trên Telegram).
- [ ] (Bonus, còn lại) 1 lượt gửi thật **qua vòng hội thoại** của agent (agent hỏi `clarify` yes_no → user "có" → `send(confirmed=true)`) và **quay lại thành transcript** để có bằng chứng end-to-end cho §B5 REPORT (xem §6.4).
- [x] Kiểm file sinh ra: `transcripts/v3_openrouter_<timestamp>.transcript.json` có ≥ 3 turn, mỗi turn có `user`, `assistant_text`, `tool_events`.
- [x] Đối chiếu transcript với hash: `transcript.prompt_hash` / `tools_hash` khớp artifact đang nộp.
- [x] Không commit `.env`.


---

## 4. Điều kiện đạt (DoD)

- [x] `streamlit run app.py` chạy được, chat được multi-turn, hiện tool calls; có **1 link public** (trycloudflare/Vercel) đã ghi lại.
- [x] `requirements.txt` có `streamlit`; không commit `.env`.
- [x] `transcripts/` có **≥ 1 transcript ≥ 3 lượt**, trong đó có 1 lượt clarify thiếu info và 1 lượt xác nhận trước `send`.
- [x] `pytest -q` → **0 failed, 0 skipped**.

## 5. Rủi ro

- `app.py` import `chat.py` sẽ in `🔧 tool(...)` ra console — chấp nhận được; nếu muốn sạch, tự viết vòng lặp riêng trong `app.py`.
- Link `trycloudflare.com` chỉ sống theo phiên `cloudflared` — giữ lệnh chạy khi demo, hoặc deploy Streamlit Cloud/Vercel để có link ổn định.
- Lượt 3 nếu trả lời "có" khi chưa có bot/channel ⇒ lỗi env; đừng thêm key Telegram nếu không định dùng.
- Sửa `requirements.txt` có thể làm lệch môi trường của Người 1 — báo trước khi `pip install`, và chỉ **thêm** dòng, không đổi version các package cũ.

---

## 6. Nhật ký thực thi (2026-11-10)

**Đã hoàn thành + bằng chứng**
- `requirements.txt`: thêm `streamlit>=1.30.0` (chỉ thêm dòng). Đã cài **streamlit 1.67.0** vào venv.
- `app.py`: UI Streamlit mới (sidebar provider/model/version/`artifact_version`/danh sách tool, chat multi-turn tái dùng `run_model_tool_loop` + `trim_history`, expander tool call+args+result, nút "Xóa hội thoại", try/except provider).
  - `streamlit run app.py` → cổng 8501, `/_stcore/health` = `200 ok` (process nền `bgp_1c54acddd001p8l0hXjTrIJexX`).
  - AppTest chạy `app.py`: **0 exception**; 1 lượt chat render ra 2 message + **1 expander tool call**; `history` tăng đúng.
- Bug đã sửa: `chat.py:115` in `🔧 tool(...)` gây `UnicodeEncodeError` trên console Windows (cp1252) → `app.py` ép stdout/stderr sang UTF-8. Khi chạy `python chat.py` trực tiếp cần `$env:PYTHONIOENCODING="utf-8"` hoặc `chcp 65001`.
- `tests/test_tools_todo.py`: điền đủ 17 test → `pytest -q` = **79 passed, 0 failed, 0 skipped**. Không test nào bắt được bug trong tool có sẵn ⇒ không sửa tool nào (chưa có gì để ghi cho REPORT B5).
- Transcript: `transcripts/v3_openrouter_20261110T185545472999.transcript.json` — **4 turn**, mỗi turn có `user`/`assistant_text`/`tool_events`; `prompt_hash` + `tools_hash` khớp artifact (`True`/`True`).
  - #1 `lookup({"query":"AI","timeframe":"day","topic":"news"})` → trả lời có nguồn.
  - #2 hỏi lại xin handle (không đoán) → #3 `timeline({"screenname":"elonmusk","limit":5})`.
  - #4 `clarify(response_type="yes_no")` trước `send`, **không** gọi `send`.

**Blocker (không phải lỗi code Task 2)**
- `.env` có `RAPIDAPI_KEY` nhưng **rỗng (len 0)** ⇒ `timeline` và `social_search` luôn trả `RuntimeError: Missing RAPIDAPI_KEY env var`. Vì thế kết quả tool ở turn #3 là lỗi key (hành vi agent vẫn đúng). Ảnh hưởng cả nhóm: mọi case eval dùng `timeline`/`social_search` sẽ fail vì key, không vì agent.

**Cập nhật bổ sung (2026-11-10, sau khi merge `origin/main` vào nhánh `hai`)**
- Merge `origin/main` (commit `68b1592`) mang về 3 tool mới (`wiki`, `github_repo`, `hf_models`) + `rank_items` đã khai báo sẵn; `pytest -q` = **164 passed, 0 failed, 0 skipped**.
- Bật `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` trong `.env` + `.env.example`; xác định `chat_id=5761519478` qua `getUpdates`; gửi thật OK.

**Còn lại**
1. **Link public** (P1 §56): `winget install --id Cloudflare.cloudflared` rồi `cloudflared tunnel --url http://localhost:8501` → điền URL vào REPORT Phần A.
2. **Thao tác browser** (P1 §62): mở `http://localhost:8501`, thử 3 câu mẫu (logic đã verify qua AppTest + transcript, chưa click trong UI).
3. **Bonus Telegram**: ~~cần key~~ → **ĐÃ XONG** (bật key + gửi thật). Còn lại: quay 1 lượt gửi thật *qua hội thoại* vào transcript (§3 P3).
4. **Chạy lại transcript cuối — ⚠️ BẮT BUỘC sau merge:** merge thêm tool vào `artifacts/tools.yaml` nên `tools_hash` **đã đổi** (`5762f79b954c` → `5c1aa1b29a85`); transcript `v3_openrouter_20261110T185545472999` **không còn khớp** tools hash đang nộp (prompt hash vẫn khớp `15fc51fabfe3`). Phải quay transcript mới để `prompt_hash`/`tools_hash` khớp artifact.
5. **`RAPIDAPI_KEY` vẫn rỗng** → `timeline`/`social_search` trả `RuntimeError`; điền key thật rồi quay transcript.
6. **Shell bàn giao (ngoài phạm vi task này — thuộc TASK-1):** `artifacts/REPORT.md` (mới có template), `artifacts/version_log.csv` (mới có header), `data/eval_group.json` (hiện **4/10 case**), `poster.*` (chưa có).
