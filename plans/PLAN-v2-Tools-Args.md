# PLAN v2 — Tool Contract & Arg Convention (Role B)

**Owner:** Thành viên B
**Version chạy:** `v2`
**Artifact sở hữu (CHỈ file này):** `artifacts/tools.yaml` (phần thân = mô tả các tool có sẵn)
**Case v0 cần sửa:** R03, R13 (giữ R06, R07 pass; giúp R12 khi ghép A)

> ⚠️ B **không** đụng `system_prompt.md`, `tools/**`, `tests/**`, `data/**`.
> B chỉ sửa các `description` của tool có sẵn. Khối tool mới do C append ở **cuối file**.

> ✅ **Precondition (làm TRƯỚC khi bắt đầu):** phải có snapshot baseline
> `artifacts/_baseline/system_prompt_v0.md` và `artifacts/_baseline/tools_v0.yaml`
> (bước đóng băng trong `PLAN-INDEX.md` §"Bước đóng băng chung"). Hiện `artifacts/_baseline/`
> **chưa tồn tại** — nếu chưa tạo, lệnh ở §5 sẽ `FileNotFoundError` (xem `run_eval.py:275`).

---

## 1. Bằng chứng v0

| Case | Query | Agent làm (SAI) | Đáng lẽ |
|---|---|---|---|
| R03 | "Tin tức AI hôm nay có gì nổi bật?" | `lookup(query="AI news", topic=news, timeframe=day)` | `query="AI"` (không nhồi "news") |
| R13 | "Tìm trên web tin AI hôm nay và tìm thêm tweet về AI." | `lookup(query="AI news", timeframe=day)` — **thiếu `topic=news`** | `lookup(query="AI", topic=news, timeframe=day)` + `social_search(query="AI")` |
| R12 | "Đăng bản tin này lên Telegram" | `send(text=...)` không xác nhận | `clarify(response_type=yes_no)` trước khi gửi — **chỉ pass khi ghép A (rule prompt) + B (mô tả `send`)**; B một mình KHÔNG đủ |

> Bằng chứng lấy từ `runs/v0_B_base_openrouter_*.json` (cả 2 run: `case_accuracy=0.65`,
> `argument_accuracy=0.65`, `tool_routing_accuracy=0.75`, `multiturn_accuracy=1.0`).

## 2. Giả thuyết

`description` trong tools.yaml quá mơ hồ và **thiếu convention args**, khiến model điền sai args:

- `lookup.query` không nói **query chỉ là từ khoá lõi** ⇒ model nhồi "AI news" (R03, và cả R13).
- `lookup.topic` không nói **"news" cho tin tức** ⇒ khi request trải trên nhiều tool (R13), model
  bỏ `topic`. *(Lưu ý: cùng description mơ hồ này ở R03 model vẫn suy ra `topic=news` đúng ⇒
  description chỉ là *một phần* nguyên nhân; ca đa nguồn mới là nơi bị bỏ sót.)*
- `social_search.search_type` không nói **Top = phổ biến**.
- `timeline.screenname` không nói **không có `@`**, không có ví dụ map tên→handle.
- `send` không nói **boundary xác nhận**.

⇒ Viết lại description "khi nào dùng / khi nào KHÔNG dùng" + convention args sẽ sửa nhóm lỗi sai args.
Giả thuyết **không** bao gồm các lỗi boundary/out-of-scope (R08, R10, R11, R14) — đó là phạm vi của A.

## 3. Việc cần làm (what to do)

Với **mỗi** tool: mô tả gồm (a) làm gì, (b) **khi nào dùng**, (c) **khi nào KHÔNG dùng**, (d) convention từng param.

Các convention bắt buộc phải ghi:

| Tool | Param | Convention cần ghi rõ |
|---|---|---|
| `lookup` | `query` | CHỈ từ khoá lõi; KHÔNG nhồi "news/tin tức/hôm nay" (đã có `topic`/`timeframe`) |
| `lookup` | `topic` | `news` cho tin tức/thời sự; `general` cho kiến thức chung |
| `lookup` | `timeframe` | `day`=hôm nay, `week`=tuần này, `month`=tháng này, `year`=năm nay |
| `social_search` | `search_type` | `Top` = phổ biến/nổi bật/top; `Latest` = mới nhất |
| `timeline` | `screenname` | handle **không có `@`**, viết thường; ví dụ: Sam Altman→`sama`, Elon Musk→`elonmusk`, Andrej Karpathy→`karpathy` |
| `fetch` | `url` | chỉ dùng khi user đã đưa link cụ thể |
| `format` | – | chỉ dùng khi ĐÃ có items, không tự đi lấy dữ liệu |
| `clarify` | `response_type` | `text` khi thiếu thông tin; `yes_no` khi cần xác nhận hành động ghi; `choice` khi cần chọn trong `options` (**giữ đủ cả 3 giá trị enum**) |
| `send` | `confirmed` | CHỈ gọi khi user ĐÃ xác nhận; nếu chưa → `clarify(yes_no)` trước, đặt `confirmed=true` sau khi user đồng ý |

> **Bắt buộc:** rewrite description cho **cả 10 tool** có sẵn (không chỉ 4 tool ở §4). Enum/default/type
> giữ **y nguyên** so với v0; chỉ đổi chữ trong `description`.

## 4. Cải thiện gì (draft description — copy chỉnh lại)

Chỉ sửa field `description` (và `description` của param), **giữ nguyên `name`** để không phá eval/tests.

> ⚠️ Đoạn YAML dưới là **thân list** (không có key gốc `tools:`). Khi áp dụng, chèn vào **đúng vị trí
> trong list dưới `tools:`** của `artifacts/tools.yaml`, giữ indent 2 space. Enum/default/type phải
> khớp bản v0 (contract test `test_tool_contract.py` kiểm param khai báo ⊆ signature — **không thêm param mới**).

```yaml
  - name: timeline
    description: "Lấy các bài đăng/tweet gần đây CỦA MỘT tài khoản cụ thể. Dùng khi user nêu tên người/tài khoản. KHÔNG dùng cho chủ đề chung (đó là social_search)."
    parameters:
      type: object
      properties:
        screenname: {type: string, default: "", description: "Handle KHÔNG có '@', viết thường. Map tên: Sam Altman->sama, Elon Musk->elonmusk, Andrej Karpathy->karpathy."}
        limit: {type: integer, default: 5, description: "Số bài muốn lấy, lấy từ 'N tweet' user nói."}
      required: [screenname]

  - name: social_search
    description: "Tìm bài đăng/tweet theo CHỦ ĐỀ hoặc từ khoá (không phải của một người). Dùng khi user hỏi 'mọi người nói gì về X'."
    parameters:
      type: object
      properties:
        query: {type: string, default: "", description: "Từ khoá/chủ đề cần tìm."}
        search_type: {type: string, enum: [Latest, Top], default: "Latest", description: "Top = phổ biến/nổi bật/top; Latest = mới nhất."}
        limit: {type: integer, default: 5, description: "Số kết quả."}
      required: [query]

  - name: lookup
    description: "Tra cứu thông tin trên web. topic='news' cho TIN TỨC/thời sự hiện tại; topic='general' cho kiến thức chung. KHÔNG dùng khi user đã đưa URL cụ thể (dùng fetch)."
    parameters:
      type: object
      properties:
        query: {type: string, default: "", description: "CHỈ từ khoá lõi (vd 'AI'). KHÔNG nhồi 'news/tin tức/hôm nay' vào query — thời điểm dùng timeframe, loại dùng topic."}
        topic: {type: string, enum: [general, news], default: "general", description: "news = tin tức/thời sự; general = kiến thức chung. Tin AI hôm nay -> topic=news."}
        timeframe: {type: string, enum: [day, week, month, year], default: "week", description: "day=hôm nay, week=tuần này, month=tháng này, year=năm nay."}
        max_results: {type: integer, default: 5, description: "Số kết quả."}
      required: [query]

  - name: clarify
    description: "Gửi một câu hỏi cho người dùng và chờ lượt sau. Dùng khi THIẾU thông tin bắt buộc (handle/URL/từ khoá) hoặc cần XÁC NHẬN hành động ghi (gửi/đăng). KHÔNG đoán bừa khi thiếu dữ liệu."
    parameters:
      type: object
      properties:
        question: {type: string, default: "", description: "Câu hỏi cho user."}
        response_type: {type: string, enum: [text, yes_no, choice], default: "text", description: "text = hỏi thông tin; yes_no = xin xác nhận hành động ghi; choice = chọn trong options."}
        options: {type: array, default: [], items: {type: string}, description: "Các lựa chọn khi response_type=choice."}
      required: [question]

  - name: send
    description: "Gửi text lên Telegram channel (HÀNH ĐỘNG ghi). CHỈ gọi sau khi user ĐÃ xác nhận. Nếu chưa xác nhận, gọi clarify(response_type='yes_no') trước; khi user đồng ý mới gọi send với confirmed=true."
    parameters:
      type: object
      properties:
        text: {type: string, default: "", description: "Nội dung gửi."}
        confirmed: {type: boolean, default: false, description: "true CHỈ khi user đã đồng ý gửi."}
      required: [text]
```

> Các tool còn lại (`fetch`, `format`, `policy`, `papers`, `paper_text`) cũng làm gọn theo cùng công thức
> (làm gì / khi nào dùng / khi nào KHÔNG / convention param).

## 5. Cách verify (chạy tách lập, không đụng A)

Chuẩn bị baseline (nếu chưa có) và kích hoạt venv:

```powershell
cd starter_v0
New-Item -ItemType Directory -Force -Path artifacts\_baseline
if (-not (Test-Path artifacts\_baseline\system_prompt_v0.md)) { Copy-Item artifacts\system_prompt.md artifacts\_baseline\system_prompt_v0.md }
if (-not (Test-Path artifacts\_baseline\tools_v0.yaml))       { Copy-Item artifacts\tools.yaml       artifacts\_baseline\tools_v0.yaml }
.venv\Scripts\Activate.ps1
```

Chạy eval v2:

```powershell
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json `
  --system-prompt artifacts/_baseline/system_prompt_v0.md `
  --tools artifacts/tools.yaml
```

Kiểm R03 (`query="AI"`) và R13 (có `topic=news`) chuyển PASS.

> Ghi chú: `--suite base` chỉ là **nhãn run** (không filter case); việc lọc case do `--eval-cases` quyết định.

## 6. Điều kiện đạt (DoD)

- R03, R13 → PASS.
- **Không regress BẤT KỲ case nào đang PASS ở v0.** Đặc biệt: R01, R02, R04, R09, R05, R06, R07
  và **toàn bộ M01–M06** (nhóm multi-turn phụ thuộc trực tiếp `timeline.screenname` + `limit` mà B đang sửa).
- `multiturn_accuracy` giữ `1.0`.
- `case_accuracy` **và** `argument_accuracy` đều tăng: baseline v0 = **0.65 / 0.65** → kỳ vọng ~0.75 / 0.75
  (chỉ sửa được R03 + R13; các case còn lại là phạm vi A).
- `pytest tests/test_tool_contract.py` xanh (mỗi param khai báo phải có trong signature — **không thêm param mới**, chỉ sửa description).
- Xác nhận diff `tools.yaml` **chỉ đổi chữ trong `description`**, không đổi `name`/`type`/`enum`/`default`/`required`.

## 7. KHÔNG được đụng

`system_prompt.md`, `tools/**`, `tests/**`, `data/**`, và **không chèn tool mới** (đó là việc của C).

## 8. Ghi log

Thêm 1 dòng `v2` vào `artifacts/version_log.csv` — **điền đủ 11 cột** theo header:

```text
version,author,changed_artifact,artifact_version,prompt_hash,tools_hash,reason,hypothesis,metric_before,metric_after,run_file
```

- `version=v2`, `author=<tên B>`, `changed_artifact=tools.yaml`
- `artifact_version`, `prompt_hash`, `tools_hash`, đường dẫn `run_file` → lấy từ output cuối lần chạy `run_eval.py`
- `reason="rewrite description các tool có sẵn: query lõi, topic=news, timeframe, search_type, handle không @, boundary confirm"`
- `hypothesis="viết lại description + convention args sẽ sửa nhóm lỗi sai args (R03, R13)"`
- `metric_before=0.65`, `metric_after=<đo được>`

## 9. Checklist thực thi (theo đúng plan v2)

**P0 — Chuẩn bị (làm trước, dùng chung cả nhóm)**
- [x] Tạo `artifacts/_baseline/system_prompt_v0.md` (snapshot prompt gốc, TRƯỚC khi A sửa). — ✅ khôi phục đúng v0 từ `c69f2bf^` (prompt "fast, proactive"); bản working đã bị A commit thành v1 nên phải lấy lại từ git history.
- [x] Tạo `artifacts/_baseline/tools_v0.yaml` (snapshot tools gốc, TRƯỚC khi B sửa). — ✅ khôi phục từ `HEAD:starter_v0/artifacts/tools.yaml` (mô tả mơ hồ v0, vd `"Gửi một câu hỏi cho người dùng."`).
- [x] `.venv` đã tạo, đã `pip install -r requirements.txt`, `preflight_provider.py --provider openrouter` pass. — ✅ `OK provider=openrouter model=openai/gpt-4o-mini`
- [x] `pytest tests/test_tool_contract.py` xanh trên v0. — ✅ 55 passed

**P1 — Đọc bằng chứng & chốt giả thuyết**
- [x] Mở `runs/v0_B_base_openrouter_*.json`, xác nhận R03/R13 FAIL với đúng `actual_tool_calls` (query="AI news", R13 thiếu topic). — ✅ cả 2 run: R03 `lookup{query:"AI news",topic:"news",timeframe:"day"}` (fail: `query expected 'AI'`); R13 `lookup{query:"AI news",timeframe:"day"}` (fail: `query` + `topic expected 'news', got None`), `social_search{query:"AI"}` vẫn được gọi.
- [x] Ghi lại baseline: `case_accuracy=0.65`, `argument_accuracy=0.65`, `tool_routing_accuracy=0.75`, `multiturn_accuracy=1.0`. — ✅ xác nhận trên `v0_B_base_openrouter_20261110T160101187649.json` và `v0_B_base_openrouter_20261110T171212254700.json` (giống nhau).
- [x] Chốt giả thuyết §2 (chỉ ngôn ngữ description; KHÔNG gồm boundary/out-of-scope). — ✅ đã chốt; loại trừ R08/R10/R11/R14 (thuộc A).

**P2 — Sửa `artifacts/tools.yaml` (chỉ phần thân, chỉ `description`)**
- [x] Rewrite `description` cho **cả 10 tool** có sẵn theo công thức (a)(b)(c)(d).
- [x] `lookup.query`: "CHỈ từ khoá lõi, không nhồi news/tin tức/hôm nay".
- [x] `lookup.topic`: `news` cho tin tức/thời sự; `general` cho kiến thức chung.
- [x] `lookup.timeframe`: day/week/month/year = hôm nay/tuần này/tháng này/năm nay.
- [x] `social_search.search_type`: `Top`=phổ biến/nổi bật, `Latest`=mới nhất.
- [x] `timeline.screenname`: handle không `@`, ví dụ map Sam Altman→sama, Elon Musk→elonmusk, Andrej Karpathy→karpathy.
- [x] `fetch.url`: chỉ khi user đưa link cụ thể.
- [x] `format`: chỉ khi đã có items.
- [x] `clarify.response_type`: text/yes_no/choice (giữ đủ 3 enum).
- [x] `send`: nêu boundary xác nhận (`clarify(yes_no)` trước, `confirmed=true` sau).
- [x] Kiểm KHÔNG đổi `name`/`type`/`enum`/`default`/`required`; KHÔNG thêm/xóa tool; KHÔNG đụng khối C. — ✅ diff cấu trúc vs `_baseline/tools_v0.yaml`: cùng 10 tên, cùng thứ tự, `type/default/enum/required` y hệt, 0 tool thêm/xóa.

**P3 — Kiểm tĩnh trước khi eval**
- [x] `pytest tests/test_tool_contract.py` xanh. — ✅ 55 passed
- [x] `git diff artifacts/tools.yaml` → chỉ dòng `description` đổi. — ✅ 37 dòng sửa (74 dòng diff), **0 dòng không phải `description`**.
- [x] YAML parse được (không lỗi indent). — ✅ `yaml.safe_load` OK.

**P4 — Chạy eval v2 (như §5)**
- [x] Chạy đúng lệnh `run_eval.py` với `--system-prompt artifacts/_baseline/system_prompt_v0.md` và `--tools artifacts/tools.yaml`. — ✅ run `runs/v2_B_base_openrouter_20261110T174610790159.json` (artifact_version `v2+pf0c107a9d7a1+tf157b4bf1101`).
- [x] R03 PASS (query="AI", topic=news, timeframe=day). — ✅
- [x] R13 PASS (lookup query="AI" + topic=news, đồng thời có social_search query="AI"). — ✅
- [x] Không regress: R01, R02, R04, R05, R06, R07, R09 PASS; M01–M06 PASS; `multiturn_accuracy=1.0`. — ✅ tất cả PASS, `multiturn_accuracy=1.0`.
- [x] `case_accuracy` và `argument_accuracy` tăng so với 0.65/0.65. — ✅ `case_accuracy=0.8`, `argument_accuracy=0.8`, `tool_routing_accuracy=0.8` (16/20 pass).
- [x] R12 ghi nhận trạng thái (kỳ vọng vẫn FAIL ở v2 một mình; chỉ PASS khi ghép A). — ✅ R12 vẫn FAIL (wrong_boundary) như dự kiến; R10/R11 cũng FAIL (phạm vi A), R08 FAIL (phạm vi A).

**P5 — Ghi log**
- [ ] Thêm dòng `v2` đủ **11 cột** vào `artifacts/version_log.csv` (§8), có `run_file` trỏ tới run mới.

**P6 — Bàn giao cho C (integrator)**
- [ ] Freeze phần thân `tools.yaml` (báo C có thể append `rank_items` ở cuối).
- [ ] Ghi chú R12: cần A (prompt) + B (mô tả `send`) mới pass → xác nhận khi ghép.
