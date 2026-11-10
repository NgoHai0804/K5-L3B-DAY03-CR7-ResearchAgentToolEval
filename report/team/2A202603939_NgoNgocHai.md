# Báo cáo cá nhân — NgoNgocHai-2A202603939

## 1. Thông tin thành viên

- Họ tên: Ngô Ngọc Hải
- MSSV: 2A202603939
- Email: ngongochai0804@gmail.com
- Nhóm: CR7 (L3B), nhánh làm việc `hai`
- Vai trò: B — Tool & Arg convention (v2), baseline v0, kế hoạch chia việc, UI Streamlit, live chat/transcript, stub test của tool có sẵn (TASK-2)

## 2. Phần việc phụ trách

Theo [plans/PLAN-INDEX.md](../../plans/PLAN-INDEX.md), nhóm chia 3 vai trò, mỗi người sở hữu một vùng file riêng để làm song song không xung đột. Phần của tôi:

- **Baseline & kế hoạch:** chạy baseline `v0`, đóng băng bản v0 (`artifacts/_baseline/`), chia việc 3 version song song để A/B/C không đụng file của nhau.
- **Role B:** phần thân `artifacts/tools.yaml` (v2) — viết lại mô tả 10 tool có sẵn theo hướng "khi nào dùng / khi nào không dùng" + convention args.
- **UI:** `starter_v0/app.py` (Streamlit) + dòng `streamlit` trong `requirements.txt`.
- **Live chat & transcript:** `starter_v0/chat.py`, gồm luồng gửi Telegram thật sau khi người dùng xác nhận.
- **Unit test tool có sẵn:** điền các stub trong `starter_v0/tests/test_tools_todo.py` (challenge 4b), giữ `pytest` xanh.
- **Điều phối:** quản lý merge các PR #1–#9 vào `main`.

## 3. Đóng góp cụ thể

### 3.1. Baseline v0 và kế hoạch làm song song

- Chạy base eval `v0` (starter chưa sửa) → `case_accuracy` 0.65. Chạy lặp 4 lần cùng hash cho 0.65 / 0.65 / 0.70 / 0.70 ⇒ đo được **độ dao động ±0.05** giữa các lần chạy; con số này dùng để diễn giải các bảng so sánh về sau.
- Đóng băng `artifacts/_baseline/system_prompt_v0.md` + `artifacts/_baseline/tools_v0.yaml` để mỗi người test độc lập: A sửa prompt nhưng vẫn dùng tools v0, B sửa tools nhưng dùng prompt v0 (qua `run_eval.py --system-prompt/--tools`).
- Viết [plans/PLAN-INDEX.md](../../plans/PLAN-INDEX.md): bản đồ version tích luỹ (v0 → v1 → v2 → v3), vùng file từng người, quy ước "C chèn khối tool mới ở cuối `tools.yaml` sau khi B freeze phần thân".

### 3.2. v2 — viết lại `tools.yaml` (Role B)

- Viết lại `description` của 10 tool có sẵn theo khuôn: làm gì → **khi nào dùng** → **khi nào không dùng** → dùng tool nào thay; kèm convention args: handle không có `@` và viết thường, `query` chỉ giữ chủ đề chính (không nhét "news"/"tin tức"), `topic=news` + `timeframe` cho tin tức, `search_type=Top|Latest`, `send` chỉ gửi khi `confirmed=true`.
- **Giả thuyết:** mô tả tool mơ hồ khiến model gửi `send` ngay mà không xác nhận (case R12); viết rõ boundary của `send` sẽ sửa được.
- **Kết quả: 0.95 → 0.85 — giả thuyết KHÔNG được xác nhận.** R12 vẫn fail (model hỏi nội dung bằng `clarify(response_type="text")` thay vì hỏi xác nhận `yes_no`), đồng thời phát sinh hồi quy: R10 (model gọi `social_search("tóm tắt")` thay vì hỏi lại) và M06 (gọi thừa tool nguồn đã bị user bỏ). Tôi ghi trung thực kết quả âm này vào `version_log.csv` thay vì giữ lại một thay đổi không cải thiện.
- Chạy thêm một **run cô lập** để tách ảnh hưởng: prompt v0 + tools v2 → 0.80, xác nhận phần hồi quy đến từ thay đổi mô tả tool chứ không phải nhiễu giữa các lần chạy.
- **Bài học chuyển cho v3:** thông tin "khi nào dùng/không dùng" đúng là thuộc mô tả tool, nhưng các lỗi **ưu tiên rule** (send, bỏ nguồn) lại thuộc `system_prompt.md` — Đức đã sửa được ở v3 (0.85 → 1.0).

### 3.3. UI Streamlit (`app.py`)

- Thêm `streamlit>=1.30.0` vào `requirements.txt` (chỉ **thêm** một dòng, không đổi version các package cũ để không phá môi trường của thành viên khác).
- `app.py`:
  - Sidebar: chọn `provider` (mặc định openrouter), `model`, nhãn `version`, hiển thị `artifact_version` (dùng `versioning.build_artifact_version`) và danh sách tool đang bật.
  - Khung chat multi-turn, tái sử dụng `run_model_tool_loop` + `trim_history` từ `chat.py` (không viết lại vòng lặp tool).
  - Mỗi lượt hiện **tool call + args** và **kết quả tool** trong expander, để chứng minh agent chọn đúng tool/args khi demo.
  - Nút "Xóa hội thoại"; `try/except` quanh lời gọi provider để không crash app và không lộ API key.
- **Link dùng thử** qua Cloudflare Tunnel (`cloudflared tunnel --url http://localhost:8501`).
- **Kiểm chứng:** `streamlit run app.py` → cổng 8501, endpoint `/_stcore/health` trả `200 ok`. Chạy `AppTest` trên `app.py`: **0 exception**; 1 lượt chat render ra 2 message + 1 expander tool call; `history` tăng đúng.
- **Bug đã sửa:** `chat.py:115` in `🔧 tool(...)` gây `UnicodeEncodeError` trên console Windows (cp1252) → `app.py` ép `stdout/stderr` sang UTF-8. Khi chạy `python chat.py` trực tiếp cần `$env:PYTHONIOENCODING="utf-8"` (hoặc `chcp 65001`).

### 3.4. Live chat và transcript (gồm luồng `send` end-to-end)

`chat.py` ghi mỗi lượt ra `transcripts/*.transcript.json` (mỗi turn có `user`, `assistant_text`, `tool_events`).

- **Transcript `v3_openrouter_20261110T194324903467`** (5 lượt, artifact khớp bản chốt):
  1. "Tin AI hôm nay…" → `lookup(query=AI, topic=news, timeframe=day)` → trả lời có nguồn.
  2. "Transformer trong deep learning là gì?" → `wiki(...)`.
  3. "Repo ollama/ollama bao nhiêu star…" → `github_repo` gọi **1 lần**.
  4. "Tóm tắt 5 tweet mới nhất" → agent **hỏi lại handle** (không đoán) → "Của Andrej Karpathy" → `timeline(screenname=karpathy, limit=5)`.
  5. "Đăng bản tin này lên Telegram giúp mình" → `clarify(response_type=yes_no)`, **không** gọi `send`.
- **Transcript `v3_openrouter_20261110T215800069030`** (send end-to-end, bằng chứng guardrail):
  - Turn 1 → `clarify(response_type=yes_no)`, status `waiting_for_user`, **không** gọi `send`.
  - Turn 2 ("Có, mình xác nhận…") → `send({"text": …, "confirmed": true})` → `{"tool": "send_telegram", "status": "sent"}` (gửi thật, tin nhận trên Telegram).

### 3.5. Unit test tool có sẵn (challenge 4b: 0 skipped, 0 failed)

- Điền hết các stub trong `tests/test_tools_todo.py` cho `clarify`, `format`, `send`, `lookup`, `fetch`, `timeline`, `social_search`, `policy`. Nguyên tắc: một test kiểm **một** hành vi, assert **cả request gửi đi lẫn kết quả trả về**, chạy offline (HTTP bị chặn, mock bằng fixture `fake_http`).
- Ví dụ hành vi được đo:
  - `send`: `confirmed=true` + đủ env → **đúng 1 POST**, URL chứa token, body có `chat_id` + `text`, `status == "sent"`; `confirmed=true` nhưng thiếu env → trả error dict và **không gọi HTTP**.
  - `lookup`: `timeframe=None` → body request **không** có key `time_range`.
  - `fetch`: map response Firecrawl → `items[0]` có `title/url/source/summary`; markdown dài bị cắt còn 4000 ký tự.
  - `policy`: dòng kiểu "ra lệnh" trong file policy nằm ở `untrusted_text`, **không** nằm trong `facts`.
- Sau khi Đức và Quyền merge phần của họ, chạy lại toàn bộ suite: **164 passed, 0 failed, 0 skipped**. Không phát hiện bug trong tool có sẵn (chưa có gì để ghi cho REPORT B5).

### 3.6. Điều phối và nộp bài

- Quản lý merge PR #1–#9 của các nhánh `Duc`, `quyen_3961` vào `main`; xử lý các lần merge `origin/main` vào nhánh `hai`.
- Sắp xếp lại cây file nộp theo `SUBMISSION.md` (báo cáo nhóm → `report/team/group_report.md`, poster → `report/team/poster.html`, thêm `TEAM.md`).

## 4. Bằng chứng

- **File/commit/PR:**
  - Commit `0f90ee5`: kế hoạch `PLAN-INDEX.md` + run baseline v0.
  - Commit `f961d3e`: `artifacts/tools.yaml` v2 (viết lại mô tả 10 tool + convention args).
  - Commit `45060db`, `976bb35`: TASK-1/2 và cập nhật kế hoạch.
  - Commit `1a6c652` / `96505c6`: `app.py` (Streamlit) + transcript.
  - Commit `5f2d403`; merge các PR #1–#9.
  - Code: `starter_v0/app.py`, `starter_v0/requirements.txt`, `starter_v0/artifacts/tools.yaml`, `starter_v0/artifacts/_baseline/`, `starter_v0/tests/test_tools_todo.py`.
  - Run (đều hợp lệ: `provider_error_cases = 0`, `measured_cases = total_cases`):
    - `starter_v0/runs/v0_B_base_openrouter_20261110T160101187649.json`: baseline 0.65 (dòng `v0` trong version log).
    - `starter_v0/runs/v2_B_base_openrouter_20261110T174330086638.json`: v2 = 0.85, hồi quy R10/M06 (dòng `v2`).
    - `starter_v0/runs/v2_B_base_openrouter_20261110T174610790159.json`: test cô lập prompt v0 + tools v2 = 0.80.
  - Transcript: `starter_v0/transcripts/v3_openrouter_20261110T194324903467.transcript.json` (5 lượt), `starter_v0/transcripts/v3_openrouter_20261110T215800069030.transcript.json` (send end-to-end), `starter_v0/transcripts/v3_openrouter_20261110T185545472999.transcript.json` (bản cũ).
  - UI: `starter_v0/app.py`; link public qua Cloudflare Tunnel (xem mục A1 group report).
- **AI/công cụ đã dùng và cách tự kiểm tra kết quả:**
  - **Công cụ:** AI hỗ trợ viết UI Streamlit, dựng vòng chat và điền test.
  - **Cách tự kiểm tra:** không tin kết quả chỉ vì AI báo "xong"; mỗi kết luận đối chiếu với một lần chạy thật:
    - Chạy `streamlit run` rồi gọi `/_stcore/health` và chạy `AppTest` để xác nhận UI render đúng (message + expander tool call) chứ không chỉ đọc code.
    - Chạy `pytest` sau mỗi thay đổi, gồm cả `test_tool_contract.py` (kiểm `tools.yaml` khớp code).
    - Chạy `chat.py` thật và đọc lại transcript JSON để xác nhận routing/args và luồng `clarify` → `send`.
    - v2 không cải thiện thì ghi trung thực kết quả âm thay vì giữ lại; chạy thêm run cô lập để chắc nguyên nhân.

## 5. Tự đánh giá

**Làm tốt:**
- Hoàn thành phần UI **bắt buộc** của lab: `streamlit run app.py` chạy được, chat multi-turn, hiện tool call + args + kết quả, và có **link public** để team khác thử.
- Bao phủ đủ 3 tình huống quan trọng trong transcript: research bình thường, thiếu thông tin → hỏi lại (không đoán), và xác nhận trước khi `send` (kèm bằng chứng gửi thật end-to-end).
- Điền đủ stub test tool có sẵn ⇒ `pytest` **0 skipped, 0 failed**; giữ đúng vùng file của mình nên 3 người làm song song không xung đột.
- Chạy và ghi baseline v0 (kèm độ dao động ±0.05) làm mốc so sánh cho cả nhóm.

**Chưa tốt / bài học:**
- **v2 làm điểm giảm (0.95 → 0.85):** giả thuyết "sửa mô tả tool là đủ để sửa R12" sai; mô tả chi tiết hơn còn gây hồi quy R10/M06. Bài học: lỗi **ưu tiên rule** phải sửa ở `system_prompt.md`, không phải ở `tools.yaml`.
- **`RAPIDAPI_KEY` rỗng** trên máy chạy ⇒ `timeline`/`social_search` lỗi `RuntimeError` khi chạy thật (eval vẫn PASS vì chỉ chấm routing/args). Đây là gap vận hành, cần key thật để demo live trọn vẹn.
- **Link `trycloudflare` là tạm thời**, sống theo phiên `cloudflared`; mở lại tunnel sẽ ra URL khác và phải cập nhật báo cáo.
- Mọi kết quả chỉ đo trên một model (`gpt-4o-mini`); nhóm chưa chạy Small Local Model Challenge (bonus) nên chưa kiểm chứng prompt/tools tối ưu có còn đúng với model nhỏ hay không.
