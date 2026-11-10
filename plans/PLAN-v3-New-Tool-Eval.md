# PLAN v3 — New Tool & Eval Expansion (Role C)

**Owner:** Thành viên C
**Version chạy:** `v3`
**Sở hữu:** `tools/<tên_mới>/**`, `tools/__init__.py` (append 1 dòng), `tests/test_tools_<tên_mới>.py`, `data/eval_group.json`, và **1 khối append ở CUỐI** `artifacts/tools.yaml`.

> ⚠️ C **không** đụng `system_prompt.md`, và **không sửa phần thân** `tools.yaml`
> (chỉ nối khối tool mới xuống cuối file, sau khi B đã freeze).

---

## 1. Mục tiêu

1. Viết **1 tool mới** hoàn chỉnh: `tools/<tên>/tool.py` + `TOOL.md`, đăng ký ở `tools/__init__.py` (`TOOL_FUNCTIONS`) và declare trong `artifacts/tools.yaml`.
2. **≥ 3 unit test** cho tool mới; giữ `pytest` xanh (challenge: 0 failed / 0 skipped).
3. Thêm **10 case** vào `data/eval_group.json` (5 single-turn + 5 multi-turn).

## 2. Chọn tool mới — đề xuất `rank_items` (tool local, không cần mạng)

Lý do chọn tool **local, không gọi mạng**: `tests/conftest.py` **chặn mọi HTTP thật** ⇒ tool offline thì test dễ xanh, không cần mock.

**Chức năng:** nhận danh sách item đã thu thập → khử trùng lặp + sắp xếp + cắt `top_k`.

### 2a. `tools/rank_items/TOOL.md`

```markdown
---
name: rank_items
track: core
kind: local_formatter
provider:
requires_env: []
inputs: [items, sort_by, dedupe, top_k]
outputs: [items, count, removed]
side_effect: false
---
# rank_items

Dedupes already-collected items and ranks them. It does NOT fetch data.
```

### 2b. `tools/rank_items/tool.py` (skeleton — tự hoàn thiện)

```python
from __future__ import annotations
from typing import Any

def rank_items(
    items: list[dict[str, Any]] | None = None,
    sort_by: str = "recency",
    dedupe: bool = True,
    top_k: int = 10,
) -> dict[str, Any]:
    if not isinstance(items, list):
        return {"error": "items must be a list"}
    if sort_by not in {"recency", "relevance", "score"}:
        return {"error": f"unsupported sort_by: {sort_by}"}

    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("url") or item.get("title") or "").strip().lower()
        if dedupe and key and key in seen:
            continue
        if key:
            seen.add(key)
        cleaned.append(item)

    if sort_by == "recency":
        cleaned.sort(key=lambda it: str(it.get("date") or it.get("published") or ""), reverse=True)
    elif sort_by == "score":
        cleaned.sort(key=lambda it: float(it.get("score") or 0), reverse=True)

    removed = len(items) - len(cleaned)
    k = max(0, int(top_k)) if isinstance(top_k, int) else 10
    result = cleaned[:k]
    return {"items": result, "count": len(result), "removed": removed}
```

### 2c. Đăng ký registry — `tools/__init__.py`

Thêm import + 1 dòng trong `TOOL_FUNCTIONS` (dòng ~38):

```python
from .rank_items.tool import rank_items
...
TOOL_FUNCTIONS = {
    ...,
    "rank_items": rank_items,
}
```

### 2d. Declare trong `artifacts/tools.yaml` — APPEND Ở CUỐI FILE

```yaml
  - name: rank_items
    description: "Khử trùng lặp và sắp xếp danh sách item đã thu thập. Dùng khi ĐÃ có items và user muốn xếp hạng/lọc/bỏ trùng. KHÔNG dùng để lấy dữ liệu mới."
    parameters:
      type: object
      properties:
        items:
          type: array
          default: []
          description: "Danh sách item đã có."
          items:
            type: object
            properties:
              title: {type: string}
              url: {type: string}
              date: {type: string}
              score: {type: number}
        sort_by: {type: string, enum: [recency, relevance, score], default: "recency", description: "Tiêu chí sắp xếp."}
        dedupe: {type: boolean, default: true, description: "Bỏ item trùng url/title."}
        top_k: {type: integer, default: 10, description: "Giữ tối đa bao nhiêu item."}
      required: [items]
```

## 3. Unit test — `tests/test_tools_rank_items.py` (≥ 3, gợi ý 5)

Một test một hành vi; assert **kết quả trả về**, không chỉ gọi hàm.

```python
from tools.rank_items.tool import rank_items

def test_dedupes_by_url():
    items = [
        {"title": "A", "url": "http://x"},
        {"title": "A dup", "url": "http://x"},
        {"title": "B", "url": "http://y"},
    ]
    out = rank_items(items=items)
    assert out["count"] == 2
    assert out["removed"] == 1

def test_respects_top_k():
    items = [{"title": str(i), "url": f"http://{i}"} for i in range(5)]
    out = rank_items(items=items, top_k=2)
    assert out["count"] == 2

def test_empty_input_returns_zero():
    out = rank_items(items=[])
    assert out == {"items": [], "count": 0, "removed": 0}

def test_non_list_input_returns_error_not_raise():
    out = rank_items(items="not-a-list")
    assert "error" in out

def test_top_k_zero_returns_empty():
    out = rank_items(items=[{"url": "http://x"}], top_k=0)
    assert out["count"] == 0
```

## 4. 10 case nhóm — `data/eval_group.json` (chỉ dùng tool đã declare)

> Điền vào mảng `"cases"` (đang rỗng). Mỗi case cần `id, phase="B", failure_type, expect, metadata.what_it_tests`.

**5 single-turn (G01–G05):**

| id | query | expect | failure_type |
|---|---|---|---|
| G01_timeline_handle | "Tweet mới nhất của Andrej Karpathy" | `timeline({screenname:"karpathy"})` | wrong_tool |
| G02_news_timeframe_month | "Tin công nghệ tháng này" | `lookup({topic:"news", timeframe:"month"})` | wrong_arg_value |
| G03_missing_keyword | "Tìm giúp mình tin này" | `clarify({response_type:"text"})` | missing_info |
| G04_out_of_scope_chitchat | "Kể cho mình một câu chuyện cười" | `no_tool=true`, refuse | out_of_scope |
| G05_confirm_send | "Đăng bản tin này lên Telegram giúp mình" | `clarify({response_type:"yes_no"})` | wrong_boundary |

**5 multi-turn (G06–G10, dùng `turns`, chỉ chấm lượt cuối):**

| id | turns (rút gọn) | expect | failure_type |
|---|---|---|---|
| G06_clarify_then_handle | "Tóm tắt 3 tweet mới nhất" / "Của Elon Musk" / "Đúng 3 thôi" | `timeline({screenname:"elonmusk", limit:3})` | missing_info |
| G07_switch_tool | "Mọi người nói gì về AI trên Twitter?" / "Bỏ Twitter, tìm web tin tức" / "Giữ chủ đề AI" | `lookup({query:"AI", topic:"news"})` | wrong_tool |
| G08_correction_handle | "Tweet của Sam Altman" / "À nhầm, Karpathy" / "Lấy 5 cái" | `timeline({screenname:"karpathy", limit:5})` | wrong_arg_value |
| G09_carryover_timeframe | "Tin AI hôm nay" / "Còn robotics?" / "Chỉ robotics, vẫn hôm nay" | `lookup({query:"robotics", topic:"news", timeframe:"day"})` | wrong_arg_value |
| G10_clarify_then_url | "Tóm tắt bài này" / "https://openai.com/blog/gpt-5" / "Chỉ đọc link đó" | `fetch({url:"https://openai.com/blog/gpt-5"})` | missing_info |

> ⚠️ Tránh case dẫn tới `send(confirmed=true)` trong eval (gây side-effect thật lên Telegram). Nếu muốn đo, để riêng và chấp nhận có thể chạm mạng.

## 5. Cách verify

```powershell
cd starter_v0

# 1) Contract + unit test tool mới
pytest tests/test_tool_contract.py tests/test_tools_rank_items.py -v

# 2) Toàn bộ test (challenge: 0 failed, 0 skipped)
pytest

# 3) (sau khi ghép A+B) base suite ở v3 — kiểm tool mới không bị gọi thừa
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json

# 4) Suite nhóm
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

## 6. Điều kiện đạt (DoD)

- `tools/rank_items/tool.py` + `TOOL.md` tồn tại; name khớp frontmatter.
- Đã register ở `TOOL_FUNCTIONS` **và** declare cuối `tools.yaml` (contract test xanh).
- ≥ 3 test cho tool mới; `pytest` xanh (đích challenge: 0 failed / 0 skipped).
- `data/eval_group.json` có đủ 10 case (5 single + 5 multi), mỗi case có `metadata.what_it_tests`.
- Suite `group` chạy được, `case_accuracy` ghi vào báo cáo.

## 7. Rủi ro cần theo dõi

- Thêm tool mới ⇒ model có thể **gọi thừa** (`extra_tool_call`) làm giảm base accuracy ở v3. Bắt buộc đo lại base suite ở v3, không chỉ group.
- Nếu rename/đổi tên tool: phải đồng bộ **3 nơi** (`tools.yaml` ↔ `TOOL_FUNCTIONS` ↔ `eval_*.json`).
- `test_tool_contract.py:70` quét `eval_group.json`: case nhóm **chỉ được expect tool đã declare**.

## 8. Ghi log

Thêm 1 dòng `v3` vào `artifacts/version_log.csv`: `author=<tên C>`,
`changed_artifact=tools.yaml+tools/rank_items`, `hypothesis="thêm tool rank_items (local) + 10 case nhóm; đo base để bắt extra_tool_call"`.
