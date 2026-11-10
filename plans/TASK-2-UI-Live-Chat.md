# TASK 2 — UI Streamlit + live chat transcript + hoàn thiện unit test challenge

**Owner:** Người 2 (điền tên): ____________________
**Trạng thái:** TODO
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

## 2. Trạng thái hiện tại (đã kiểm tra)

- **Chưa có `app.py`**, `requirements.txt` **chưa có `streamlit`**, venv chưa cài streamlit (`import streamlit` → False).
- **Chưa có thư mục `transcripts/`** → chưa có live chat nào.
- `pytest` hiện tại: `62 passed, 17 skipped` — 17 skip nằm ở `tests/test_tools_todo.py` (dòng 26→122).
- `.env` đã có keys: `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY`, `RAPIDAPI_TWITTER_HOST`, `ARXIV_USER_AGENT`. **Chưa có** `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` (aspect bonus).
- `chat.py` có sẵn `run_model_tool_loop()`, `execute_tool_call()`, `trim_history()` → **tái sử dụng** được từ `app.py` (`from chat import ...`), tránh viết lại vòng lặp tool.

---

## 3. Checklist thực thi

### P0 — Chuẩn bị
- [ ] `cd starter_v0`; `.\.venv\Scripts\Activate.ps1`
- [ ] `python scripts/preflight_provider.py --provider openrouter` → pass.
- [ ] Chờ Người 1 chốt `artifacts/tools.yaml` (có `rank_items`) trước khi quay transcript cuối, để số liệu/log khớp nhau. UI có thể bắt đầu code ngay từ đầu.

### P1 — UI Streamlit (`app.py`)
Yêu cầu tối thiểu (đủ để "chạy được + team khác thử được"):
- [ ] Thêm `streamlit>=1.30.0` vào `requirements.txt`; `pip install -r requirements.txt`.
- [ ] `app.py` chạy được bằng `streamlit run app.py` (mặc định cổng 8501).
- [ ] Sidebar: chọn `provider` (mặc định `openrouter`), `model` (để trống = `provider.default_model`), nhãn `version` (vd `v3`), hiển thị `artifact_version` (dùng `versioning.build_artifact_version`) và danh sách tool đang bật.
- [ ] Khung chat multi-turn: giữ history (dùng `chat.trim_history` với `history_window`), gọi `providers.make_provider` + `tools.load_tool_declarations` + `tools.to_openai_tools`.
- [ ] Hiển thị **tool call + args** và **kết quả tool** cho mỗi lượt (expandable), để chứng minh agent chọn tool/args đúng khi demo.
- [ ] Xử lý lỗi provider (try/except → hiện message, không crash app); không lộ API key.
- [ ] Nút "Xóa hội thoại".
- [ ] Chạy thử local: `streamlit run app.py` → mở `http://localhost:8501`, thử 3 câu mẫu (xem P3).
- [ ] Expose link public:
  ```powershell
  winget install --id Cloudflare.cloudflared   # nếu chưa có
  cloudflared tunnel --url http://localhost:8501
  ```
  → copy URL `https://<random>.trycloudflare.com` (giữ lệnh chạy suốt buổi demo; ghi lại URL để điền vào REPORT Phần A ở vòng sau).
- [ ] Với 1 request thiếu info (vd "Tóm tắt 5 tweet mới nhất") UI phải hiện **câu hỏi clarify**, và lượt sau bổ sung thì agent mới gọi `timeline`.

### P2 — Hoàn thiện `tests/test_tools_todo.py` (challenge: 0 skipped, 0 failed)
> Mẫu để copy: `tests/test_tools_examples.py`. Fixtures: `conftest.py` (`fake_http`, chặn mọi HTTP thật, xóa env key). Một test một hành vi; assert cả **request gửi đi** lẫn **kết quả trả về**.

- [ ] `clarify`: `response_type="choice"` → trả `options` nguyên vẹn + `awaiting_user is True`.
- [ ] `format`: nhóm item theo `section` (markdown có đúng 1 `## A`, 1 `## B`).
- [ ] `format`: `template="thread"` → các dòng bắt đầu `1/`, `2/`, …
- [ ] `format`: `items=None` và `items=[]` → `item_count == 0`, không raise.
- [ ] `send`: `confirmed=True` có env + mock HTTP → **đúng 1 POST**, URL chứa token, json có `chat_id` + `text`, `status == "sent"`.
- [ ] `send`: `confirmed=True` nhưng **thiếu env** → trả error dict và **không gọi HTTP** (`calls == []`).
- [ ] `lookup`: `timeframe=None` → body request **không** có key `time_range`.
- [ ] `fetch`: map response Firecrawl `{"data":{"markdown","metadata":{"title","sourceURL"}}}` → `items[0]` có `title/url/source/summary`.
- [ ] `fetch`: markdown dài bị cắt còn 4000 ký tự.
- [ ] `timeline`: tôn trọng `limit` và bỏ item thiếu `tweet_id`; url dạng `https://x.com/<handle>/status/<id>`.
- [ ] `social_search`: request params mang đúng `query` + `search_type` (`Top`/`Latest`).
- [ ] `policy`: `query` rỗng → không có kết quả.
- [ ] `policy`: `policy_area="data_privacy"` → mọi kết quả cùng `policy_area`.
- [ ] `policy`: dòng kiểu "ra lệnh" trong file policy nằm ở `untrusted_text`, **không** nằm trong `facts`.
- [ ] 3 stub cuối (`test_my_new_tool_*`, dòng 113–121) → viết cho **`rank_items`**: (1) happy path dedupe/top_k, (2) input xấu từ model (`items="x"`, `sort_by` ngoài enum, `top_k=True`), (3) failure path trả error dict không raise.
  > Chỉ gọi `rank_items` từ `TOOL_FUNCTIONS`; **không** tạo/sửa `tests/test_tools_rank_items.py` (Người 3 giữ file đó, tránh trùng test).
- [ ] `pytest -q` → **0 failed, 0 skipped** (tổng ≥ 79 passed).
- [ ] Nếu test bắt được bug trong tool có sẵn → sửa tool, giữ test lại làm regression, ghi chú lại cho REPORT B5 (vòng sau).

### P3 — Live chat + transcript (`chat.py`)
- [ ] Chạy: `python chat.py --provider openrouter --version v3`
- [ ] Lượt 1 — research bình thường (vd "Tin AI hôm nay có gì nổi bật?").
- [ ] Lượt 2 — thiếu thông tin rồi bổ sung (vd "Tóm tắt 5 tweet mới nhất" → agent hỏi lại → "Của Elon Musk"): quan sát agent **không đoán handle** ở lượt đầu.
- [ ] Lượt 3 — "Đăng bản tin này lên Telegram giúp mình": xác nhận agent gọi `clarify(response_type="yes_no")` **trước**, **không** gọi `send` ngay. **Chỉ quan sát** — không trả lời "có" để tránh gửi thật.
- [ ] (Tuỳ chọn, cần thêm `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` trong `.env`) một lượt xác nhận thật để có bằng chứng bonus "send có confirmation".
- [ ] Kiểm file sinh ra: `transcripts/v3_openrouter_<timestamp>.transcript.json` có ≥ 3 turn, mỗi turn có `user`, `assistant_text`, `tool_events`.
- [ ] Đối chiếu transcript với hash: `transcript.prompt_hash` / `tools_hash` khớp artifact đang nộp.
- [ ] Không commit `.env`.

### P4 — Bonus (tuỳ chọn, không bắt buộc để hoàn thành task)
- [ ] Cài Ollama + 2 model nhỏ (`qwen2.5:7b`, `llama3.2:3b`).
- [ ] ```powershell
      python run_eval.py --provider ollama --model qwen2.5:7b  --version v3-qwen7b  --suite base --eval-cases data/eval_base.json
      python run_eval.py --provider ollama --model llama3.2:3b --version v3-llama3b --suite base --eval-cases data/eval_base.json
      ```
- [ ] Ghi lại số liệu 2 run + nhận xét "cái gì giúp model nhỏ gọi tool đúng hơn" cho REPORT B7 (vòng sau).

---

## 4. Điều kiện đạt (DoD)

- [ ] `streamlit run app.py` chạy được, chat được multi-turn, hiện tool calls; có **1 link public** (trycloudflare/Vercel) đã ghi lại.
- [ ] `requirements.txt` có `streamlit`; không commit `.env`.
- [ ] `transcripts/` có **≥ 1 transcript ≥ 3 lượt**, trong đó có 1 lượt clarify thiếu info và 1 lượt xác nhận trước `send`.
- [ ] `pytest -q` → **0 failed, 0 skipped**.
- [ ] (Bonus) có run Ollama cho ≥ 2 model.

## 5. Rủi ro

- `app.py` import `chat.py` sẽ in `🔧 tool(...)` ra console — chấp nhận được; nếu muốn sạch, tự viết vòng lặp riêng trong `app.py`.
- Link `trycloudflare.com` chỉ sống theo phiên `cloudflared` — giữ lệnh chạy khi demo, hoặc deploy Streamlit Cloud/Vercel để có link ổn định.
- Lượt 3 nếu trả lời "có" khi chưa có bot/channel ⇒ lỗi env; đừng thêm key Telegram nếu không định dùng.
- Sửa `requirements.txt` có thể làm lệch môi trường của Người 1 — báo trước khi `pip install`, và chỉ **thêm** dòng, không đổi version các package cũ.
