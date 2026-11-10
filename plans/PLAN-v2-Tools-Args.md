# PLAN v2 — Tool Contract & Arg Convention (Role B)

**Owner:** Thành viên B
**Version chạy:** `v2`
**Artifact sở hữu (CHỈ file này):** `artifacts/tools.yaml` (phần thân = mô tả các tool có sẵn)
**Case v0 cần sửa:** R03, R13 (giữ R06, R07 pass; giúp R12)

> ⚠️ B **không** đụng `system_prompt.md`, `tools/**`, `tests/**`, `data/**`.
> B chỉ sửa các `description` của tool có sẵn. Khối tool mới do C append ở **cuối file**.

---

## 1. Bằng chứng v0

| Case | Query | Agent làm (SAI) | Đáng lẽ |
|---|---|---|---|
| R03 | "Tin tức AI hôm nay có gì nổi bật?" | `lookup(query="AI news", topic=news, timeframe=day)` | `query="AI"` (không nhồi "news") |
| R13 | "Tìm trên web tin AI hôm nay và tìm thêm tweet về AI." | `lookup(query="AI news", timeframe=day)` — **thiếu `topic=news`** | `lookup(query="AI", topic=news, timeframe=day)` + `social_search(query="AI")` |
| R12 | "Đăng bản tin này lên Telegram" | `send(text=…)` không xác nhận | mô tả `send` phải nói rõ cần xác nhận |

## 2. Giả thuyết

`description` trong tools.yaml quá mơ hồ và **thiếu convention args**:

- `lookup.query` không nói **query chỉ là từ khoá lõi** ⇒ model nhồi "AI news".
- `lookup.topic` không nói **"news" cho tin tức** ⇒ model bỏ luôn `topic` (R13).
- `social_search.search_type` không nói **Top = phổ biến**.
- `timeline.screenname` không nói **không có `@`**, không có ví dụ map tên→handle.
- `send` không nói **boundary xác nhận**.

⇒ Viết lại description "khi nào dùng / khi nào KHÔNG dùng" + convention args sẽ sửa nhóm lỗi sai args.

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
| `clarify` | `response_type` | `text` khi thiếu thông tin; `yes_no` khi cần xác nhận hành động ghi |
| `send` | `confirmed` | CHỈ gọi khi user ĐÃ xác nhận; nếu chưa → `clarify(yes_no)` trước, đặt `confirmed=true` sau khi user đồng ý |

## 4. Cải thiện gì (draft description — copy chỉnh lại)

Chỉ sửa field `description` (và `description` của param), **giữ nguyên `name`** để không phá eval/tests.

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

  - name: send
    description: "Gửi text lên Telegram channel (HÀNH ĐỘNG ghi). CHỈ gọi sau khi user ĐÃ xác nhận. Nếu chưa xác nhận, gọi clarify(response_type='yes_no') trước; khi user đồng ý mới gọi send với confirmed=true."
    parameters:
      type: object
      properties:
        text: {type: string, default: "", description: "Nội dung gửi."}
        confirmed: {type: boolean, default: false, description: "true CHỈ khi user đã đồng ý gửi."}
      required: [text]
```

> Các tool còn lại (`clarify`, `fetch`, `format`, `policy`, `papers`, `paper_text`) cũng làm gọn theo cùng công thức (làm gì / khi nào dùng / khi nào KHÔNG / convention param).

## 5. Cách verify (chạy tách lập, không đụng A)

```powershell
cd starter_v0
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json `
  --system-prompt artifacts/_baseline/system_prompt_v0.md `
  --tools artifacts/tools.yaml
```

Kiểm R03 (`query="AI"`) và R13 (có `topic=news`) chuyển PASS.

## 6. Điều kiện đạt (DoD)

- R03, R13 → PASS; R06, R07, R05 không bị regress.
- `argument_accuracy` tăng so với v0 (0.65).
- `pytest tests/test_tool_contract.py` xanh (mỗi param khai báo phải có trong signature — **không thêm param mới**, chỉ sửa description).

## 7. KHÔNG được đụng

`system_prompt.md`, `tools/**`, `tests/**`, `data/**`, và **không chèn tool mới** (đó là việc của C).

## 8. Ghi log

Thêm 1 dòng `v2` vào `artifacts/version_log.csv`: `author=<tên B>`,
`changed_artifact=tools.yaml`, `hypothesis="viết lại description + convention args (query lõi, topic=news, timeframe, search_type)"`.
