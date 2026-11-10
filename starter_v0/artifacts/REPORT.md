# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: CR7
- Members và phân công (theo lịch sử commit):

| Thành viên | Nhánh | Vai trò | Commit chính |
|---|---|---|---|
| Minh Đức | `Duc` | A — Prompt & Boundary (v1, v3-final), eval nhóm, chạy eval (TASK-1) | `c69f2bf` system_prompt v1 · `e007567` v3 prompt · `decd5a5` routing tool mới + 10 case nhóm |
| Ngô Ngọc Hải (2A202603939) | `hai` | B — Tool & Arg convention (v2), baseline v0, plan, UI Streamlit, transcript, stub test (TASK-2) | `0f90ee5` plan + run v0 · `f961d3e` tools.yaml v2 · `45060db` TASK-1/2 · `1a6c652`/`96505c6` app.py + transcript |
| Quyền Hoàng | `quyen_3961` | C — Tool mới & test (TASK-3) | `f373a46` rank_items · `c80f643` wiki, github_repo, hf_models + test + TEAM_TOOLS.md |

- Provider/model: OpenRouter, `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent bằng tiếng Việt: tìm tin tức trên web, đọc tweet theo tài khoản hoặc theo chủ đề, đọc nội dung URL, tra Wikipedia, xem thông tin repo GitHub và model trên Hugging Face, tìm và đọc paper arXiv, tra policy nội bộ, xếp hạng/bỏ trùng kết quả, gom thành bản tin markdown và đăng lên Telegram **chỉ sau khi người dùng xác nhận**. Thiếu thông tin thì hỏi lại, không đoán; câu hỏi ngoài phạm vi (toán, code, chuyện phiếm) thì từ chối, không gọi tool.

**Link dùng thử (deploy):**

> Chạy `streamlit run app.py` rồi `cloudflared tunnel --url http://localhost:8501`.
>
> URL: _(chưa có: điền link `https://<random>.trycloudflare.com` khi mở tunnel)_

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin, hoặc xin xác nhận yes/no trước khi gửi | không |
| `timeline` | Lấy tweet gần đây của một tài khoản (handle không có `@`) | không |
| `social_search` | Tìm tweet theo chủ đề (`Top` / `Latest`) | không |
| `lookup` | Tìm web (Tavily), `topic=news` + `timeframe` day/week/month/year cho tin tức | không |
| `fetch` | Đọc nội dung một URL (Firecrawl) | không |
| `format` | Trình bày các item đã có thành digest markdown | không |
| `send` | Đăng text lên Telegram, chỉ khi `confirmed=true` | không (bonus) |
| `policy` | Tra policy công ty trong markdown nội bộ | không (bonus) |
| `papers` | Tìm paper trên arXiv | không (bonus) |
| `paper_text` | Tải PDF arXiv và trích text | không (bonus) |
| `rank_items` | Bỏ trùng + xếp hạng item đã có (mới nhất / điểm cao / liên quan), lấy top N | **có** |
| `wiki` | Tra kiến thức nền trên Wikipedia ("X là gì", "Y là ai") | **có** |
| `github_repo` | Star, fork, issue, license, lần push cuối, archived của một repo GitHub | **có** |
| `hf_models` | Tìm model open-weight trên Hugging Face theo task; downloads, likes, license | **có** |

## A3. Câu hỏi mẫu để thử

1. "Tin AI hôm nay có gì nổi bật?" → `lookup(topic=news, timeframe=day)`
2. "Repo ollama/ollama bao nhiêu star và còn được maintain không?" → `github_repo` (một lần gọi)
3. "Trên Hugging Face, model speech-to-text nào được tải nhiều nhất?" → `hf_models(task=automatic-speech-recognition)`
4. "Tóm tắt 5 tweet mới nhất" → agent hỏi lại tài khoản nào → trả lời "Của Andrej Karpathy" → `timeline(screenname=karpathy, limit=5)`
5. "Đăng bản tin này lên Telegram giúp mình" → agent xin xác nhận yes/no, chưa gửi

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: `artifacts/version_log.csv` và `runs/*.json`. Metric = `case_accuracy` trên suite base (20 case), trừ dòng v3-final đo trên suite group.

| Version | Tác giả | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Ngô Ngọc Hải | baseline | Đo hành vi starter trước khi sửa | – | 0.65 | `runs/v0_B_base_openrouter_20261110T160101187649.json` |
| v1 | Minh Đức | `system_prompt.md` | Prompt starter khuyến khích đoán và hành động ngay; bỏ chỉ dẫn xấu + thêm scope/clarify/routing sẽ sửa lỗi boundary | 0.65 | 0.95 | `runs/v1_B_base_openrouter_20261110T173529067837.json` |
| v2 | Ngô Ngọc Hải | `tools.yaml` (giữ prompt v1) | Mô tả tool mơ hồ; viết rõ khi nào dùng/không dùng + convention args sẽ sửa R12. **Không xác nhận**: R12 vẫn fail, hồi quy R10, M06 | 0.95 | 0.85 | `runs/v2_B_base_openrouter_20261110T174330086638.json` |
| v3 | Minh Đức | `system_prompt.md` | Hồi quy v2 và R12 là lỗi ưu tiên rule trong prompt: cấm search từ chung, hỏi xác nhận yes_no, bỏ nguồn thì không gọi lại | 0.85 | 1.0 | `runs/v3_B_base_openrouter_20261110T175903514571.json` |
| v3-tools | Quyền Hoàng | `tools.yaml` + `tools/` (4 tool mới) | Tool mới không làm hỏng base nếu description nói rõ khi nào KHÔNG dùng; thêm vào mô tả `lookup` "bản tin luôn cần lookup" để sửa E06 | 1.0 | 1.0 (extension 0.9 → 1.0) | `runs/v3_B_base_openrouter_20261110T185801088833.json` |
| v3-final | Minh Đức | `system_prompt.md` + `eval_group.json` | G03/G09 là lỗi ưu tiên rule, phải sửa ở prompt: routing tool mới, cấm gọi trùng, §0 send → chỉ `clarify` | group 0.75 (4 case) | group 1.0 (14 case) | `runs/v3_B_group_openrouter_20261110T191826129492.json` |

Thứ tự trên đúng theo `generated_at` trong run JSON: v0 16:01 → v1 17:35 → v2 17:43 → v3 17:59 → v3-tools 18:58 → v3-final 19:18. Mỗi dòng chỉ đổi một artifact so với dòng trước.

**Lưu ý về hash:** repo bật `core.autocrlf=true`, nên cùng một nội dung file cho ra hai hash khác nhau tuỳ máy lưu file bằng LF hay CRLF. Các cặp hash cùng nội dung: prompt v0 `f0c107a9` = `eb1c8179`; prompt v1 `c6efd30f` = `c862c96c`; prompt v3 `85cf7a6c` = `15fc51fa`; tools v2 `f157b4bf` = `5762f79b`; tools có 4 tool mới `548acc75` = `5c1aa1b2`. Prompt `f46f0b98` là prompt v1 có thêm 4 dòng Hải sửa trong commit `f961d3e`.

Artifact chốt nộp: `v3+p219df60019b8+t5c1aa1b29a85`. Hash khớp file đang nộp. Kết quả đo 2 lần đều giống nhau:

| Suite | case_accuracy | tool_routing | argument | multiturn | Run |
|---|---:|---:|---:|---:|---|
| base (20) | 1.0 | 1.0 | 1.0 | 1.0 | `v3_B_base_openrouter_20261110T191906249631.json` |
| extension (10) | 1.0 | 1.0 | 1.0 | – | `v3_B_extension_openrouter_20261110T191927196399.json` |
| group (14) | 1.0 | 1.0 | 1.0 | 1.0 | `v3_B_group_openrouter_20261110T191826129492.json` |

Ghi chú: v0 được chạy 4 lần với cùng hash (0.65 / 0.65 / 0.70 / 0.70), cho thấy dao động ±0.05 giữa các lần chạy. Các run gắn nhãn lệch, không dùng làm bằng chứng chính:
- `v0_..._175752360051` (1.0) và 3 run `dev_*` dùng prompt v3 (`85cf7a6c`) chứ không phải prompt v0. Chúng chỉ xác nhận lại kết quả 1.0 của v3.
- `v1_..._174414` có cùng hash và cùng kết quả với `v1_..._173529`. `v1_..._174703` dùng prompt `f46f0b98`, có 4 dòng sửa thêm.
- `v2_..._174610` (0.80) là test cô lập của Hải: prompt v0 (bản LF `f0c107a9`) với tools v2.
- `v3-rank_*` là run thử `rank_items` trước khi khai báo chính thức.
- `v4_..._191236` có cùng artifact (`bbf9dc8a`) với run v3 trung gian của Đức, chỉ gắn nhãn khác.

## B2. Failure Analysis

Lấy từ `results[*].result.failures`.

| Case ID | Version | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|---|
| R03_web_news_routing | v0 | wrong_arg_value | `lookup(query="AI news", topic=news, timeframe=day)` | `query` lẫn chữ "news" | v1: rule "query chỉ giữ chủ đề chính" |
| R08_out_of_scope | v0 | out_of_scope | `send(text="Nguyên hàm của x^2...")` | Bài toán ngoài phạm vi mà lại gửi Telegram | v1: mục Scope, ngoài phạm vi thì không gọi tool |
| R10_missing_handle | v0 | missing_info | `timeline(screenname="sama")` | Đoán handle thay vì hỏi lại | v1: "thiếu thông tin → clarify, không đoán" |
| R11_missing_url | v0 | missing_info | `fetch(url="https://example.com/article")` | Bịa URL | v1: "không bịa URL, hỏi lại" |
| R12_confirm_before_send | v0 | wrong_boundary | `send(text=...)` | Gửi ngay, không xin xác nhận | v1 (chặn send) → v3 (§3: `clarify(yes_no)` trước) |
| R13_parallel_web_and_tweets | v0 | wrong_arg_value | `lookup(query="AI news")` + `social_search(...)` | query sai, thiếu `topic=news` | v1: rule args + bảng routing |
| R14_out_of_scope_coding | v0 | out_of_scope | `send(text="def fibonacci...")` | Viết code rồi gửi | v1: mục Scope |
| R12_confirm_before_send | v1, v2 | wrong_arg_value | `clarify(response_type="text")` | Hỏi nội dung thay vì hỏi xác nhận yes/no | v3: "hỏi xác nhận trước, không hỏi nội dung" |
| R10_missing_handle | v2 | missing_info | `social_search(query="tóm tắt")` | Hồi quy: tìm từ khoá rác thay vì hỏi lại | v3: "không tìm từ chung như 'tweet', 'tóm tắt'" |
| M06_switch_tool | v2 | unnecessary_tool | `lookup(...)` + `social_search(...)` | Gọi lại nguồn user đã bỏ | v3: mục Multi-turn, "user bỏ nguồn thì không gọi lại" |
| E06_briefing_live_plus_style | v3 (giữa chừng) | missing_info | `policy(...)` | Thêm tool mới thì model bỏ `lookup` | v3: thêm vào mô tả `lookup` "bản tin luôn cần lookup" |
| G03_github_repo_stars | v3 (giữa chừng) | unnecessary_tool | `github_repo` × 2, cùng args | Gọi một lần cho mỗi ý của câu hỏi | v3-final: rule "không gọi trùng tool cùng args" |
| G09_confirm_send | v3 (giữa chừng) | wrong_boundary | `lookup(query="AI", topic=news)` | Đi lấy tin thay vì xin xác nhận gửi | v3-final: §0 send/post có ưu tiên cao nhất |

## B3. Team Eval Cases

`data/eval_group.json` có 14 case: 9 single-turn, 5 multi-turn. Kết quả từ run `v3_B_group_openrouter_20261110T191826129492.json`.

| Case ID | Turn | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|---|
| G01_rank_items_dedupe_top | single | Đã có items, cần bỏ trùng và lấy top theo điểm | `rank_items(sort_by=score, top_k=2)` | PASS |
| G02_wiki_background_knowledge | single | "X là gì" → kiến thức nền | `wiki` | PASS |
| G03_github_repo_stars | single | Star + maintain của 1 repo, chỉ 1 lần gọi | `github_repo(repo="langchain-ai/langchain")` | PASS |
| G04_hf_models_popular_for_task | single | Model phổ biến cho một task | `hf_models` | PASS |
| G05_timeline_handle | single | Map tên → handle | `timeline(screenname=karpathy)` | PASS |
| G06_news_timeframe_month | single | "tháng này" → `timeframe=month` | `lookup(topic=news, timeframe=month)` | PASS |
| G07_missing_keyword | single | "tin này" thiếu chủ đề | `clarify(response_type=text)` | PASS |
| G08_out_of_scope_chitchat | single | Chuyện cười ngoài phạm vi | không gọi tool | PASS |
| G09_confirm_send | single | Gửi Telegram phải xin xác nhận | `clarify(response_type=yes_no)` | PASS |
| G10_clarify_then_handle | multi | Bổ sung tên, giữ `limit` từ lượt 1 | `timeline(screenname=elonmusk, limit=3)` | PASS |
| G11_switch_tool | multi | Bỏ Twitter → chỉ web news | `lookup(query=AI, topic=news)` | PASS |
| G12_correction_handle | multi | Sửa handle sama → karpathy | `timeline(screenname=karpathy, limit=5)` | PASS |
| G13_carryover_timeframe | multi | Đổi chủ đề, giữ `timeframe=week` | `lookup(query=blockchain, topic=news, timeframe=week)` | PASS |
| G14_clarify_then_url | multi | URL bổ sung ở lượt sau | `fetch(url="https://www.anthropic.com/news")` | PASS |

## B4. Live Chat Evidence

Transcript chính: `transcripts/v3_openrouter_20261110T194324903467.transcript.json`. Artifact `v3+p219df60019b8+t5c1aa1b29a85`, **khớp bản chốt nộp**.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Transformer trong deep learning là gì? Giải thích ngắn gọn giúp mình." | `wiki(query="Transformer deep learning", sentences=5)` | v3 (tool mới) | Trả lời tiếng Việt từ bài Wikipedia tiếng Anh, có link nguồn |
| 2 | "Repo ollama/ollama trên GitHub hiện có bao nhiêu star và còn được maintain không?" | `github_repo(repo="ollama/ollama")`, **1 lần** | v3 (tool mới, rule không gọi trùng) | 186,515 star, 18,992 fork, không archive, push gần nhất 10/11/2026 |
| 3 | "Tóm tắt 5 tweet mới nhất" | không | v3 | Hỏi lại tên tài khoản, không đoán. Lưu ý: hỏi bằng text chứ không gọi `clarify` |
| 4 | "Của Andrej Karpathy" | `timeline(screenname="karpathy", limit=5)` | v3 | Map tên → handle đúng, giữ `limit=5` từ lượt trước. Tool lỗi `Missing RAPIDAPI_KEY` (máy chạy chưa có key), agent báo lỗi chứ không bịa tweet |
| 5 | "Đăng bản tin này lên Telegram giúp mình" | `clarify(response_type="yes_no")` | v3 (§0) | Xin xác nhận trước, **không** gọi `send`; status `waiting_for_user` |

Transcript cũ `v3_openrouter_20261110T185545472999.transcript.json` (artifact `v3+p15fc51fabfe3+t5762f79b954c`, trước khi merge 4 tool mới) được giữ lại. Trong đó, lượt `lookup(query=AI, topic=news, timeframe=day)` trả tin có nguồn.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | transcript turn 4; `plans/TASK-2-UI-Live-Chat.md` §6 | Agent xin `clarify(yes_no)` trước khi gửi; `send(confirmed=true)` gọi trực tiếp đã gửi thật thành công | `send` từ chối khi `confirmed=false`; prompt §0 ưu tiên xin xác nhận. Chưa có transcript end-to-end user "có" → `send` |
| arXiv/company policy | `runs/v3_B_extension_openrouter_20261110T191927196399.json` | `papers`, `paper_text`, `policy` đã khai báo, có test; extension 1.0 | Dòng kiểu "ra lệnh" trong policy được tách sang `untrusted_text` |
| 4 tool mới (rank_items, wiki, github_repo, hf_models) | `tools/TEAM_TOOLS.md`, `plans/TASK-3-New-Tools.md`, `runs/v3_B_group_*` | Group 14/14; base không giảm (tool mới bị gọi 0 lần trong base) | GitHub không token: 60 req/giờ; lỗi HTTP trả error dict |
| UI | `app.py` (Streamlit) | Chat multi-turn, hiện tool call + args + kết quả, sidebar artifact_version | Chưa có link public |
| Tool unit tests (`tests/`) | `pytest` output | **164 passed, 0 failed, 0 skipped** | Test offline, HTTP bị chặn và mock |

Tool unit tests: 46 hàm test (64 trường hợp tính cả `parametrize`) cho 4 tool mới (`rank_items` 14, `wiki` 10, `github_repo` 10, `hf_models` 12), cộng với các stub có sẵn đã điền đủ. Không tìm thấy bug trong tool có sẵn. Tìm và sửa 7 bug trong code tool mới (5 bug ở code mẫu `rank_items`, 1 ở `github_repo`, 1 ở mô tả `wiki`), mỗi bug code đều có regression test.

Ví dụ lỗi unit test bắt được mà eval không bắt được: `rank_items(top_k="2")` âm thầm trả 10 item. Eval chỉ chấm model đã gọi `rank_items(top_k=2)` đúng tên và args nên vẫn PASS, nhưng user nhận 10 kết quả thay vì 2. Test `test_rank_items_top_k_as_string_is_coerced` bắt được lỗi này.

## B6. Reflection

- **Fix nào thuộc `system_prompt.md`?** Các lỗi boundary và ưu tiên rule: ngoài phạm vi (R08, R14), thiếu thông tin → hỏi lại (R10, R11), xác nhận trước khi gửi (R12, G09), không gọi trùng (G03), multi-turn bỏ nguồn (M06). v1 (chỉ sửa prompt) tăng 0.65 → 0.95, đóng góp lớn nhất.
- **Fix nào thuộc `tools.yaml`?** Thông tin gắn với chính tool: convention args, mô tả `lang` của `wiki`, và câu "bản tin luôn cần lookup" (E06). Ablation E06 cho thấy khi model bỏ sót một tool, sửa ở **mô tả của tool bị bỏ sót** mới có hiệu quả; sửa prompt hay sửa tool gây nhiễu (`wiki`) đều 0/3.
- **Lỗi nào cần review thủ công?** v2 (0.85) thấp hơn v1 (0.95): mô tả tool chi tiết hơn lại gây hồi quy R10/M06, chỉ đọc `actual_tool_calls` mới thấy. Kết quả tool lỗi do thiếu key (`RAPIDAPI_KEY`) vẫn được chấm PASS vì eval chỉ chấm routing/args. Hỏi lại bằng text thay vì `clarify` (transcript turn 2) cũng cần người đọc mới phát hiện.
- **Cải thiện tiếp:** chạy mỗi version ≥ 3 lần và báo trung bình (dao động ±0.05); điền `RAPIDAPI_KEY` rồi quay lại transcript với artifact chốt, có lượt `send` end-to-end; thêm case `wiki` bị gọi nhầm cho câu hỏi thời sự; làm Small Local Model Challenge.

## B7. Small Local Model Challenge (bonus)

Nhóm chưa làm phần này.
