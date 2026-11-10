# Báo cáo cá nhân — TranMinhDuc-2A202603977

## 1. Thông tin thành viên

- Họ tên: Trần Minh Đức
- MSSV: 2A202603977
- Email: tranminhduc2324@gmail.com
- GitHub: [tmduc23](https://github.com/tmduc23)
- Nhóm: CR7 (L3B), nhánh làm việc `Duc`
- Vai trò: A — Prompt & Boundary (v1, v3, v3-final), eval nhóm, chạy eval (TASK-1)

## 2. Phần việc phụ trách

Theo [plans/PLAN-INDEX.md](../../plans/PLAN-INDEX.md), nhóm chia 3 vai trò, mỗi người sở hữu một vùng file riêng để làm song song không xung đột. Phần của tôi:

- **Role A:** `starter_v0/artifacts/system_prompt.md` cho các version v1, v3, v3-final.
- **Eval nhóm:** viết các case single/multi-turn trong `starter_v0/data/eval_group.json` và chạy eval cho từng version.
- **Chạy eval:** base suite (v1, v3), extension, group; ghi `artifacts/version_log.csv` và hoàn thiện group report + transcript chốt.
- **Kế hoạch:** [plans/TASK-1-Agent-Core-Tool-Eval.md](../../plans/TASK-1-Agent-Core-Tool-Eval.md).

## 3. Đóng góp cụ thể

### 3.1. v1 — viết lại `system_prompt.md` (0.65 → 0.95)

Prompt starter được cài **cố ý** các chỉ dẫn xấu (đoán thay vì hỏi, gửi không cần xác nhận, ép làm một bước). Tôi bỏ các chỉ dẫn đó và thêm:

- **§1 Scope:** câu hỏi ngoài phạm vi (toán, code, chuyện phiếm) → trả lời từ chối, gọi **no tool**.
- **§2 Missing information:** thiếu chủ đề/handle/URL → `clarify`, tuyệt đối không đoán, không bịa URL.
- **§3 Write actions cần xác nhận:** `send` không được gọi ngay trong lượt yêu cầu.
- **§4 Bảng Routing:** mỗi ý định người dùng → một tool + args; kèm **rule args**: `query` chỉ giữ chủ đề chính (không nhét "news"/"tin tức"), thời gian để ở `timeframe`, loại để ở `topic`.
- **§5 Multi-turn:** chỉ hành động theo lượt cuối, kế thừa chi tiết chưa đổi, áp dụng sửa lỗi.

**Kết quả: 0.65 → 0.95.** Sửa được R03, R08, R10, R11, R13, R14. Còn lại R12 (confirm-before-send) vẫn fail.

### 3.2. v3 — sửa hồi quy của v2 và R12 (0.85 → 1.0)

Sau khi Hải sửa `tools.yaml` (v2), điểm **giảm** 0.95 → 0.85 với hồi quy R10 (model gọi `social_search("tóm tắt")`) và M06 (gọi thừa nguồn user đã bỏ), R12 vẫn fail. Tôi kết luận đây là lỗi **ưu tiên rule trong prompt** (không phải mô tả tool) và sửa:

- **§2** cấm search bằng từ chung ("tweet", "tóm tắt") → sửa R10.
- **§3** yêu cầu gửi/đăng phải hỏi xác nhận bằng `clarify(response_type="yes_no")`, **không** hỏi nội dung → sửa R12.
- **§5** user bỏ một nguồn thì **không** gọi lại tool đó → sửa M06.

**Kết quả: 0.85 → 1.0**, lặp lại 1.0 ở 4 run khác cùng hash (kể cả các run `dev_*` và một run gắn nhãn `v0` nhưng dùng prompt v3).

### 3.3. v3-final — routing 4 tool mới + chống gọi trùng (group 0.75 → 1.0)

Sau khi Quyền thêm 4 tool mới (`rank_items`, `wiki`, `github_repo`, `hf_models`), tôi thêm vào prompt:

- **Routing cho 4 tool mới** (câu "X là gì / Y là ai" → `wiki`; repo GitHub → `github_repo`; model Hugging Face → `hf_models`; xếp hạng/bỏ trùng kết quả đã có → `rank_items`).
- **Rule "không gọi trùng tool cùng args"** trong một lượt — sửa G03 (model gọi `github_repo` hai lần cho cùng một repo).
- **§0 — rule ưu tiên cao nhất:** nếu lượt cuối là yêu cầu gửi/đăng, hành động **duy nhất** là `clarify(response_type="yes_no")`, không gọi tool khác (kể cả `lookup`) — sửa G09.

**Kết quả:** base giữ **1.0**; suite group 0.75 (4 case) → **1.0**. Bản trung gian chưa có §0 đạt 0.9286 — ghi trong version log. (Bộ case nhóm sau đó được rút về đúng 10 case không lặp base — xem 3.4.)

### 3.4. Eval case nhóm (`data/eval_group.json`)

Tôi phụ trách bộ case nhóm cho suite `group`. Bản đầu nhóm viết **14 case** (9 single + 5 multi), nhưng khi so lại với base thì phần lớn chỉ là biến thể của case có sẵn (R01/R06/R10/R11/R08/R14/R12 và M01–M06). Vì `RUBRIC.md` C5 yêu cầu **đúng 5 single + 5 multi** và ghi **"chép case có sẵn thì không tính"**, nhóm đã rút về **đúng 10 case MỚI, không lặp base** (dòng `v3-group` trong `version_log.csv`); 8/10 case route tới 4 tool mới:

| Case ID | Turn | Nội dung đo |
|---|---|---|
| G01_rank_items_dedupe_top | single | Đã có items → bỏ trùng, top theo điểm (tool mới) |
| G02_wiki_background_knowledge | single | "X là gì" → kiến thức nền (tool mới) |
| G03_github_repo_stars | single | Star + maintain 1 repo, 1 lần gọi (tool mới) |
| G04_hf_models_popular_for_task | single | Model phổ biến cho một task (tool mới) |
| G05_format_digest_from_items | single | Đã có items → chỉ trình bày digest |
| G06_switch_twitter_to_github | multi | Bỏ Twitter → tool mới `github_repo` |
| G07_hf_task_carryover_limit | multi | Lượt cuối sửa số lượng trên tool mới (`limit=3`) |
| G08_clarify_then_rank_items | multi | Thiếu items → hỏi lại → xếp hạng (tool mới) |
| G09_wiki_then_news_switch | multi | Bỏ wiki → chỉ tin tức |
| G10_correction_repo | multi | Sửa repo trên tool mới `github_repo` |

(Bốn case G01–G04 route tới 4 tool mới; `v3-group` = 10/10 PASS, run `runs/v3_B_group_openrouter_20261110T235944198197.json`.)

### 3.5. Chạy eval, version log, report

- Chạy base v1/v3, extension và group; đọc `summary.case_accuracy` / `tool_routing_accuracy` / `argument_accuracy` / `multiturn_accuracy` và `observed_mismatch` để rút ra failure analysis.
- Ghi `artifacts/version_log.csv` cho từng version (hash prompt/tools, lý do, giả thuyết, metric before/after, run file).
- Hoàn thiện group report và quay transcript chốt (`v3_openrouter_20261110T194324903467.transcript.json`).

## 4. Bằng chứng

- **File/commit/PR:**
  - Commit `c69f2bf`: `system_prompt.md` v1 (bỏ chỉ dẫn xấu + scope + clarify + routing).
  - Commit `e007567`: prompt v3 (cấm search từ chung, xác nhận `yes_no`, bỏ nguồn không gọi lại).
  - Commit `decd5a5`: routing 4 tool mới + rule không gọi trùng + 10 case nhóm.
  - Commit `6c4bbb9`: TASK-3 plan, version log, report và transcript chốt.
  - Merge qua PR #1, #4, #6, #8.
  - Code: `starter_v0/artifacts/system_prompt.md`, `starter_v0/data/eval_group.json`, `starter_v0/artifacts/version_log.csv`.
  - Run (đều hợp lệ: `provider_error_cases = 0`, `measured_cases = total_cases`):
    - `starter_v0/runs/v1_B_base_openrouter_20261110T173529067837.json`: base 0.95 (dòng `v1`).
    - `starter_v0/runs/v3_B_base_openrouter_20261110T175903514571.json`: base 1.0 (dòng `v3`).
    - `starter_v0/runs/v3_B_group_openrouter_20261110T191826129492.json`: group 1.0 trên bộ 14 case cũ (dòng `v3-final`); sau khi rút về bộ 10 case mới: `starter_v0/runs/v3_B_group_openrouter_20261110T235944198197.json`: group 1.0 (dòng `v3-group`).
  - Transcript: `starter_v0/transcripts/v3_openrouter_20261110T194324903467.transcript.json`.
- **AI/công cụ đã dùng và cách tự kiểm tra kết quả:**
  - **Công cụ:** AI hỗ trợ phân tích run JSON (tìm case FAIL, đọc `observed_mismatch`/`actual_tool_calls`) và soạn rule trong prompt.
  - **Cách tự kiểm tra:** mỗi kết luận đều đối chiếu với một run thật, không dựa vào cảm giác:
    - Mỗi version chỉ đổi **một** giả thuyết rồi chạy lại, so metric trước/sau; nếu không cải thiện thì đổi giả thuyết (v2 là ví dụ ghi trung thực kết quả âm).
    - Đọc `actual_tool_calls` thay vì chỉ xem điểm, nên phát hiện được hồi quy R10/M06 của v2.
    - Chạy lặp nhiều lần cùng cấu hình để loại nhiễu (base dao động ±0.05–0.15; v0 0.65/0.65/0.70/0.70).
    - Khi mô tả tool bị nghi là thủ phạm (E06), phối hợp với Quyền làm ablation và kết luận sửa ở **mô tả tool bị bỏ sót** (`lookup`) mới hiệu quả.

## 5. Tự đánh giá

**Làm tốt:**
- v1 (chỉ sửa prompt) đã tăng 0.65 → 0.95 — đóng góp lớn nhất, cho thấy phần lớn lỗi v0 là lỗi boundary/ưu tiên rule trong prompt.
- Chẩn đoán đúng các hồi quy của v2 là lỗi **ưu tiên rule** (không phải mô tả tool) và sửa ở prompt (v3: 1.0).
- v3-final đưa cả base và suite group lên 1.0 (giải quyết gọi trùng tool và xác nhận trước khi gửi); bộ case nhóm sau đó được rút về đúng 10 case (5 single + 5 multi) không lặp base và vẫn giữ 1.0.

**Chưa tốt / bài học:**
- v2 cho thấy thêm mô tả chi tiết hơn **không** tự động tốt hơn: sửa `tools.yaml` lại gây hồi quy R10/M06, phải sửa tiếp ở prompt. Bài học: ranh giới giữa "thông tin thuộc tool" và "rule ưu tiên thuộc prompt" rất quan trọng.
- Base eval dao động ±0.05–0.15 giữa các lần chạy cùng cấu hình; nhóm mới chạy lặp 2–4 lần thay vì báo trung bình trên nhiều lần.
- Kết quả tool lỗi do thiếu `RAPIDAPI_KEY` vẫn được chấm PASS vì eval chỉ chấm routing/args — đây là điểm eval không phủ được, cần review thủ công.
- Mọi kết quả chỉ đo trên một model (`gpt-4o-mini`); nhóm chưa chạy Small Local Model Challenge (bonus).
