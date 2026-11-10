# Hướng dẫn tổng hợp Lab Day 03 — Research Agent Tool Eval

## Mục tiêu

Xây dựng một research agent có thể chọn và gọi tool, sau đó dùng kết quả chạy thật để cải thiện prompt và khai báo tool qua các phiên bản `v0`–`v3`. Hãy dựa vào log và số liệu, không chỉ đánh giá câu trả lời bằng cảm giác.

Các hướng dẫn chi tiết của bài nằm trong [README.md](README.md), cấu hình API nằm trong [docs/TOOL-SETUP.md](docs/TOOL-SETUP.md), mẫu báo cáo nằm trong [report/team/group_report.md](report/team/group_report.md).

## Các bước thực hiện

### 1. Mở đúng thư mục

Mở PowerShell tại thư mục `starter_v0`:

```powershell
cd D:\AI20K\Day_3\Lab\K5-L3B-DAY03-CR7-ResearchAgentToolEval\starter_v0
```

Các lệnh bên dưới giả định bạn đang chạy từ thư mục này.

### 2. Tạo môi trường Python và cài thư viện

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Nếu PowerShell chặn kích hoạt môi trường, có thể gọi Python trong môi trường trực tiếp bằng `.\.venv\Scripts\python.exe`.

### 3. Cấu hình API key

Tạo file `.env` trong `starter_v0` và thêm các khóa bạn đã có. Ví dụ:

```text
OPENROUTER_API_KEY=...
TAVILY_API_KEY=...
FIRECRAWL_API_KEY=...
RAPIDAPI_KEY=...
RAPIDAPI_TWITTER_HOST=twitter-api45.p.rapidapi.com
```

OpenRouter là provider được khuyến nghị; có thể dùng OpenAI, Anthropic hoặc Gemini thay thế. Telegram và arXiv là tùy chọn/bonus; xem [docs/TOOL-SETUP.md](docs/TOOL-SETUP.md) để biết cách cấu hình.

**Không đưa `.env` hoặc API key vào Git, báo cáo, ảnh chụp màn hình hay transcript.**

### 4. Kiểm tra provider trước khi chạy

```powershell
python scripts/preflight_provider.py --provider openrouter
```

Chỉ tiếp tục khi kiểm tra thành công. Nếu lỗi, kiểm tra key, thư viện đã cài và kết nối mạng.

### 5. Chạy baseline `v0`

Chạy bộ eval gốc. Không chỉnh sửa các case trong `data/eval_base.json`.

```powershell
python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json
```

Lệnh tạo log trong `runs/`. Đọc các metric:

- `case_accuracy`
- `tool_routing_accuracy`
- `argument_accuracy`
- `multiturn_accuracy`

Với từng case thất bại, xem `failures`, `observed_mismatch` và `actual_tool_calls` để xác định agent chọn sai tool, sai arguments, thiếu thông tin hay gọi tool không cần thiết.

### 6. Sửa prompt và khai báo tool dựa trên lỗi

Hai file chính cần cải thiện:

- `artifacts/system_prompt.md`: quy tắc ứng xử và định tuyến tool.
- `artifacts/tools.yaml`: mô tả mỗi tool, khi nào dùng/không dùng và quy ước arguments.

Prompt ban đầu có các hướng dẫn cố ý không phù hợp với mục tiêu lab, như đoán khi thiếu thông tin, tự gửi nội dung khi chưa xác nhận và cố làm mọi việc trong một bước. Hãy sửa chúng. Mỗi vòng chỉ nên kiểm tra **một thay đổi/giả thuyết**, rồi chạy lại eval và so sánh metric.

### 7. Chạy các phiên bản `v1`, `v2`, `v3`

```powershell
python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json
python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json
```

Sau mỗi lần chạy, ghi vào `artifacts/version_log.csv`: artifact đã sửa, giả thuyết, metric trước/sau, hash và tên file run. Đây là bằng chứng cho thấy thay đổi có cải thiện agent hay không.

### 8. Viết một tool mới và kiểm thử

Mỗi tool nằm trong một thư mục riêng, gồm `tool.py` và `TOOL.md`. Hợp đồng thư mục được mô tả trong `starter_v0/tools/README.md`.

Để thêm tool:

1. Tạo implementation và `TOOL.md`.
2. Đăng ký tool trong `tools/__init__.py`.
3. Khai báo tool trong `artifacts/tools.yaml`.
4. Viết **ít nhất 3 unit test**: trường hợp chạy bình thường, input không hợp lệ và nhánh lỗi.
5. Thêm eval case kiểm tra model có chọn đúng tool mới.

Chạy test:

```powershell
pytest
```

Eval kiểm tra model chọn tool/arguments có đúng không; unit test kiểm tra code của tool hoạt động đúng không. Challenge của bài yêu cầu điền các test đang bị skip; nếu làm challenge, mục tiêu là `0 failed, 0 skipped`.

### 9. Thêm eval case của nhóm

Bổ sung `data/eval_group.json`. Yêu cầu tổng thể là **10 case: 5 single-turn và 5 multi-turn**. Mỗi case cần có ID, `phase: "B"`, nội dung truy vấn hoặc các lượt hội thoại, loại lỗi cần kiểm tra, kết quả mong đợi và `metadata.what_it_tests`.

Chạy:

```powershell
python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json
```

Không sửa nội dung các case baseline trong `data/eval_base.json`.

### 10. Thử chat trực tiếp

```powershell
python chat.py --provider openrouter --version v3
```

Thử ít nhất 3 tình huống:

1. Yêu cầu nghiên cứu thông thường.
2. Yêu cầu còn thiếu tài khoản hoặc URL để agent phải hỏi lại.
3. Yêu cầu gửi nội dung để kiểm tra agent có chờ xác nhận hay không.

Transcript được ghi trong `transcripts/`.

### 11. Làm UI và chuẩn bị demo

Lab yêu cầu có UI chạy được bằng Streamlit hoặc Vercel. Nếu dự án có `app.py`, chạy UI Streamlit bằng:

```powershell
streamlit run app.py
```

Sau đó mở `http://localhost:8501`. Nếu cần cho nhóm khác truy cập, có thể dùng Cloudflare Tunnel:

```powershell
cloudflared tunnel --url http://localhost:8501
```

Dùng link được tạo trong phần giới thiệu báo cáo. Link tunnel là tạm thời và chỉ hoạt động khi tiến trình `cloudflared` còn chạy. Nếu chưa có file UI, cần xây dựng UI trước khi chạy các lệnh trên.

### 12. Hoàn thiện báo cáo và nộp

Hoàn thiện `report/team/group_report.md`:

- **Phần A:** giới thiệu agent, liệt kê tool và đưa ra vài câu hỏi mẫu; hoàn thành trước buổi demo.
- **Phần B:** điền bằng chứng từ run JSON, version log, eval, transcript và unit test; hoàn thiện để nộp.

Các đầu ra chính cần giữ gồm prompt, khai báo tool, version log có `v0`–`v3`, báo cáo, eval của nhóm, unit test, run JSON và transcript. **Không nộp `.env` hoặc API key.**

## Thứ tự ưu tiên nếu thời gian gấp

1. Cài môi trường, cấu hình key và chạy preflight.
2. Chạy baseline `v0`.
3. Cải thiện prompt/tools và chạy đủ `v1`–`v3`.
4. Thêm tool mới, viết test và eval case.
5. Thử chat, làm UI, rồi điền báo cáo từ log thật.

## Vòng lặp cải thiện quan trọng nhất

**Chạy eval → đọc lỗi trong log → đặt một giả thuyết → sửa một thay đổi → chạy lại → ghi metric và bằng chứng.**
