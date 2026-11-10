# Kế hoạch 3 version song song (v1 / v2 / v3)

Tài liệu này chia việc để **3 người làm song song, không đụng file của nhau**.
Mỗi version = **một giả thuyết độc lập**, sở hữu **một vùng file riêng**.

| Version | Role | Sở hữu (chỉ những file này) | Case v0 cần sửa | File kế hoạch |
|---|---|---|---|---|
| v1 | A — Prompt & Boundary | `artifacts/system_prompt.md` | R08, R10, R11, R14 (+ R12) | `PLAN-v1-Prompt-Boundary.md` |
| v2 | B — Tool & Arg Convention | `artifacts/tools.yaml` (mô tả tool có sẵn) | R03, R13 (+ R12) | `PLAN-v2-Tools-Args.md` |
| v3 | C — New Tool & Eval | `tools/<mới>/`, `tools/__init__.py`, `tests/`, `data/eval_group.json`, append cuối `tools.yaml` | mở rộng năng lực + 10 case nhóm | `PLAN-v3-New-Tool-Eval.md` |

## Vì sao không đụng nhau

`run_eval.py` nhận `--system-prompt <file>` và `--tools <file>` (xem `run_eval.py:269-270`).
Mỗi người trỏ vào **file riêng của mình** khi test:

- A chạy: `--system-prompt artifacts/system_prompt.md --tools artifacts/_baseline/tools_v0.yaml`
- B chạy: `--system-prompt artifacts/_baseline/system_prompt_v0.md --tools artifacts/tools.yaml`
- C chạy: chỉ `pytest` + suite `group`, không cần base suite.

→ Mỗi người luôn dùng **bản đóng băng (baseline)** của người kia ⇒ kết quả không bị nhiễu.

## Bước đóng băng chung (làm TRƯỚC khi 3 người bắt đầu)

Tạo 2 bản snapshot v0 để A/B test độc lập:

```powershell
cd starter_v0
New-Item -ItemType Directory -Force -Path artifacts\_baseline
Copy-Item artifacts\system_prompt.md artifacts\_baseline\system_prompt_v0.md
Copy-Item artifacts\tools.yaml       artifacts\_baseline\tools_v0.yaml
```

## Bản đồ version khi ghép lại (cumulative)

| Bản | system_prompt | tools.yaml | tool mới | Kỳ vọng case_accuracy (base) |
|---|---|---|---|---|
| v0 | gốc (xấu) | gốc (mơ hồ) | – | 0.65 (đo rồi) |
| v1 | **A viết lại** | v0 | – | ~0.85–0.90 |
| v2 | A | **B viết lại** | – | ~0.95–1.0 |
| v3 | A | B | **C thêm** | giữ base + pass suite `group` |

R12 (confirm-before-send) chỉ pass ở **v2** vì cần cả rule prompt (A) lẫn mô tả boundary của `send` (B).

## Điểm chạm chung duy nhất

Khối khai báo tool mới của C được **append ở CUỐI** `artifacts/tools.yaml`, còn B sửa **phần thân** (các tool có sẵn) ⇒ khác vùng dòng, không xung đột.
Quy ước: **C chèn khối cuối cùng, sau khi B đã freeze phần thân.**

## Ghi log (integrator)

Mỗi run xong, thêm 1 dòng vào `artifacts/version_log.csv`:

```text
version,author,changed_artifact,artifact_version,prompt_hash,tools_hash,reason,hypothesis,metric_before,metric_after,run_file
v1,A,system_prompt.md,<lấy từ output>,... ,...,<lý do>,<giả thuyết>,0.65,<after>,runs/<file>.json
v2,B,tools.yaml,... ,...,<lý do>,<giả thuyết>,<before>,<after>,runs/<file>.json
v3,C,tools.yaml+tools/<mới>/,... ,...,<lý do>,<giả thuyết>,<before>,<after>,runs/<file>.json
```

`prompt_hash`, `tools_hash`, `artifact_version`, đường dẫn run in ra cuối mỗi lần chạy `run_eval.py`.
