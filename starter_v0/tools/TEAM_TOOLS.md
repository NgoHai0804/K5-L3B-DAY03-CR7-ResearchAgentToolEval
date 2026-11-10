# Tool mới của nhóm (v3)

Tài liệu này mô tả 4 tool nhóm tự viết thêm cho research agent: mỗi tool làm gì, khi
nào agent nên (và không nên) gọi, nhận đầu vào gì, chạy ra sao, trả về gì, lỗi thế
nào, đã được kiểm thử ra sao. Đọc xong, bạn có thể tự dùng, sửa hoặc viết test cho
từng tool mà không cần mở code.

| Tool | Một câu | Nguồn dữ liệu | Cần mạng | Cần key |
|---|---|---|---|---|
| [`rank_items`](#1-rank_items) | Bỏ trùng, xếp hạng, cắt top N cho kết quả đã có | không, chạy local | không | không |
| [`wiki`](#2-wiki) | Tra kiến thức nền (khái niệm, người, tổ chức) | Wikipedia | có | không |
| [`github_repo`](#3-github_repo) | Xem star, hoạt động, license của một repo | GitHub REST API | có | không (tuỳ chọn `GITHUB_TOKEN`) |
| [`hf_models`](#4-hf_models) | Tìm / xem model AI open-weight | Hugging Face Hub API | có | không (tuỳ chọn `HF_TOKEN`) |

Mục lục: [Khái niệm chung](#khái-niệm-chung) · [rank_items](#1-rank_items) ·
[wiki](#2-wiki) · [github_repo](#3-github_repo) · [hf_models](#4-hf_models) ·
[Kết quả đo](#kết-quả-đo-trên-eval) · [Chạy lại](#cách-chạy-lại)

---

## Khái niệm chung

### Một tool gồm những gì

Mỗi tool nằm trong một thư mục riêng `tools/<tên>/`:

| File / nơi | Vai trò |
|---|---|
| `tools/<tên>/tool.py` | Code Python thật sự chạy. |
| `tools/<tên>/TOOL.md` | Frontmatter (tên, loại, đầu vào, đầu ra) + ghi chú ngắn. |
| `tools/__init__.py` → `TOOL_FUNCTIONS` | Bảng tra "tên tool → hàm Python". Agent dùng bảng này để chạy tool. |
| `artifacts/tools.yaml` | Phần **model nhìn thấy**: tên, mô tả, tham số. Model chọn tool dựa *hoàn toàn* vào phần này. |

Điều quan trọng nhất: **model không đọc code**. Nó chỉ đọc `description` trong
`tools.yaml`. Vì vậy mô tả của 4 tool đều theo cùng một khuôn: *làm gì* → *khi nào
dùng* → *khi nào KHÔNG dùng (và dùng tool nào thay)*.

### Một lượt gọi tool diễn ra thế nào

```text
user hỏi ──► model đọc system prompt + tools.yaml ──► model chọn tool + điền tham số (JSON)
                                                              │
        agent tra TOOL_FUNCTIONS["tên"] và gọi hàm Python ◄───┘
                                                              │
        hàm trả về một dict  ──► agent đưa dict lại cho model ──► model trả lời user
```

### Quy ước chung của cả 4 tool

1. **Không bao giờ raise exception.** Mọi lỗi (đầu vào sai, mạng lỗi, API lỗi) đều
   trả về một *error dict*:

   ```json
   {"tool": "<tên hàm>", "error": "<Loại lỗi>", "message": "<giải thích>"}
   ```

   Nhờ vậy model đọc được lỗi và tự sửa (ví dụ gọi lại với tham số đúng), thay vì
   cả agent bị dừng.

2. **Chấp nhận đầu vào "bẩn" mà model hay gửi.** Model hay gửi số dưới dạng chuỗi
   (`"5"` thay vì `5`), hoặc `true` thay cho số. Các tool tự chuyển `"5"` → `5`, giới
   hạn giá trị vào khoảng hợp lệ, và coi `true`/`false` ở chỗ cần số là không hợp lệ
   (dùng giá trị mặc định). Lưu ý: trong Python, `True` là một số nguyên (`True == 1`),
   nên nếu không chặn riêng, `top_k=True` sẽ âm thầm thành `top_k=1`.

3. **Kiểm tra đầu vào *trước* khi gọi mạng.** Đầu vào sai thì trả lỗi ngay, không tốn
   request.

4. **"Không tìm thấy" không phải là lỗi.** Khi tra cứu không có kết quả, tool trả về
   `found: false` và `items: []`, không có trường `error`. Model hiểu ngay là "không
   có", thay vì nghĩ là "hỏng".

5. **Cùng một khuôn item.** Mỗi kết quả là một dict có ít nhất `title`, `url`,
   `source`, giống các tool sẵn có (`lookup`, `social_search`, `papers`). Nhờ vậy kết
   quả của tool này đưa thẳng được vào tool khác (ví dụ `rank_items`, `format`).

6. **Mỗi lần gọi = đúng một request mạng** (với 3 tool có gọi mạng). Ít request hơn
   nghĩa là ít điểm hỏng hơn, ít chạm giới hạn lượt gọi hơn, và test đơn giản hơn.

---

## 1. `rank_items`

**Bỏ trùng và xếp hạng danh sách kết quả mà agent ĐÃ thu thập được.** Tool không lấy
dữ liệu mới, không gọi mạng.

| | |
|---|---|
| Code | [`tools/rank_items/tool.py`](rank_items/tool.py) |
| Hàm Python | `rank_items(items, sort_by, query, dedupe, top_k)` |
| Loại | `local_formatter`, chạy offline |

### Vì sao cần

Khi agent tìm từ nhiều nguồn, kết quả thường bị **trùng** (cùng một bài, link hơi
khác), **lộn xộn** về thứ tự, và **quá nhiều**. Nếu để model tự sắp xếp trong đầu, nó
dễ sai: đếm nhầm, bỏ sót bài trùng, so ngày sai. `rank_items` làm việc đó bằng code nên
kết quả luôn giống nhau và kiểm chứng được.

Nó là bước "dọn dẹp" ở giữa chuỗi:

```text
lấy dữ liệu                        dọn dẹp / xếp hạng      trình bày
lookup / social_search / papers ─► rank_items ───────────► format
```

### Khi nào agent gọi / không gọi

- **Gọi** khi đã có danh sách và user muốn: bỏ trùng, lọc top N, xếp theo mới nhất /
  điểm cao / độ liên quan.
- **Không gọi** để lấy dữ liệu mới (phải gọi `lookup` / `social_search` / `papers`
  trước), và **không gọi** để trình bày thành bản tin (đó là việc của `format`).

### Đầu vào

| Tham số | Kiểu | Mặc định | Bắt buộc | Ý nghĩa |
|---|---|---|---|---|
| `items` | list các dict | `[]` | có | Danh sách item đã thu thập, giữ nguyên các trường từ tool trước. |
| `sort_by` | `recency` \| `score` \| `relevance` | `recency` | | Tiêu chí xếp hạng (xem bên dưới). |
| `query` | string | `""` | chỉ khi `sort_by=relevance` | Từ khoá để đo độ liên quan. |
| `dedupe` | bool | `true` | | Có bỏ item trùng không. |
| `top_k` | int | `10` | | Giữ tối đa bao nhiêu item. `"3"` được hiểu là `3`. Giá trị không hợp lệ (`true`, `"abc"`) → dùng 10. Số âm → 0. |

### Cách hoạt động

1. **Kiểm tra đầu vào.**
   - `items` không phải list → trả lỗi.
   - `sort_by` ngoài 3 giá trị cho phép → trả lỗi.
   - `sort_by=relevance` mà không có `query` → trả lỗi (không có từ khoá thì không đo
     được độ liên quan).
2. **Lọc và bỏ trùng.** Duyệt từng item theo thứ tự:
   - Bỏ qua item không phải dict (chuỗi, số, `None`...).
   - Tạo *khoá trùng* = `url` (nếu không có url thì dùng `title`), viết thường, bỏ
     khoảng trắng và dấu `/` ở cuối. Ví dụ `https://x.com/a/` và `https://X.com/a` có
     cùng khoá.
   - Nếu khoá đã gặp → bỏ item này (giữ item xuất hiện **đầu tiên**).
3. **Sắp xếp** (giảm dần):
   - `recency`: theo `date`, nếu không có thì `published`, rồi `created_at`. So sánh
     dạng chuỗi, nên ngày phải ở dạng ISO (`2026-03-01...`) như các tool trả về. Item
     không có ngày xếp cuối.
   - `score`: theo `score`; nếu không có thì `points`, `likes`, `stars`. Nhờ vậy trộn
     được kết quả từ nhiều nguồn có tên trường khác nhau. Giá trị không phải số
     (`"abc"`) được coi là 0.
   - `relevance`: đếm số từ khoá của `query` xuất hiện trong `title` + `summary` (đã bỏ
     dấu tiếng Việt và stopword như "của", "và").
   - Khi hai item bằng điểm, giữ nguyên thứ tự ban đầu.
4. **Cắt** lấy `top_k` item đầu.

### Đầu ra

```json
{
  "tool": "rank_items",
  "sort_by": "score",
  "items": [ {"title": "...", "url": "...", "score": 9}, ... ],
  "count": 2,
  "removed": 2
}
```

| Trường | Ý nghĩa |
|---|---|
| `items` | Danh sách đã xếp hạng, mỗi item **giữ nguyên** mọi trường gốc. |
| `count` | Số item trả về (sau khi cắt `top_k`). |
| `removed` | Số item bị loại ở bước lọc: trùng **cộng** không phải dict. Không tính phần bị cắt bởi `top_k`. |

### Ví dụ

Đầu vào (4 item, trong đó 2 cái trùng vì chỉ khác dấu `/` cuối):

```json
{
  "items": [
    {"title": "OpenAI ra mắt GPT-5", "url": "https://openai.com/blog/gpt-5", "score": 7},
    {"title": "OpenAI ra mắt GPT-5", "url": "https://openai.com/blog/gpt-5/", "score": 7},
    {"title": "Anthropic công bố Claude mới", "url": "https://anthropic.com/news", "score": 9},
    {"title": "Google cập nhật Gemini", "url": "https://blog.google/gemini", "score": 4}
  ],
  "sort_by": "score",
  "top_k": 2
}
```

Kết quả: `items` = [Anthropic (9), OpenAI (7)], `count` = 2, `removed` = 1.

### Lỗi

| Tình huống | Kết quả |
|---|---|
| `items` không phải list | `{"error": "ValueError", "message": "items must be a list"}` |
| `sort_by` không hợp lệ | `{"error": "ValueError", "message": "unsupported sort_by: ..."}` |
| `relevance` thiếu `query` | `{"error": "ValueError", "message": "sort_by=relevance needs a query"}` |
| `items=[]` | không lỗi: `items=[]`, `count=0`, `removed=0` |

### Giới hạn

- Chỉ hữu ích khi **đã có danh sách**. Trong eval một lượt, user phải dán danh sách vào
  câu hỏi; trong `chat.py`, model tự nối kết quả tool trước vào.
- `relevance` chỉ đếm từ khoá trùng, không hiểu nghĩa ("LLM" và "mô hình ngôn ngữ lớn"
  là khác nhau với nó).
- Bỏ trùng theo url/title chính xác. Cùng một tin đăng ở hai báo khác nhau vẫn bị coi
  là hai item.

### Đã sửa gì so với code mẫu trong PLAN-v3

Code mẫu ban đầu có 5 bug; mỗi bug giờ có một regression test:

| Đầu vào | Code mẫu | Bây giờ |
|---|---|---|
| `score: "abc"` | crash `ValueError` | coi như 0 |
| `top_k="2"` | âm thầm thành 10 | 2 |
| `top_k=True` | thành 1 | dùng mặc định 10 |
| `sort_by="relevance"` | được chấp nhận nhưng không sắp xếp gì | sắp theo từ khoá |
| `.../a/` và `.../a` | không coi là trùng | coi là trùng |

---

## 2. `wiki`

**Tra kiến thức nền ổn định trên Wikipedia** (khái niệm, người, tổ chức, sự kiện) và
trả về đoạn mở đầu của bài phù hợp nhất.

| | |
|---|---|
| Code | [`tools/wiki/tool.py`](wiki/tool.py) |
| Hàm Python | `wiki_summary(query, lang, sentences)` (tên tool model thấy: `wiki`) |
| Nguồn | MediaWiki Action API: `https://{en,vi}.wikipedia.org/w/api.php` |

### Vì sao chọn Wikipedia

- **Uy tín:** bách khoa toàn thư có trích dẫn nguồn, do Wikimedia Foundation vận hành.
- **Ổn định:** API công khai chạy nhiều năm, không cần key, giới hạn lượt gọi rộng.
- **Lấp chỗ trống:** trước đó agent không có tool nào cho câu "X là gì / Y là ai";
  `lookup` là để tìm tin tức, không phải kiến thức nền.

### Khi nào agent gọi / không gọi

- **Gọi:** "X là gì", "giới thiệu về Y", "Y là ai".
- **Không gọi:** tin tức hoặc thông tin mới (dùng `lookup` với `topic=news`); bài toán,
  tính toán, viết code (ngoài phạm vi, trả lời không cần tool).

### Đầu vào

| Tham số | Kiểu | Mặc định | Bắt buộc | Ý nghĩa |
|---|---|---|---|---|
| `query` | string | `""` | có | Tên khái niệm / người / tổ chức, ngắn gọn. Ví dụ `"Transformer deep learning"`. |
| `lang` | `en` \| `vi` | `en` | | Ngôn ngữ **của Wikipedia**, không phải của câu hỏi. Chỉ dùng `vi` khi user nói rõ "Wikipedia tiếng Việt". |
| `sentences` | int | `5` | | Số câu tóm tắt. `"4"` → 4; giới hạn 1..10; `true`/`"abc"` → 5. |

### Cách hoạt động

1. **Kiểm tra đầu vào.** `query` rỗng hoặc không phải chuỗi → lỗi. `lang` ngoài `en`/`vi`
   → lỗi. Cả hai trường hợp đều **không gửi request**.
2. **Gửi đúng một request** `GET https://{lang}.wikipedia.org/w/api.php` với:
   - `generator=search`, `gsrsearch=<query>`, `gsrlimit=1`: tìm bài khớp nhất. Cần bước
     này vì model hiếm khi biết chính xác tên bài (bài đúng là "Transformer (deep
     learning)", không phải "Transformer").
   - `prop=extracts` + `exintro` + `explaintext` + `exsentences`: lấy đoạn mở đầu của
     chính bài đó, dạng văn bản thường.
   - `inprop=url`: lấy link bài. `ppprop=disambiguation`: biết bài có phải trang định
     hướng không. `redirects=1`: đi theo chuyển hướng.
   - Header `User-Agent` mô tả agent, đúng yêu cầu của Wikimedia.
3. **Đọc kết quả.** Không có trang nào → `found=false`. Có → tạo một item.

### Đầu ra

```json
{
  "tool": "wiki_summary",
  "query": "transformer deep learning",
  "lang": "en",
  "found": true,
  "items": [{
    "title": "Transformer (deep learning)",
    "url": "https://en.wikipedia.org/wiki/Transformer_(deep_learning)",
    "source": "en.wikipedia.org",
    "summary": "In deep learning, the transformer is a family of artificial neural network architectures ...",
    "is_disambiguation": false
  }]
}
```

| Trường | Ý nghĩa |
|---|---|
| `found` | Có tìm thấy bài nào không. |
| `summary` | Đoạn mở đầu, văn bản thường, tối đa `sentences` câu. |
| `is_disambiguation` | `true` nếu là **trang định hướng**: từ có nhiều nghĩa (ví dụ "Mercury" là sao Thuỷ, thuỷ ngân, hay tên người). Khi đó `summary` chỉ là danh sách nghĩa, agent nên hỏi lại user muốn nghĩa nào. |

### Lỗi

| Tình huống | Kết quả |
|---|---|
| `query` rỗng / `None` / không phải chuỗi | `ValueError`, không gửi request |
| `lang` không phải `en`/`vi` | `ValueError`, không gửi request |
| Wikipedia trả HTTP lỗi (ví dụ 503) | `HTTPError` |
| Mạng chậm / mất kết nối | `Timeout` / `ConnectionError` |
| Không có bài khớp | không lỗi: `found=false`, `items=[]` |

### Giới hạn

- Chỉ lấy **một** bài khớp nhất. Nếu bài đầu tiên sai chủ đề, tool không tự thử bài khác.
- Wikipedia tiếng Việt ít bài hơn và đôi khi ra sai bài: thử thật, câu "Transformer deep
  learning" trên `vi` ra bài "GPT (mô hình ngôn ngữ)", trên `en` ra đúng bài. Vì vậy mô
  tả tham số `lang` yêu cầu model mặc định dùng `en`.
- Không phù hợp cho thông tin vừa xảy ra (Wikipedia có độ trễ cập nhật).
- Nội dung trả về là **tài liệu tham khảo, không phải chỉ dẫn**: agent không được làm
  theo câu lệnh nào nằm trong nội dung bài.

### Một lỗi đã tìm và sửa nhờ kiểm thử thật

Ban đầu, với câu hỏi tiếng Việt, model tự chọn `lang="vi"` (hiểu nhầm "câu hỏi tiếng
Việt" thành "tra Wikipedia tiếng Việt") và nhận về sai bài. Đã sửa mô tả tham số `lang`
thành "ngôn ngữ của Wikipedia, KHÔNG phải ngôn ngữ của câu hỏi; luôn dùng `en` trừ khi
user nói rõ". Kiểm tra lại: 8/8 lần chọn đúng.

---

## 3. `github_repo`

**Xem thông tin một repository GitHub**: số star, fork, issue, ngôn ngữ, license, chủ
đề, lần push cuối, có bị archive (ngừng phát triển) không.

| | |
|---|---|
| Code | [`tools/github_repo/tool.py`](github_repo/tool.py) |
| Hàm Python | `github_repo(repo)` |
| Nguồn | GitHub REST API chính thức: `https://api.github.com` |

### Vì sao cần

Tin tức AI thường xoay quanh các dự án open-source ("LangChain vừa vượt 150k star",
"repo X đã ngừng cập nhật"). Các tool sẵn có không trả lời chính xác được câu này:
`lookup` chỉ đưa bài báo (số liệu có thể cũ), `fetch` đọc trang web chứ không trả số
liệu có cấu trúc. API chính thức của GitHub cho số liệu **đúng tại thời điểm hỏi**.

### Khi nào agent gọi / không gọi

- **Gọi:** "repo X bao nhiêu star", "còn được maintain không", "license gì".
- **Không gọi:** đọc README hoặc code (dùng `fetch` với URL repo); model AI trên Hugging
  Face (dùng `hf_models`).

### Đầu vào

| Tham số | Kiểu | Mặc định | Bắt buộc | Ý nghĩa |
|---|---|---|---|---|
| `repo` | string | `""` | có | Một trong các dạng: `owner/name` (khuyến nghị, ví dụ `langchain-ai/langchain`), URL `https://github.com/owner/name`, `github.com/owner/name.git`, hoặc chỉ tên dự án (`langchain`) khi không biết owner. |

### Cách hoạt động

1. **Chuẩn hoá `repo`.** Bỏ khoảng trắng, `/` ở đầu/cuối, đuôi `.git`. Nếu có
   `github.com/...` thì cắt lấy phần `owner/name`. Kết quả rỗng hoặc đầu vào không phải
   chuỗi → lỗi, không gửi request.
2. **Chọn một trong hai đường** (mỗi đường đúng **một** request):

   | Đầu vào | Request | Giới hạn khi không có token |
   |---|---|---|
   | dạng `owner/name` | `GET /repos/{owner}/{name}` | 60 lần / giờ, **đường ổn định** |
   | chỉ có tên (`langchain`) | `GET /search/repositories?q=langchain in:name&per_page=5` | chỉ 10 lần / phút |

   Với đường tìm kiếm, tool **ưu tiên repo trùng tên chính xác** (nhiều repo cùng tên thì
   lấy cái nhiều star nhất); không có repo trùng tên thì lấy kết quả đầu tiên.
   Kết quả tìm kiếm đã chứa đủ các trường cần thiết nên không cần request thứ hai.
3. **Xử lý phản hồi.**
   - `404` → repo không tồn tại → `found=false` (không phải lỗi).
   - `403`/`429` kèm header `x-ratelimit-remaining: 0` → hết lượt gọi → lỗi kèm hướng
     dẫn: đặt `GITHUB_TOKEN` hoặc truyền `owner/name`.
   - Lỗi HTTP khác → `HTTPError`.
4. Nếu biến môi trường `GITHUB_TOKEN` có giá trị, tool gửi kèm header `Authorization`.
   Giới hạn tăng lên 5000 lần / giờ. Không có token thì tool vẫn chạy.

### Đầu ra

```json
{
  "tool": "github_repo",
  "repo": "langchain-ai/langchain",
  "found": true,
  "items": [{
    "title": "langchain-ai/langchain",
    "url": "https://github.com/langchain-ai/langchain",
    "source": "github.com",
    "summary": "The agent engineering platform.",
    "stars": 149300,
    "forks": 25103,
    "open_issues": 739,
    "language": "Python",
    "license": "MIT",
    "topics": ["llm", "agents"],
    "last_push": "2026-11-10T08:28:09Z",
    "archived": false
  }]
}
```

| Trường | Ý nghĩa |
|---|---|
| `repo` | Tên repo đã chuẩn hoá. Với đường tìm kiếm, đây là repo tool đã chọn. |
| `summary` | Mô tả ngắn của repo. |
| `stars`, `forks` | Mức độ phổ biến. |
| `open_issues` | Số issue **cộng** pull request đang mở (GitHub gộp chung). |
| `license` | Mã license chuẩn SPDX (`MIT`, `Apache-2.0`...), hoặc `null`. |
| `last_push` | Lần cuối có code được đẩy lên: cách đo "còn được maintain không". |
| `archived` | `true` = chủ repo đã đóng băng, không phát triển nữa. |

### Lỗi

| Tình huống | Kết quả |
|---|---|
| `repo` rỗng / `None` / số | `ValueError`, không gửi request |
| Repo không tồn tại (404) / tìm không ra | không lỗi: `found=false`, `items=[]` |
| Hết lượt gọi | `RuntimeError` với hướng dẫn đặt `GITHUB_TOKEN` |
| GitHub lỗi (5xx) | `HTTPError` |
| Mạng chậm / mất kết nối | `Timeout` / `ConnectionError` |

### Giới hạn

- Không có token, đường tìm kiếm rất dễ hết lượt (10 lần/phút); khi thử nghiệm đã chạm
  giới hạn này 2 lần. Nên truyền `owner/name`, hoặc đặt `GITHUB_TOKEN` trong `.env` khi
  demo.
- Không trả về release mới nhất (cần thêm request, đã bỏ để giữ "một request mỗi lần").
- Số liệu là của thời điểm gọi, không có lịch sử (không biết star tăng nhanh hay chậm).

### Một lỗi đã tìm và sửa nhờ kiểm thử thật

Bản đầu sắp kết quả tìm kiếm theo số star. Kết quả: tìm `langchain` ra
**microsoft/markitdown** (một repo rất nhiều star có nhắc tới chữ "langchain"). Đã đổi
sang thứ tự khớp mặc định của GitHub và ưu tiên repo trùng tên chính xác. Có regression
test cho lỗi này.

---

## 4. `hf_models`

**Tìm model AI open-weight trên Hugging Face Hub, hoặc xem chi tiết một model**: lượt
tải, lượt thích, license, loại task, paper arXiv liên quan.

| | |
|---|---|
| Code | [`tools/hf_models/tool.py`](hf_models/tool.py) |
| Hàm Python | `hf_models(query, model_id, task, sort_by, limit)` |
| Nguồn | Hugging Face Hub API chính thức: `https://huggingface.co/api/models` |

### Vì sao cần

Hugging Face là nơi phát hành gần như mọi model open-weight (Llama, Qwen, Whisper...).
Câu "model nào đang phổ biến cho task X" hay "model Y license gì, có được dùng thương
mại không" rất hay gặp trong tin tức AI. Tool sẵn có `papers` chỉ tìm paper, không biết
model nào được tải nhiều hay license của nó.

### Khi nào agent gọi / không gọi

- **Gọi:** "model speech-to-text nào được tải nhiều nhất", "Qwen3 bao nhiêu lượt tải",
  "license của Llama 3.1".
- **Không gọi:** tìm paper (dùng `papers`); repo code GitHub (dùng `github_repo`).

### Đầu vào

Tool có **hai chế độ**, chọn tự động theo việc có `model_id` hay không.

| Tham số | Kiểu | Mặc định | Dùng ở chế độ | Ý nghĩa |
|---|---|---|---|---|
| `model_id` | string | `""` | xem chi tiết | Id chính xác dạng `org/name`, ví dụ `meta-llama/Llama-3.1-8B-Instruct`. Có giá trị → chế độ xem chi tiết. |
| `query` | string | `""` | tìm kiếm | Từ khoá, ví dụ `"qwen"`, `"whisper"`. |
| `task` | string | `""` | tìm kiếm | Lọc theo loại task của Hugging Face, ví dụ `text-generation`, `automatic-speech-recognition`, `text-to-image`. |
| `sort_by` | `downloads` \| `likes` \| `trending` \| `recent` | `downloads` | tìm kiếm | Phổ biến nhất / được thích nhất / đang hot / mới nhất. |
| `limit` | int | `5` | tìm kiếm | Số model, giới hạn 1..20. `"7"` → 7; `true` → 5. |

Ở chế độ tìm kiếm cần **ít nhất một** trong `query` hoặc `task`.

### Cách hoạt động

**Chế độ xem chi tiết** (có `model_id`):

1. `model_id` phải đúng dạng `org/name` (một dấu `/`). Sai dạng (thiếu org, là URL, có
   hai dấu `/`) → lỗi, không gửi request.
2. Gửi `GET https://huggingface.co/api/models/{model_id}`.
3. Hugging Face trả **401** (không phải 404) khi model không tồn tại hoặc là private.
   Tool hiểu cả 401 và 404 là "không tìm thấy" → `found=false`.

**Chế độ tìm kiếm** (không có `model_id`):

1. Không có cả `query` lẫn `task` → lỗi. `sort_by` sai → lỗi. Cả hai đều không gửi
   request.
2. Gửi `GET https://huggingface.co/api/models` với `search=<query>` (nếu có),
   `pipeline_tag=<task>` (nếu có), `sort=<khoá sắp xếp>`, `direction=-1` (giảm dần),
   `limit=<limit>`. `sort_by` được đổi sang tên của Hub: `trending` → `trendingScore`,
   `recent` → `createdAt`.

**Cả hai chế độ** biến mỗi model thành một item. License và paper được lấy từ **tags**
của model: tag `license:apache-2.0` → `license = "apache-2.0"`, tag `arxiv:2505.09388`
→ `arxiv = ["2505.09388"]`. Nếu biến môi trường `HF_TOKEN` có giá trị, tool gửi kèm
header `Authorization` (không bắt buộc).

### Đầu ra

```json
{
  "tool": "hf_models",
  "query": "qwen",
  "task": null,
  "sort_by": "downloads",
  "found": true,
  "items": [{
    "title": "Qwen/Qwen3-0.6B",
    "url": "https://huggingface.co/Qwen/Qwen3-0.6B",
    "source": "huggingface.co",
    "task": "text-generation",
    "library": "transformers",
    "downloads": 20511631,
    "likes": 1889,
    "license": "apache-2.0",
    "arxiv": ["2505.09388"],
    "gated": false,
    "date": "2025-04-27T03:40:08.000Z"
  }]
}
```

| Trường | Ý nghĩa |
|---|---|
| `title` | Id model (`org/name`). |
| `task` | Loại task Hugging Face gán cho model. |
| `library` | Thư viện để chạy model (`transformers`, `diffusers`...). |
| `downloads` | Lượt tải trong **30 ngày gần nhất** (không phải tổng từ trước đến nay). |
| `likes` | Số lượt thích. |
| `license` | License lấy từ tag; `null` nếu model không khai báo. |
| `arxiv` | Danh sách id paper arXiv liên quan, đưa thẳng vào `paper_text` được. |
| `gated` | `true` = phải đăng nhập và đồng ý điều khoản mới tải được (ví dụ Llama). |
| `date` | Lần sửa cuối (`lastModified`, chỉ có ở chế độ xem chi tiết) hoặc ngày tạo (`createdAt`). |

Chế độ xem chi tiết trả về `model_id` thay cho `query` / `task` / `sort_by`.

### Lỗi

| Tình huống | Kết quả |
|---|---|
| Không có `query`, `task`, `model_id` | `ValueError`, không gửi request |
| `sort_by` không hợp lệ | `ValueError`, không gửi request |
| `model_id` sai dạng | `ValueError`, không gửi request |
| Model không tồn tại / private (401, 404) | không lỗi: `found=false`, `items=[]` |
| Hugging Face lỗi (5xx) | `HTTPError` |
| Mạng chậm / mất kết nối | `Timeout` / `ConnectionError` |

### Giới hạn

- `downloads` chỉ tính 30 ngày, nên model cũ nhưng nổi tiếng có thể xếp sau model mới.
- License lấy từ tag do tác giả tự khai. Một số model ghi `other` (license riêng), cần đọc
  trang model để biết chi tiết.
- Từ khoá tìm kiếm khớp theo **tên** model, không theo mô tả: tìm "speech" sẽ không ra
  Whisper; nên dùng `task` để lọc theo chức năng.

---

## Kết quả đo trên eval

Tất cả đo bằng `openai/gpt-4o-mini` qua OpenRouter, với prompt và `tools.yaml` hiện tại
của nhóm (v1 + v2 + 4 tool mới).

### Unit test (`pytest`)

**164 passed, 0 failed, 0 skipped.** Test chạy offline: mọi HTTP thật bị chặn và
được giả lập bằng fixture `fake_http`; mọi API key bị xoá trước mỗi test.

| Tool | Số hàm test | Số trường hợp (tính cả `parametrize`) |
|---|---|---|
| `rank_items` | 14 | 14 |
| `wiki` | 10 | 17 |
| `github_repo` | 10 | 15 |
| `hf_models` | 12 | 18 |

Mỗi tool có đủ 3 nhóm test theo yêu cầu: (1) happy path, kiểm tra cả **request gửi đi**
lẫn **kết quả trả về**; (2) đầu vào xấu từ model; (3) nhánh lỗi trả error dict, không
raise. Ngoài ra, 14 stub có sẵn cho các tool cũ (clarify, format, send, lookup, fetch,
timeline, social_search, policy) đã được điền đủ.

### Eval case route tới tool mới (`data/eval_group.json`)

| Case | Câu hỏi (rút gọn) | Kỳ vọng | Kết quả |
|---|---|---|---|
| G01 | "Đây là kết quả... bỏ trùng, giữ 2 bài điểm cao nhất" | `rank_items(sort_by=score, top_k=2)` | PASS |
| G02 | "Transformer trong deep learning là gì?" | `wiki` | PASS |
| G03 | "Repo langchain-ai/langchain bao nhiêu star và còn được maintain không?" | `github_repo(repo="langchain-ai/langchain")` | **FAIL** (xem dưới) |
| G04 | "Trên Hugging Face, model speech-to-text nào được tải nhiều nhất?" | `hf_models` | PASS (model tự điền `task=automatic-speech-recognition`) |

**Vì sao G03 fail:** model chọn **đúng** tool và đúng tham số, nhưng gọi
`github_repo` **hai lần** cho cùng một repo: một lần cho ý "bao nhiêu star", một lần cho
ý "còn maintain không". Một lần gọi đã trả về cả hai thông tin. Đã thử hai cách sửa,
đều không có tác dụng (3/3 và 2/2 lần vẫn fail), nên đã hoàn tác:

1. Thêm vào mô tả tool: "một lần gọi trả về tất cả các trường, chỉ gọi 1 lần cho mỗi
   repo".
2. Thêm vào bản sao system prompt: "không gọi cùng một tool hai lần với cùng tham số".

Case được giữ nguyên vì nó phản ánh đúng một lỗi thật (`unnecessary_tool`): gọi thừa
tốn lượt gọi của GitHub (60 lần/giờ khi không có token).

### Tool mới có làm hỏng case cũ không?

Kết quả cuối cùng (sau khi sửa, xem bên dưới), mỗi suite chạy 2 lần trên bản thử và 1
lần chính thức, lần nào cũng ra cùng điểm:

| Suite | Có 4 tool mới | Không có tool mới (đối chứng) | Số lần model gọi tool mới |
|---|---|---|---|
| base (20 case) | **1.0** | 0.85 (2 lần chạy) | 0 |
| extension (10 case) | **1.0** | 1.0 | 0 |
| group (4 case) | 0.75 (chỉ G03 fail) | không đo được: thiếu tool thì case không thể pass | 3 case gọi đúng |

Điểm base dao động 0.85–1.0 giữa các lần chạy, kể cả với cùng một cấu hình, nên chênh
lệch nhỏ là do model, không phải do tool.

### Hồi quy ở case E06 và cách đã sửa

**Triệu chứng.** Sau khi thêm 4 tool, bộ extension tụt từ 1.0 xuống 0.9 (3/3 lần), chỉ
vì case E06: "Làm bản tin AI hôm nay, nhưng kiểm tra policy công ty về source/citation
**trước**". Kỳ vọng là gọi `lookup` **và** `policy`, nhưng model chỉ gọi `policy`. Tool
mới không hề được gọi trong case này.

**Tìm nguyên nhân** (mỗi cấu hình chạy E06 ba lần, với prompt hiện tại):

| Cấu hình | E06 pass |
|---|---|
| 10 tool cũ (đối chứng) | 3/3 |
| + chỉ `github_repo` | 3/3 |
| + chỉ `rank_items` | 2/3 |
| + chỉ `hf_models` | 2/3 |
| + chỉ `wiki` | **0/3** |
| + cả 4 tool | 0/3 |

Thêm tool nào cũng làm case này kém ổn định đi, mạnh nhất là `wiki`. Model hiểu chữ
"trước" là "làm từng bước": gọi `policy` bây giờ, còn `lookup` để sau. Nhưng trong eval
không có "sau", vì mỗi case chỉ được chấm một lượt.

**Các cách đã thử nhưng KHÔNG hiệu quả** (đều 0/3 hoặc chập chờn, đã hoàn tác):

| Cách thử | E06 pass |
|---|---|
| Rút mô tả `wiki` chỉ còn "Tra Wikipedia." | 0/3 |
| Bỏ mệnh đề "không dùng cho tin tức" hoặc "không dùng cho toán / code" khỏi mô tả `wiki` | 0/3 |
| Đổi tên `wiki` thành `wikipedia` | 1/3 |
| Bỏ tham số `lang`, `sentences` của `wiki` | 1/3 |
| Thêm "không thay thế lookup trong bản tin" vào mô tả `wiki` | 0/3 |
| Thêm 4 tool mới vào bảng routing của system prompt (bản sao) | 0/3 |
| Thêm vào system prompt (bản sao): "'trước' không có nghĩa là làm từng bước" + một ví dụ khác chủ đề | 0/3 |

**Cách sửa đã kiểm chứng.** Thêm một câu vào **mô tả của `lookup`** trong `tools.yaml`:

> Yêu cầu làm bản tin / tin tức luôn cần lookup, kể cả khi user muốn kiểm tra thêm
> policy: gọi cả hai trong cùng lượt.

Kết quả: E06 3/3; cả 3 suite chạy 2 lần đều giữ điểm (base 1.0, extension 1.0, group
0.75). Lý do cách này hiệu quả mà sửa `wiki` hay sửa prompt thì không: thông tin model
thiếu nằm ở **chính tool cần được gọi**. Mô tả cũ của `lookup` không hề nói rằng làm bản
tin thì bắt buộc phải lấy tin. Khi có nhiều tool hơn, model cần tín hiệu đó rõ hơn để
không bỏ sót `lookup`.

Lưu ý cho nhóm: câu này nằm trong phần thân `tools.yaml` (phần của Role B), không phải
khối tool mới ở cuối file.

Bài học: kết luận đầu tiên của ablation ("thủ phạm là `wiki`") chỉ đúng một phần. Khi
prompt của nhóm thay đổi (sau khi merge PR mới), cấu hình "bỏ `wiki`" từ 3/3 pass chuyển
sang 0/3. Mỗi lần prompt hoặc `tools.yaml` đổi, cần chạy lại đối chứng thay vì dùng lại
kết quả cũ.

### Gọi API thật (không mock)

Cả 3 tool có gọi mạng đều đã được gọi thật, ra đúng kết quả:

| Tool | Trường hợp đã thử |
|---|---|
| `wiki` | bài tiếng Anh, bài tiếng Việt, trang định hướng ("Mercury"), từ khoá không tồn tại |
| `github_repo` | `owner/name`, URL có `.git`, tên trống `langchain`, repo không tồn tại, đầu vào rỗng |
| `hf_models` | tìm theo từ khoá, xem chi tiết một model, model không tồn tại (401), lọc theo task, sắp theo trending, thiếu đầu vào, `sort_by` sai |

---

## Cách chạy lại

Chạy từ thư mục `starter_v0/`:

```powershell
# toàn bộ unit test (offline, miễn phí)
pytest

# chỉ test của 4 tool mới
pytest tests/test_tools_todo.py -v -k "rank_items or wiki or github_repo or hf_models"

# kiểm tra tools.yaml khớp với code (chạy lại mỗi khi thêm / đổi tên tool)
pytest tests/test_tool_contract.py

# eval case của nhóm (gọi model thật, tốn credit)
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

Thêm một tool mới nữa? Làm đủ 5 bước: `tools/<tên>/tool.py` → `tools/<tên>/TOOL.md` →
đăng ký trong `tools/__init__.py` → khai báo ở cuối `artifacts/tools.yaml` → viết ≥ 3
test và ≥ 1 eval case. Sau đó chạy lại base và extension để kiểm tra tool mới không làm
hỏng case cũ.
