# Team

## Thông tin nhóm

- Tên nhóm: CR7
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY03-CR7-ResearchAgentToolEval` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo: https://github.com/NgoHai0804/K5-L3B-DAY03-CR7-ResearchAgentToolEval
- Nhánh nộp: `main`
- Commit chốt: `1500ababee6221b135e4ec7ee689bad1da2ce524` (nhánh `main`)
- Provider / model dùng cho mọi run: OpenRouter, `openai/gpt-4o-mini`
- Artifact chốt: `v3+p219df60019b8+t5c1aa1b29a85` (xem B1 trong [group report](report/team/group_report.md))

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Trần Minh Đức | 2A202603977 | tranminhduc2324@gmail.com | https://github.com/tmduc23 | A — Prompt & Boundary (v1, v3, v3-final), eval nhóm, chạy eval (TASK-1) |
|   2 | Ngô Ngọc Hải | 2A202603939 | ngongochai0804@gmail.com | [NgoHai0804](https://github.com/NgoHai0804) | B — Tool & arg convention (v2), baseline v0, kế hoạch, UI Streamlit, transcript, stub test (TASK-2) |
|   3 | Hoàng Minh Quyền | 2A202603961 | quyentryhard@gmail.com | [EddyTryToCode](https://github.com/EddyTryToCode) | C — 4 tool mới, unit test, eval case cho tool mới (TASK-3) |

Phân chia file để làm song song không đụng nhau: [plans/PLAN-INDEX.md](plans/PLAN-INDEX.md).

## Cá nhân

Mỗi thành viên có báo cáo riêng trong `report/team/` theo dạng `MSSV_HoTen.md`:

| Thành viên | Báo cáo cá nhân |
|---|---|
| Minh Đức | [report/team/2A202603977_TranMinhDuc.md](report/team/2A202603977_TranMinhDuc.md) |
| Ngô Ngọc Hải | [report/team/2A202603939_NgoNgocHai.md](report/team/2A202603939_NgoNgocHai.md) |
| Hoàng Minh Quyền | [report/team/2A202603961_HoangMinhQuyen.md](report/team/2A202603961_HoangMinhQuyen.md) |

## TranMinhDuc-2A202603977

### Phần việc phụ trách

- Role A: `artifacts/system_prompt.md` (v1, v3, v3-final) và `data/eval_group.json`; chạy eval cho các version (kế hoạch: [plans/TASK-1-Agent-Core-Tool-Eval.md](plans/TASK-1-Agent-Core-Tool-Eval.md)).

### Đóng góp cụ thể

- **v1:** bỏ các chỉ dẫn xấu cố ý của starter (đoán thay vì hỏi, gửi không cần xác nhận), thêm mục Scope, Missing information → `clarify`, bảng Routing. Base 0.65 → 0.95.
- **v3:** sửa hồi quy của v2 (R10, M06) và R12 bằng rule ưu tiên trong prompt: cấm search từ chung, xin xác nhận `yes_no`, user bỏ nguồn thì không gọi lại. Base 0.85 → 1.0.
- **v3-final:** thêm routing cho 4 tool mới, rule không gọi trùng tool cùng args (sửa G03), §0 yêu cầu gửi/đăng chỉ gọi `clarify` (sửa G09). Group 0.75 → 1.0.
- Viết 10 case nhóm G05–G14; viết version log, group report và transcript chốt.

### Bằng chứng

- Commit: `c69f2bf` (system_prompt v1), `e007567` (v3 prompt), `decd5a5` (routing tool mới + case nhóm), `6c4bbb9` (TASK-3 plan, version log, report, transcript cuối).
- Run: `runs/v1_B_base_openrouter_20261110T173529067837.json`, `runs/v3_B_base_openrouter_20261110T175903514571.json`, `runs/v3_B_group_openrouter_20261110T191826129492.json`.

## NgoNgocHai-2A202603939

### Phần việc phụ trách

- Role B: phần thân `artifacts/tools.yaml` (v2), baseline v0, kế hoạch chia việc, UI Streamlit, live chat và transcript, điền stub test của tool có sẵn (kế hoạch: [plans/TASK-2-UI-Live-Chat.md](plans/TASK-2-UI-Live-Chat.md)).

### Đóng góp cụ thể

- **v0:** chạy baseline (0.65), đóng băng bản v0 trong `artifacts/_baseline/`, lập kế hoạch 3 version song song.
- **v2:** viết lại mô tả 10 tool có sẵn (khi nào dùng / không dùng, convention args). Kết quả 0.95 → 0.85 (giả thuyết không được xác nhận, ghi trung thực trong version log).
- **UI:** `app.py` (Streamlit): chat nhiều lượt, hiện tool call, args, kết quả và `artifact_version`; link public qua Cloudflare Tunnel.
- **Transcript:** chat live, gồm luồng gửi Telegram thật sau khi người dùng xác nhận (`status: sent`).
- Điền các stub test của tool có sẵn trong `tests/test_tools_todo.py`; quản lý merge các PR.

### Bằng chứng

- Commit: `0f90ee5` (plan + run v0), `f961d3e` (tools.yaml v2), `45060db` (TASK-1/2), `1a6c652` / `96505c6` (app.py + transcript), `5f2d403`; merge PR #1–#8.
- Run: `runs/v0_B_base_openrouter_20261110T160101187649.json`, `runs/v2_B_base_openrouter_20261110T174330086638.json`.
- Transcript: `transcripts/v3_openrouter_20261110T194324903467.transcript.json`, `transcripts/v3_openrouter_20261110T215800069030.transcript.json`.

## HoangMinhQuyen-2A202603961

### Phần việc phụ trách

- Role C: tool mới của nhóm, unit test và eval case cho tool mới; chỉ sửa khối cuối `tools.yaml`, không đụng `system_prompt.md` (kế hoạch: [plans/TASK-3-New-Tools.md](plans/TASK-3-New-Tools.md)).

### Đóng góp cụ thể

- **4 tool mới:** `rank_items` (bỏ trùng, xếp hạng kết quả đã có, offline), `wiki` (Wikipedia), `github_repo` (GitHub REST API), `hf_models` (Hugging Face Hub API). Mỗi tool có `tool.py`, `TOOL.md`, đăng ký trong `tools/__init__.py`, khai báo ở cuối `tools.yaml`.
- **Unit test:** 46 hàm test (64 trường hợp) cho 4 tool, đủ 3 nhóm happy path / input xấu / nhánh lỗi; sửa 7 bug trong code tool mới, mỗi bug code có regression test.
- **Eval:** 4 case G01–G04, mỗi case route tới một tool mới.
- **Kiểm tra hồi quy:** chạy đối chứng có / không có tool mới trên base và extension; tìm ra hồi quy E06 (extension 1.0 → 0.9) và sửa bằng một câu trong mô tả `lookup` (dòng `v3-tools` trong version log).
- Tài liệu kỹ thuật [starter_v0/tools/TEAM_TOOLS.md](starter_v0/tools/TEAM_TOOLS.md); sắp xếp lại file nộp theo `SUBMISSION.md`.

### Bằng chứng

- Commit: `f373a46` (rank_items), `c80f643` (wiki, github_repo, hf_models, test, eval case, TEAM_TOOLS.md); merge qua PR #3 và #5.
- Run: `runs/v3_B_base_openrouter_20261110T185801088833.json`, `runs/v3_B_extension_openrouter_20261110T185831810038.json`, `runs/v3_B_group_openrouter_20261110T185844156200.json`.
- Chi tiết: [report/team/2A202603961_HoangMinhQuyen.md](report/team/2A202603961_HoangMinhQuyen.md).
