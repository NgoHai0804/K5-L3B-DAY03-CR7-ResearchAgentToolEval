# PLAN v1 — Prompt & Boundary (Role A)

**Owner:** Thành viên A
**Version chạy:** `v1`
**Artifact sở hữu (CHỈ file này):** `artifacts/system_prompt.md`
**Case v0 cần sửa:** R08, R10, R11, R14 (và giúp R12)

---

## 1. Bằng chứng v0 (đọc từ `runs/v0_*.json`)

| Case | Query | Agent làm (SAI) | Đáng lẽ phải làm |
|---|---|---|---|
| R08 | "Giải giúp mình bài toán tích phân…" | gọi `send(text=…)` | không gọi tool, từ chối |
| R14 | "Viết hàm Python Fibonacci…" | gọi `send(text=code)` | không gọi tool, từ chối |
| R10 | "Tóm tắt 5 tweet mới nhất giúp mình" | gọi `timeline(screenname="sama")` | gọi `clarify(response_type="text")` |
| R11 | "Tóm tắt bài viết này hộ mình" | gọi `fetch(url="https://example.com/article")` | gọi `clarify(response_type="text")` |
| R12 | "Đăng bản tin này lên Telegram giúp mình" | gọi `send(text=…)` ngay | gọi `clarify(response_type="yes_no")` |

## 2. Giả thuyết

Prompt gốc (`artifacts/system_prompt.md`) **xúi agent làm sai** ở 3 dòng:

- dòng 3: *"do not ask them back — just make a sensible guess … pick a well-known account like Sam Altman … assume a likely URL"* → gây R10, R11.
- dòng 5: *"just go ahead and do it so they don't have to wait"* → gây R12.
- dòng 7: *"Always finish the request in a single step."* → gây R08, R14 (câu ngoài phạm vi vẫn cố gọi tool).

⇒ Bỏ các chỉ dẫn xấu và thay bằng rule routing rõ ràng sẽ sửa được nhóm lỗi boundary.

## 3. Việc cần làm (what to do)

1. Xoá hẳn 3 chỉ dẫn xấu ở dòng 3, 5, 7 (không "đoán", không "gửi ngay", không "một bước").
2. Thêm **rule thiếu thông tin**: thiếu handle/URL/từ khoá → gọi `clarify`, KHÔNG đoán.
3. Thêm **rule xác nhận trước khi ghi/gửi**: mọi hành động `send`/đăng → `clarify(response_type="yes_no")` nếu user chưa xác nhận.
4. Thêm **rule ngoài phạm vi**: coding/math/chitchat → KHÔNG gọi tool, từ chối lịch sự + định hướng lại.
5. Thêm **rule routing** cho 6 core tool (khi nào dùng cái nào).
6. Thêm **rule đa nguồn**: cần nhiều nguồn → gọi nhiều tool trong cùng lượt (giữ R13).

## 4. Cải thiện gì (draft thay thế — copy chỉnh lại)

```markdown
You are a careful, accurate research assistant with tools.

## Ground rules
- Do exactly what the current request asks. Treat earlier turns only as context.
- Never guess a missing detail. If a required detail is missing (who / which URL /
  which keyword), call `clarify` with response_type="text" and wait.
- Any action that writes or sends (e.g. `send`) requires explicit confirmation.
  If the user has not confirmed yet, call `clarify` with response_type="yes_no"
  first. Only call `send` with confirmed=true after the user says yes.
- If the request is outside research / news / social / web (coding, math, chit-chat),
  do NOT call any tool. Politely decline and steer back to what you can do.
- If one request needs several sources, call several tools in the same turn.

## Routing
- Posts/tweets by a specific person -> `timeline` (screenname, no '@').
  Map names: "Sam Altman"->sama, "Elon Musk"->elonmusk, "Andrej Karpathy"->karpathy.
- Posts/tweets about a topic/keyword -> `social_search`.
- General web facts -> `lookup` (topic="general").
- News / current events -> `lookup` (topic="news", set timeframe).
- A specific URL the user gave -> `fetch`.
- Already-collected items that need presentation -> `format`.
- Missing handle / URL / keyword -> `clarify` (do not guess).
```

## 5. Cách verify (chạy tách lập, không đụng B)

```powershell
cd starter_v0
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json `
  --system-prompt artifacts/system_prompt.md `
  --tools artifacts/_baseline/tools_v0.yaml
```

Đọc `summary.case_accuracy` trong run mới + đối chiếu R08/R10/R11/R14 chuyển sang PASS.

## 6. Điều kiện đạt (DoD)

- R08, R10, R11, R14 → PASS.
- R12 cải thiện (có thể vẫn cần B, không sao — ghi lại).
- `case_accuracy` ≥ 0.85; `multiturn_accuracy` giữ 1.0.
- `pytest tests/test_tool_contract.py` vẫn xanh (file này không chạm tools.yaml nên không thể làm đỏ).

## 7. KHÔNG được đụng

`artifacts/tools.yaml`, `tools/**`, `tests/**`, `data/**`.

## 8. Ghi log

Thêm 1 dòng `v1` vào `artifacts/version_log.csv` với `author=<tên A>`,
`changed_artifact=system_prompt.md`, `hypothesis="bỏ chỉ dẫn đoán/gửi-ngay/một-bước + thêm rule routing/clarify/confirm/out-of-scope"`,
`metric_before=0.65`, `metric_after=<đo được>`.
