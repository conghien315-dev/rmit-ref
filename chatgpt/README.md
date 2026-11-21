# Dùng RMIT Ref trên ChatGPT (Custom GPT)

Thư mục này giúp bạn tạo một **Custom GPT** có cùng chức năng với skill Claude: làm ref RMIT Harvard và kiểm tra nguồn ảo bằng cách tra cứu cơ sở dữ liệu học thuật thật (Crossref, OpenAlex, Open Library).

Bạn (người tạo) làm **một lần**, rồi chia sẻ link GPT cho các bạn sinh viên khác dùng.

> Cần: tài khoản ChatGPT có quyền tạo GPT (thường là gói trả phí). Giao diện ChatGPT có thể thay đổi theo thời gian — nếu tên nút khác một chút, hãy tìm mục tương đương.

## Các file

| File | Dán / tải vào đâu |
|---|---|
| [`instructions.md`](instructions.md) | Ô **Instructions** |
| [`../skills/rmit-ref/references/rmit-harvard.md`](../skills/rmit-ref/references/rmit-harvard.md) | **Knowledge** (tải lên) |
| [`../skills/rmit-ref/references/verification-method.md`](../skills/rmit-ref/references/verification-method.md) | **Knowledge** (tải lên) |
| [`actions/crossref.yaml`](actions/crossref.yaml) | **Action** 1 — bắt buộc |
| [`actions/openlibrary.yaml`](actions/openlibrary.yaml) | **Action** 2 — nên có (kiểm tra sách) |
| [`actions/openalex.yaml`](actions/openalex.yaml) | **Action** 3 — tùy chọn, cần API key miễn phí |
| [`PRIVACY.md`](PRIVACY.md) | Link chính sách quyền riêng tư (bắt buộc khi GPT có Action và để công khai) |

## Các bước

### 1. Tạo GPT
1. Vào https://chatgpt.com/gpts/editor (hoặc **Explore GPTs → + Create**).
2. Chọn tab **Configure**.

### 2. Điền thông tin
- **Name:** `RMIT Ref`
- **Description:** `Làm reference RMIT Harvard và kiểm tra nguồn ảo bằng Crossref/OpenAlex. Not affiliated with RMIT University.`
- **Instructions:** mở [`instructions.md`](instructions.md) → bấm nút **Raw** → copy toàn bộ → dán vào.
- **Conversation starters** (gợi ý):
  - `Check giúp mình reference list này có nguồn nào ảo không`
  - `Làm ref RMIT Harvard cho DOI 10.1080/09544828.2021.1928024`
  - `Chuyển reference list APA này sang RMIT Harvard`
  - `Mình dùng ChatGPT để brainstorm, ghi nhận theo RMIT thế nào?`

### 3. Knowledge
Tải lên 2 file `rmit-harvard.md` và `verification-method.md` (bấm vào file trên GitHub → nút **Download raw file**).

### 4. Capabilities
- ✅ **Web Search** — để mở kiểm tra các nguồn là trang web.
- Code Interpreter: không cần.

### 5. Actions (phần quan trọng nhất)
Bấm **Create new action** cho từng file:

**Action 1 — Crossref (bắt buộc)**
1. Authentication: **None**.
2. Schema: mở [`actions/crossref.yaml`](actions/crossref.yaml) → **Raw** → copy → dán vào ô Schema.
3. Privacy policy: `https://github.com/conghien315-dev/rmit-ref/blob/main/chatgpt/PRIVACY.md`
4. Bấm **Test** cạnh `crossrefWorks` → nếu thấy kết quả JSON là được.

**Action 2 — Open Library (nên có):** làm giống hệt với [`actions/openlibrary.yaml`](actions/openlibrary.yaml), Authentication **None**.

**Action 3 — OpenAlex (tùy chọn, nên có nếu nhiều người dùng)**
OpenAlex cho dùng miễn phí nhưng **không có key thì giới hạn rất thấp** (dùng chung theo địa chỉ IP — mà mọi GPT đều gọi từ IP của OpenAI, nên sẽ nhanh hết lượt).
1. Lấy key miễn phí tại https://openalex.org/settings/api (đăng ký bằng email của bạn).
2. Authentication: **API Key** → Auth type: **Bearer** → dán key.
3. Schema: [`actions/openalex.yaml`](actions/openalex.yaml).

Không làm Action 3 cũng được — GPT vẫn kiểm tra bằng Crossref (nguồn chính) và Open Library.

### 6. Thử và chia sẻ
1. Ở khung **Preview** bên phải, dán file [`../examples/sample-refs.txt`](../examples/sample-refs.txt) và nhờ check. Kết quả đúng sẽ là: Papadopoulou ✅, Fiorineschi sai năm (2021), "TikTok…" DOI_MISMATCH, "Blockchain…" DOI không tồn tại.
2. Lần đầu GPT gọi Action, ChatGPT sẽ hỏi **Allow** — bấm **Always allow**.
3. Bấm **Create / Update** → chọn **Anyone with the link** (hoặc **GPT Store**) → copy link chia sẻ.

## Khác biệt so với bản Claude

| | Claude skill | Custom GPT |
|---|---|---|
| Tra Crossref, Open Library | ✅ qua script | ✅ qua Actions |
| OpenAlex | ✅ | ✅ nếu có API key |
| Kiểm tra link chết + Wayback Machine | ✅ | ⚠️ dùng Web Search, không tự động |
| Kiểm tra định dạng tự động (`check_format.py`) | ✅ | ❌ GPT tự soát theo quy tắc |
| Kiểm tra DOI không thuộc Crossref (DataCite) | ✅ qua doi.org | ⚠️ hạn chế |

## Cập nhật
Khi quy tắc hoặc hướng dẫn trong repo thay đổi: dán lại `instructions.md`, tải lại 2 file Knowledge, rồi bấm **Update**.
