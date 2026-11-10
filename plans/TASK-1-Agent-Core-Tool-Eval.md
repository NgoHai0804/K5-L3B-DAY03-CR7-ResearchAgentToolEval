# TASK 1 — Agent Core: khai báo tool mới + routing + 10 eval case + run lại

**Owner:** Người 1 (điền tên): ____________________
**Trạng thái:** TODO
**Ưu tiên:** P0 — Người 2 phụ thuộc vào `artifacts/tools.yaml` sau khi task này chốt.

> **Phân công 3 người:** Người 3 lo `tools/rank_items/**` + `tests/test_tools_rank_items.py` (không đụng gì khác).
> Vì Người 3 không sửa `artifacts/tools.yaml`, việc **khai báo** tool mới nằm trong task này.

> Không nằm trong task này (hoãn theo yêu cầu): `artifacts/REPORT.md`, `artifacts/version_log.csv`, `poster.*`.
> Người 2 điền 2 file đó ở vòng sau.

---

## 1. File được sở hữu (CHỈ những file này)

| File | Được làm gì |
|---|---|
| `starter_v0/artifacts/tools.yaml` | **CHỈ append** khối `rank_items` vào CUỐI file |
| `starter_v0/artifacts/system_prompt.md` | **CHỈ thêm** dòng routing cho `rank_items` |
| `starter_v0/data/eval_group.json` | Điền 10 case vào `cases` |
| `starter_v0/runs/*.json` | Run mới do task này sinh ra |

**KHÔNG đụng:** `tools/rank_items/**` + `tests/test_tools_rank_items.py` (Người 3), `app.py`, `requirements.txt`, `transcripts/**`, `tests/test_tools_todo.py` (Người 2).

---

## 2. Trạng thái hiện tại (đã kiểm tra)

- `tools/rank_items/tool.py` + `TOOL.md` đã có, đã đăng ký `TOOL_FUNCTIONS` (`tools/__init__.py:21,41`); **Người 3** đang hoàn thiện tool + `tests/test_tools_rank_items.py`.
- **`artifacts/tools.yaml` KHÔNG có `rank_items`** → model không thể gọi tool mới, nhiệm vụ "viết ≥1 tool mới" coi như chưa đạt. Đây là việc của task này.
- Khối YAML đã chuẩn bị sẵn: `artifacts/rank_items_block.yaml`.
- `data/eval_group.json` đang `"cases": []`.
- `pytest` hiện tại: `62 passed, 17 skipped` (17 skip thuộc `test_tools_todo.py` — của Người 2).
- `tests/test_tool_contract.py` **không** bắt lỗi thiếu khai báo (nó chỉ kiểm declared → code), nên đừng dựa vào nó để xác nhận việc append.

### Lỗi hash cần run lại (quan trọng)

Artifact đang nộp **không khớp** hash của run nào:

| Bản | File | Hash hiện tại | Run tương ứng | artifact_version của run |
|---|---|---|---|---|
| prompt | `artifacts/system_prompt.md` | `15fc51fabfe3…` | *(không có)* | – |
| tools | `artifacts/tools.yaml` | `f157b4bf1101…` | v2 | `v2+pf0c107a9d7a1+tf157b4bf1101` |
| – | – | – | v3 | `v3+p85cf7a6c7a8d+t5762f79b954c` (khác tools hiện tại) |

⇒ Kết quả **v3 = 1.0** (`runs/v3_B_base_openrouter_20261110T175903514571.json`) được tạo ở clone khác, **không tái lập được** từ file đang nộp. Bắt buộc chạy lại base v3 sau khi append tool.

---

## 3. Checklist thực thi

### P0 — Chuẩn bị
- [ ] `cd starter_v0` và kích hoạt venv: `.\.venv\Scripts\Activate.ps1`
- [ ] Xác nhận `.env` đã có `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY`, `RAPIDAPI_TWITTER_HOST` (không in key ra log).
- [ ] `python scripts/preflight_provider.py --provider openrouter` → pass.

### P1 — Gắn `rank_items` vào `artifacts/tools.yaml`
- [ ] Đọc `artifacts/rank_items_block.yaml` rồi **append nguyên khối vào CUỐI** `artifacts/tools.yaml` (sau khối `paper_text`), giữ indent **2 space** như file gốc.
- [ ] Không sửa bất kỳ dòng nào ở phần thân (10 tool cũ) — phần đó đã freeze ở v2.
- [ ] Kiểm YAML parse được: `python -c "import yaml,pathlib; d=yaml.safe_load(pathlib.Path('artifacts/tools.yaml').read_text(encoding='utf-8')); print(len(d['tools']), [t['name'] for t in d['tools']])"` → kỳ vọng **11 tool**, tên cuối là `rank_items`.
- [ ] `pytest tests/test_tool_contract.py -q` → xanh (mọi tool khai báo phải có implementation + TOOL.md đúng tên + param khai báo ⊆ signature).
- [ ] Xác nhận khớp 3 nơi: `tools/rank_items/TOOL.md` (frontmatter `name: rank_items`) ↔ `TOOL_FUNCTIONS["rank_items"]` ↔ `tools.yaml` (mục `rank_items`).

### P2 — Thêm routing cho `rank_items` trong `artifacts/system_prompt.md`
- [ ] Thêm **1 dòng** vào bảng Routing (§4) của `system_prompt.md`, ví dụ:
  `| Xếp hạng / bỏ trùng danh sách item ĐÃ CÓ (từ lookup, social_search, papers) | rank_items | sort_by = recency/score/relevance; top_k = số user nói; KHÔNG lấy dữ liệu mới |`
- [ ] Không sửa các rule khác (scope, clarify, confirm) — tránh regress R08/R10/R11/R14/R12.
- [ ] Ghi lại hash prompt mới để Người 2/dựng log dùng sau: `python -c "from pathlib import Path; from versioning import file_hash; print(file_hash(Path('artifacts/system_prompt.md'))[:12])"`.

### P3 — Unit test tool mới → **không thuộc task này** (Người 3 lo)

- [ ] Không tạo `tests/test_tools_rank_items.py` (Người 3 sở hữu), không sửa `tests/test_tools_todo.py` (Người 2 sở hữu).
- [ ] Chỉ cần **xác nhận** test của Người 3 xanh trước khi chốt: `pytest tests/test_tool_contract.py tests/test_tools_rank_items.py -q`.

> Bàn giao cho Người 3 (nếu chưa biết): output thật của `rank_items` là
> `{"tool", "sort_by", "items", "count", "removed"}`, lỗi là `{"tool", "error": "ValueError", "message"}`.
> Đừng assert `out == {"items": [], "count": 0, "removed": 0}` như skeleton trong `PLAN-v3-New-Tool-Eval.md`.

### P4 — 10 case nhóm trong `data/eval_group.json`
Schema bắt buộc mỗi case: `id`, `phase="B"`, `suite="group"`, (`query` **hoặc** `turns`), `failure_type` ∈ {`wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`}, `expect` = `{"tool_calls":[{"name":...,"args":{...}}]}` hoặc `{"no_tool": true}`, `metadata.what_it_tests`.

- [ ] 5 case single-turn (điền vào `"cases"`, giữ nguyên các key khác của file):

| id | query | expect | failure_type |
|---|---|---|---|
| G01_timeline_handle | "Tweet mới nhất của Andrej Karpathy" | `timeline({screenname:"karpathy"})` | wrong_tool |
| G02_news_timeframe_month | "Tin công nghệ tháng này" | `lookup({topic:"news", timeframe:"month"})` | wrong_arg_value |
| G03_missing_keyword | "Tìm giúp mình tin này" | `clarify({response_type:"text"})` | missing_info |
| G04_out_of_scope_chitchat | "Kể cho mình một câu chuyện cười" | `no_tool: true` | out_of_scope |
| G05_confirm_send | "Đăng bản tin này lên Telegram giúp mình" | `clarify({response_type:"yes_no"})` | wrong_boundary |

- [ ] 5 case multi-turn (dùng `turns`: mảng `{"role":"user","content":...}`, harness chỉ chấm lượt cuối):

| id | turns (rút gọn) | expect | failure_type |
|---|---|---|---|
| G06_clarify_then_handle | "Tóm tắt 3 tweet mới nhất" / "Của Elon Musk" / "Đúng 3 thôi" | `timeline({screenname:"elonmusk", limit:3})` | missing_info |
| G07_switch_tool | "Mọi người nói gì về AI trên Twitter?" / "Bỏ Twitter, tìm web tin tức" / "Giữ chủ đề AI" | `lookup({query:"AI", topic:"news"})` | wrong_tool |
| G08_correction_handle | "Tweet của Sam Altman" / "À nhầm, Karpathy" / "Lấy 5 cái" | `timeline({screenname:"karpathy", limit:5})` | wrong_arg_value |
| G09_carryover_timeframe | "Tin AI hôm nay" / "Còn robotics?" / "Chỉ robotics, vẫn hôm nay" | `lookup({query:"robotics", topic:"news", timeframe:"day"})` | wrong_arg_value |
| G10_clarify_then_url | "Tóm tắt bài này" / "https://openai.com/blog/gpt-5" / "Chỉ đọc link đó" | `fetch({url:"https://openai.com/blog/gpt-5"})` | missing_info |

- [ ] Mỗi case có `metadata.what_it_tests` mô tả rõ nó đo gì.
- [ ] **Không** đặt case dẫn tới `send(confirmed=true)` (tránh side-effect thật lên Telegram).
- [ ] Kiểm hợp lệ trước khi chạy: `python -c "import json,pathlib; d=json.loads(pathlib.Path('data/eval_group.json').read_text(encoding='utf-8')); print(len(d['cases']), {c['failure_type'] for c in d['cases']})"` → **10 case**, failure_type nằm trong 6 giá trị hợp lệ.
- [ ] (Tuỳ chọn) thêm 1 case chuỗi `rank_items` (đã có items → `rank_items({top_k:N})`) sau khi P1 xong, để đo tool mới trong group.

### P5 — Chạy lại eval sau khi đã có `rank_items`
- [ ] Base v3 (bắt buộc, để hash khớp artifact đang nộp):
  ```powershell
  python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
  ```
- [ ] Suite nhóm:
  ```powershell
  python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
  ```
- [ ] Đọc `summary.case_accuracy`, `tool_routing_accuracy`, `argument_accuracy`, `multiturn_accuracy` + `artifact_version` trong 2 run mới; ghi lại để Người 2 dựng `version_log.csv`/REPORT sau.
- [ ] Kiểm tool mới **không bị gọi thừa** làm giảm base (so với các base run trước).

---

## 4. Điều kiện đạt (DoD)

- [ ] `artifacts/tools.yaml` có **11 tool**, `rank_items` ở cuối; YAML parse OK.
- [ ] `pytest tests/test_tool_contract.py -q` xanh; test của Người 3 (`tests/test_tools_rank_items.py`) cũng xanh; `pytest -q` không tăng failed.
- [ ] `data/eval_group.json` có đúng **10 case** (5 single + 5 multi), mỗi case có `metadata.what_it_tests`.
- [ ] Có 2 run mới trong `runs/` (base v3 + group v3) và số liệu đã ghi lại.
- [ ] Base v3 `case_accuracy` ≥ 0.95; group suite chạy không lỗi validate.

## 5. Rủi ro

- Thêm tool mới ⇒ model có thể `extra_tool_call` ⇒ base giảm nhẹ. Nếu base < 0.95, thử làm rõ thêm mô tả `rank_items` ("KHÔNG dùng để lấy dữ liệu mới, KHÔNG dùng để trình bày").
- `test_tool_contract.py` **không** kiểm code → khai báo, nên tự kiểm 3 nơi bằng tay (mục P1).
- Đừng chạy `--suite group` trước khi `tools.yaml` có `rank_items` nếu case group có expect `rank_items` (sẽ `ValueError: Invalid expected tool`).
- Nếu Người 3 đổi signature `rank_items` (thêm/bớt param) thì khối `tools.yaml` phải khớp lại — `test_tool_contract.py` sẽ báo param khai báo không có trong code.
