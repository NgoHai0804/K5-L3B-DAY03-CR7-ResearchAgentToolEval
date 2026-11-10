# Báo cáo cá nhân — HoangMinhQuyen-2A202603961

## 1. Thông tin thành viên

- Họ tên: Hoàng Minh Quyền
- MSSV: 2A202603961
- Email: quyentryhard@gmail.com
- GitHub: [EddyTryToCode](https://github.com/EddyTryToCode)
- Nhóm: CR7 (L3B), nhánh làm việc `quyen_3961`
- Vai trò: C — Tool mới & test (TASK-3)

## 2. Phần việc phụ trách

Theo [plans/PLAN-INDEX.md](../../plans/PLAN-INDEX.md), nhóm chia 3 vai trò, mỗi người sở hữu một vùng file riêng để làm song song không xung đột. Phần của tôi:

- Viết tool mới: `starter_v0/tools/<tên>/tool.py` + `TOOL.md`, đăng ký trong `tools/__init__.py`.
- Khai báo tool mới ở **cuối** `artifacts/tools.yaml` (phần thân là của Role B; `system_prompt.md` là của Role A).
- Unit test cho tool mới (≥ 3 test mỗi tool), giữ `pytest` xanh.
- Eval case trong `data/eval_group.json` để kiểm tra model route đúng tới tool mới.
- Đo xem tool mới có làm hỏng các case cũ không (base, extension).

## 3. Đóng góp cụ thể

### 3.1. Chọn tool

Tôi chọn tool theo 3 tiêu chí: nguồn **uy tín**, API **ổn định** và không cần key, và **lấp khoảng trống** mà 10 tool có sẵn chưa làm được. Trước khi viết code, tôi gọi thử từng API thật.

| Tool | Làm gì | Vì sao chọn |
|---|---|---|
| `rank_items` | Bỏ trùng, xếp hạng (mới nhất / điểm / liên quan), cắt top N cho kết quả đã thu thập | Tool đề xuất trong PLAN-v3; chạy offline; dùng được cho kết quả của mọi tool tìm kiếm |
| `wiki` | Tra kiến thức nền trên Wikipedia | Chưa có tool nào cho câu "X là gì / Y là ai" |
| `github_repo` | Star, fork, license, lần push cuối, archived của một repo | Số liệu chính xác tại thời điểm hỏi, từ API chính thức |
| `hf_models` | Tìm / xem model open-weight trên Hugging Face | Tin AI hay hỏi "model nào phổ biến, license gì" |

Các phương án đã thử và bỏ, có lý do:
- **`hn_search` (Hacker News):** đã code xong và kiểm chứng, nhưng phạm vi quá hẹp (chỉ một diễn đàn).
- **OpenAlex (tra cứu học thuật):** dễ giành case của `papers` trong bộ extension (E04, E07, E10).

### 3.2. Thiết kế chung cho 4 tool

- Không bao giờ raise exception: mọi lỗi trả về error dict `{"tool", "error", "message"}`, để model đọc được và tự xử lý.
- Chấp nhận đầu vào "bẩn" mà model hay gửi: `"5"` được hiểu là `5`, giá trị được giới hạn trong khoảng hợp lệ, `true` ở chỗ cần số thì bị coi là không hợp lệ.
- Kiểm tra đầu vào trước khi gọi mạng; "không tìm thấy" trả `found: false` chứ không báo lỗi.
- Mỗi lần gọi đúng **một** request mạng.
- Mô tả trong `tools.yaml` theo khuôn: làm gì → khi nào dùng → khi nào **không** dùng, và dùng tool nào thay.

### 3.3. Bug tìm được và đã sửa (mỗi bug code đều có regression test)

| # | Tool | Bug | Cách phát hiện |
|---|---|---|---|
| 1–5 | `rank_items` | Code mẫu trong PLAN-v3: `score:"abc"` làm crash; `top_k="2"` âm thầm thành 10; `top_k=True` thành 1; `sort_by="relevance"` không sắp xếp gì; `url/` và `url` không bị coi là trùng | So code mẫu với bản sửa trên cùng đầu vào xấu |
| 6 | `github_repo` | Tìm `langchain` ra `microsoft/markitdown`, vì code sắp kết quả theo số star | Gọi API thật |
| 7 | `wiki` | Câu hỏi tiếng Việt làm model chọn `lang="vi"`, và Wikipedia tiếng Việt trả **sai bài** (GPT thay vì Transformer) | Kiểm tra routing bằng model thật; sửa mô tả tham số `lang`, sau đó đúng 8/8 lần |

### 3.4. Unit test

46 hàm test (64 trường hợp tính cả `parametrize`) trong `starter_v0/tests/test_tools_todo.py`: `rank_items` 14, `wiki` 10, `github_repo` 10, `hf_models` 12. Mỗi tool có đủ 3 nhóm: happy path (kiểm tra cả **request gửi đi** lẫn **kết quả trả về**), đầu vào xấu, và nhánh lỗi. Test chạy offline vì HTTP được mock bằng `fake_http`. Trên nhánh của mình tôi cũng điền 14 stub cho các tool có sẵn. Toàn bộ suite: **164 passed, 0 failed, 0 skipped**.

### 3.5. Eval case và đo hồi quy

- 4 case G01–G04 trong `data/eval_group.json`, mỗi case route tới một tool mới. Lần đầu: 3/4 pass. G03 fail vì model gọi `github_repo` hai lần cho cùng một repo. Tôi thử sửa mô tả tool và thêm một dòng vào bản sao prompt, cả hai không có tác dụng nên tôi hoàn tác. Đức đã sửa được ở v3-final bằng rule "không gọi trùng tool cùng args" trong prompt.
- **Base:** tool mới bị gọi 0 lần trong 20 case, điểm không giảm.
- **Extension: tìm ra một hồi quy thật.** Thêm 4 tool làm E06 tụt (1.0 → 0.9, 3/3 lần). Câu E06 là "Làm bản tin AI hôm nay, nhưng kiểm tra policy **trước**", và model chỉ gọi `policy`, bỏ mất `lookup`. Tôi làm ablation bằng cách thêm hoặc bỏ từng tool, mỗi cấu hình chạy 3 lần. Kết quả: `wiki` ảnh hưởng mạnh nhất, nhưng tool nào cũng làm case này kém ổn định. Tôi thử 7 cách sửa thất bại (đổi mô tả `wiki`, đổi tên, bỏ tham số, sửa bản sao prompt) rồi mới tìm được cách đúng: thêm một câu vào **mô tả của `lookup`**, tức chính tool bị bỏ sót: "yêu cầu làm bản tin luôn cần lookup, kể cả khi kiểm tra thêm policy". Sau khi sửa, cả 3 suite chạy 2 lần đều giữ điểm: base 1.0, extension 1.0.

### 3.6. Tài liệu và nộp bài

- [starter_v0/tools/TEAM_TOOLS.md](../../starter_v0/tools/TEAM_TOOLS.md): mô tả chi tiết từng tool (đầu vào, cách hoạt động, đầu ra, lỗi, giới hạn, test, kết quả đo, toàn bộ bảng ablation E06).
- Sắp xếp lại file theo `SUBMISSION.md`: chuyển `REPORT.md` → `report/team/group_report.md` (giữ lịch sử git), chuyển poster sang `report/team/poster.html`, lấy `TEAM.md`, `RUBRIC.md`, `RULES.md`, `CHECKPOINTS.md`, `docs/` từ repo đề bài, sửa các đường dẫn cũ; viết `TEAM.md` và báo cáo này.

## 4. Bằng chứng

- File/commit/PR:
  - Commit `f373a46`: thêm `rank_items` (merge qua PR #3).
  - Commit `c80f643`: thêm `wiki`, `github_repo`, `hf_models`, unit test, eval case G01–G04, `TEAM_TOOLS.md`, câu sửa E06 trong mô tả `lookup` (merge qua PR #5).
  - Code: `starter_v0/tools/{rank_items,wiki,github_repo,hf_models}/`, khối cuối `starter_v0/artifacts/tools.yaml`, `starter_v0/tests/test_tools_todo.py`.
  - Run (đều hợp lệ: `provider_error_cases = 0`, `measured_cases = total_cases`):
    - `starter_v0/runs/v3_B_base_openrouter_20261110T185801088833.json`: base 1.0, tool mới bị gọi 0 lần (dòng `v3-tools` trong `version_log.csv`).
    - `starter_v0/runs/v3_B_extension_openrouter_20261110T185831810038.json`: extension 1.0 sau khi sửa E06.
    - `starter_v0/runs/v3_B_group_openrouter_20261110T185844156200.json`: group 3/4, G03 fail như đã mô tả.
    - `starter_v0/runs/v3_B_extension_openrouter_20261110T183816399153.json`: extension 0.9, bằng chứng của hồi quy E06 trước khi sửa.
  - Transcript có dùng tool mới: `starter_v0/transcripts/v3_openrouter_20261110T194324903467.transcript.json` (turn 1 `wiki`, turn 2 `github_repo` gọi một lần).
- AI/công cụ đã dùng và cách tự kiểm tra kết quả:
  - **Công cụ:** Claude Code (Anthropic), dùng để đọc hướng dẫn, đề xuất và viết code tool, viết test, chạy eval, phân tích run JSON và viết tài liệu.
  - **Cách tự kiểm tra:** không tin kết quả chỉ vì AI nói "xong". Mỗi kết luận đều được đối chiếu với một bằng chứng chạy thật:
    - Gọi **API thật** của từng tool trước và sau khi viết code. Bug #6 được bắt nhờ bước này.
    - Chạy `pytest` sau mỗi thay đổi, kể cả contract test kiểm tra `tools.yaml` khớp với code.
    - Gửi câu hỏi tiếng Việt cho **model thật** để kiểm tra routing. Bug #7 được bắt nhờ bước này.
    - Mọi so sánh "có / không có tool mới" đều có **run đối chứng**, và chạy lặp 2–3 lần vì điểm base tự dao động ±0.05–0.15 giữa các lần chạy cùng cấu hình.
    - Khi một cách sửa không cải thiện kết quả thì hoàn tác, không giữ lại.
    - Khi kết quả cũ mâu thuẫn với kết quả mới thì chạy lại thay vì dùng lại số cũ. Kết luận ban đầu "thủ phạm E06 là `wiki`" đã được sửa nhờ bước này.

## 5. Tự đánh giá

**Làm tốt:**
- Hoàn thành vượt yêu cầu: 4 tool mới (yêu cầu ≥ 1; ≥ 4 để có bonus), mỗi tool có ≥ 10 test thay vì 3, `pytest` 0 skipped.
- Làm việc dựa trên bằng chứng: các bug đều được phát hiện bằng chạy thật, không phải bằng đọc code. Hồi quy E06 được tìm ra vì tôi chủ động đo cả bộ extension (bộ tuỳ chọn), không chỉ bộ base.
- Giữ đúng vùng file của mình theo kế hoạch, nên các PR merge vào `main` không xung đột với phần của Đức và Hải.

**Chưa tốt / bài học:**
- Mất thời gian ở bước chọn tool: tôi làm `hn_search` trước rồi mới nhận ra phạm vi quá hẹp. Lẽ ra nên chốt tiêu chí chọn tool (uy tín, ổn định, phạm vi) ngay từ đầu.
- Kết luận đầu tiên về E06 chỉ đúng một phần. Sau khi nhóm merge prompt mới, cấu hình "bỏ `wiki`" từ pass 3/3 chuyển sang fail 0/3. Bài học: mỗi lần prompt hoặc `tools.yaml` thay đổi, phải chạy lại đối chứng thay vì dùng lại kết quả cũ.
- Không sửa được G03 trong phạm vi file của mình, vì lỗi gọi trùng nằm ở rule của prompt. Phần này do Đức sửa.
- Unit test dùng HTTP giả lập, nên không phát hiện được khi API thật đổi định dạng. Phần đó chỉ được kiểm bằng các lần gọi API thật thủ công.
- Mọi kết quả chỉ đo trên một model (`gpt-4o-mini`). Nhóm chưa kiểm tra tool mới trên model local (Small Local Model Challenge).
