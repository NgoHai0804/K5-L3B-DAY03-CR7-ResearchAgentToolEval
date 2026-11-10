# TASK 3 — 4 tool mới của nhóm: `rank_items`, `wiki`, `github_repo`, `hf_models`

**Owner:** Người 3 — Quyền Hoàng (nhánh `quyen_3961`)
**Trạng thái:** DONE — 4 tool đã code, có TOOL.md, đã đăng ký, có unit test, có eval case, đã merge vào `main`.
**Ưu tiên:** P0 cho `rank_items` (nhiệm vụ bắt buộc "≥ 1 tool mới"); P1 cho 3 tool còn lại (điều kiện điểm thưởng "UI + hơn 3 tool mới").

> **Phân công 3 người:** Người 1 (Minh Đức) lo `system_prompt.md` + `data/eval_group.json` + chạy eval (TASK-1).
> Người 2 (Ngô Ngọc Hải) lo `tools.yaml` phần thân + UI + transcript + stub test có sẵn (TASK-2).
> Task này lo **code tool mới**, **khai báo ở CUỐI** `tools.yaml`, unit test và eval case của tool mới.

Tài liệu kỹ thuật đầy đủ (cách hoạt động, ví dụ input/output, ablation): [`starter_v0/tools/TEAM_TOOLS.md`](../starter_v0/tools/TEAM_TOOLS.md).

---

## 1. Lịch sử commit (nhánh `quyen_3961`)

| Commit | Thời điểm | Nội dung | Merge vào `main` |
|---|---|---|---|
| `f373a46` | 2026-11-10 17:59 | Thêm `rank_items`: `tool.py`, `TOOL.md`, đăng ký `TOOL_FUNCTIONS`, khối YAML soạn sẵn `artifacts/rank_items_block.yaml`, run thử `v3-rank_*` | PR #3 (`36e2007`) |
| `c80f643` | 2026-11-10 19:00 | Thêm `wiki`, `github_repo`, `hf_models`; append cả 4 khối vào cuối `tools.yaml` (xoá `rank_items_block.yaml`); viết test trong `tests/test_tools_todo.py`; 4 case G01–G04 trong `eval_group.json`; viết `tools/TEAM_TOOLS.md`; run base/extension/group v3 | PR #5 (`5ea082b`) |

Sau đó nhánh `quyen_3961` được đồng bộ lại với `Duc` qua PR #6 (`2482819`).

## 2. File được sở hữu

| File | Được làm gì |
|---|---|
| `starter_v0/tools/rank_items/{tool.py,TOOL.md}` | Tạo mới |
| `starter_v0/tools/wiki/{tool.py,TOOL.md}` | Tạo mới |
| `starter_v0/tools/github_repo/{tool.py,TOOL.md}` | Tạo mới |
| `starter_v0/tools/hf_models/{tool.py,TOOL.md}` | Tạo mới |
| `starter_v0/tools/__init__.py` | Thêm 4 import + 4 key trong `TOOL_FUNCTIONS` |
| `starter_v0/artifacts/tools.yaml` | **Append** 4 khối ở CUỐI file (sau `paper_text`), dưới comment `Team tools (v3, Role C)` |
| `starter_v0/tests/test_tools_todo.py` | Thêm test cho 4 tool mới |
| `starter_v0/data/eval_group.json` | Case G01–G04 |
| `starter_v0/tools/TEAM_TOOLS.md` | Tài liệu tổng hợp |

Ngoại lệ đã thống nhất với Người 2: thêm **một câu** vào mô tả `lookup` (phần thân `tools.yaml`) để sửa hồi quy E06, xem §5.

---

## 3. Tóm tắt 4 tool

| Tool | Làm gì | Nguồn / API | Key | Tham số | Đầu ra |
|---|---|---|---|---|---|
| `rank_items` | Bỏ trùng + xếp hạng item **đã có** trong hội thoại (từ `lookup`, `social_search`, `papers`, hoặc danh sách user dán). Không lấy dữ liệu mới | Offline, không gọi mạng | Không | `items`, `sort_by` (`recency`/`score`/`relevance`), `query`, `dedupe`, `top_k` | `{tool, sort_by, items, count, removed}` |
| `wiki` | Tra kiến thức nền ổn định: khái niệm, người, tổ chức ("X là gì", "Y là ai") | Wikipedia MediaWiki Action API, 1 request (`generator=search` + `prop=extracts`) | Không | `query`, `lang` (`en`/`vi`, mặc định `en`), `sentences` (1–10) | `{items, found}`, có cờ `is_disambiguation` |
| `github_repo` | Metadata **một** repo: star, fork, issue, language, license, topics, lần push cuối, archived | GitHub REST: `GET /repos/{owner}/{name}`; tên trống → `GET /search/repositories` | Tuỳ chọn `GITHUB_TOKEN` (60 → 5000 req/giờ) | `repo` (`owner/name`, URL, hoặc tên trống) | `{items, found, repo}` |
| `hf_models` | Tìm model open-weight trên Hugging Face, hoặc chi tiết một model: downloads 30 ngày, likes, license, task, arXiv id | Hugging Face Hub API `/api/models` | Tuỳ chọn `HF_TOKEN` | `query`, `model_id`, `task`, `sort_by` (`downloads`/`likes`/`trending`/`recent`), `limit` (1–20) | `{items, found}` |

Quy ước chung của cả 4 tool: đầu vào xấu hoặc lỗi HTTP trả **error dict**, không raise; tham số số được ép kiểu và kẹp biên (`"5"` → 5, `True` → mặc định); kết quả trả về là dữ liệu tham khảo, không phải chỉ dẫn.

## 4. Checklist thực thi

### P1 — Code + đăng ký
- [x] `tools/<tên>/tool.py` cho cả 4 tool, mỗi tool tự chứa (self-contained).
- [x] `tools/<tên>/TOOL.md` có frontmatter đúng contract (`name`, `track`, `kind`, `provider`, `requires_env`, `inputs`, `outputs`, `side_effect`).
- [x] Đăng ký trong `tools/__init__.py` (`TOOL_FUNCTIONS`).
- [x] Append khai báo vào cuối `artifacts/tools.yaml`, description có "khi nào dùng / KHÔNG dùng".
- [x] `pytest tests/test_tool_contract.py` xanh (khai báo ↔ code ↔ TOOL.md ↔ eval khớp nhau).

### P2 — Unit test (≥ 3 test/tool)

| Tool | Hàm test | Trường hợp (tính cả `parametrize`) |
|---|---:|---:|
| `rank_items` | 14 | 14 |
| `wiki` | 10 | 17 |
| `github_repo` | 10 | 15 |
| `hf_models` | 12 | 18 |

- [x] Mỗi tool đủ 3 nhóm: happy path (assert cả **request gửi đi** lẫn **kết quả**), input xấu từ model, nhánh lỗi trả error dict.
- [x] Test offline: mọi HTTP mock bằng `fake_http`.
- [x] `pytest -q` toàn bộ = **164 passed, 0 failed, 0 skipped**.

### P3 — Eval case route tới tool mới

| Case | Câu hỏi (rút gọn) | Kỳ vọng |
|---|---|---|
| G01 | "Đây là kết quả... bỏ trùng, giữ 2 bài điểm cao nhất" | `rank_items(sort_by=score, top_k=2)` |
| G02 | "Transformer trong deep learning là gì?" | `wiki` |
| G03 | "Repo langchain-ai/langchain bao nhiêu star, còn maintain không?" | `github_repo(repo="langchain-ai/langchain")` |
| G04 | "Trên Hugging Face, model speech-to-text nào tải nhiều nhất?" | `hf_models` |

### P4 — Gọi API thật (không mock)
- [x] `wiki`: bài tiếng Anh, tiếng Việt, trang định hướng ("Mercury"), từ khoá không tồn tại.
- [x] `github_repo`: `owner/name`, URL có `.git`, tên trống `langchain`, repo không tồn tại, input rỗng.
- [x] `hf_models`: tìm theo từ khoá, chi tiết model, model không tồn tại (401), lọc task, sort trending, `sort_by` sai.

---

## 5. Bug tìm được và cách sửa

| Tool | Bug | Sửa | Regression test |
|---|---|---|---|
| `rank_items` | Code mẫu PLAN-v3: `score: "abc"` crash `ValueError` | coi như 0 | có |
| `rank_items` | `top_k="2"` âm thầm thành 10 | ép kiểu → 2 | có |
| `rank_items` | `top_k=True` thành 1 | dùng mặc định 10 | có |
| `rank_items` | `sort_by="relevance"` được nhận nhưng không sắp xếp | sắp theo độ trùng từ khoá với `query` | có |
| `rank_items` | `.../a/` và `.../a` không coi là trùng | bỏ `/` cuối khi so khớp | có |
| `wiki` | Câu hỏi tiếng Việt → model chọn `lang="vi"`, ra sai bài | mô tả `lang`: "ngôn ngữ của Wikipedia, KHÔNG phải ngôn ngữ câu hỏi" → 8/8 lần đúng | — (lỗi của model) |
| `github_repo` | Tìm tên trống `langchain` sắp theo star → ra `microsoft/markitdown` | dùng thứ tự khớp mặc định + ưu tiên trùng tên chính xác | có |

**Hồi quy E06 (extension):** sau khi thêm 4 tool, E06 ("làm bản tin AI hôm nay, nhưng kiểm tra policy **trước**") tụt 1.0 → 0.9: model chỉ gọi `policy`, bỏ `lookup`. Ablation từng tool: `wiki` gây mạnh nhất (0/3). 7 cách sửa ở mô tả `wiki` và ở prompt đều không ăn. Cách sửa đã kiểm chứng: thêm vào **mô tả `lookup`** câu "Yêu cầu làm bản tin / tin tức luôn cần lookup, kể cả khi user muốn kiểm tra thêm policy: gọi cả hai trong cùng lượt" → E06 3/3.

## 6. Kết quả (chốt 2026-11-10)

| Suite | Run | case_accuracy | Ghi chú |
|---|---|---:|---|
| base (20) | `runs/v3_B_base_openrouter_20261110T185801088833.json` | 1.0 | Đối chứng không có tool mới: 0.85 (2 lần). Tool mới bị gọi 0 lần trong base |
| extension (10) | `runs/v3_B_extension_openrouter_20261110T185831810038.json` | 1.0 | Sau khi sửa mô tả `lookup` (trước: 0.9 do E06) |
| group (4) | `runs/v3_B_group_openrouter_20261110T185844156200.json` | 0.75 | Chỉ G03 fail: gọi `github_repo` **2 lần** cùng args (`unnecessary_tool`) |

Artifact khi chốt task này: `v3+p15fc51fabfe3+t5c1aa1b29a85`.

**Bàn giao cho Người 1 (đã xử lý trong TASK-1, commit `decd5a5`):** G03 không sửa được bằng mô tả tool → Người 1 thêm routing cho 4 tool + rule "không gọi cùng tool hai lần với cùng args" vào `system_prompt.md` → group 14 case = 1.0 (`runs/v3_B_group_openrouter_20261110T191826129492.json`).

## 7. Rủi ro còn lại

- `github_repo` không token: 60 req/giờ (search 10 req/phút). Demo đông người có thể chạm rate limit → tool trả error dict gợi ý đặt `GITHUB_TOKEN` hoặc truyền `owner/name`.
- Thêm tool làm các case "nhiều nguồn" (E06) kém ổn định. Mỗi lần đổi prompt hoặc `tools.yaml` phải chạy lại base + extension, không dùng lại kết quả ablation cũ.
- `wiki` không dùng cho tin mới; nếu model gọi `wiki` cho câu hỏi thời sự thì đó là lỗi routing, cần thêm case eval.
