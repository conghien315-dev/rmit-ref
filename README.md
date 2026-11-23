# RMIT Ref 📚

**Skill cho Claude giúp sinh viên RMIT làm reference theo RMIT Harvard dễ hơn, và kiểm tra nguồn — kể cả nguồn ảo do AI bịa ra — một cách có bằng chứng.**
*A Claude skill that helps RMIT students reference in RMIT Harvard style and verify that every source is real — with evidence.*

[Tiếng Việt](#tiếng-việt) · [English](#english)

---

## Tiếng Việt

### Skill này làm được gì?

| Việc | Ví dụ bạn có thể nói với Claude |
|---|---|
| **Tạo reference** từ DOI, link, tên sách, ảnh chụp, PDF | "Làm ref RMIT Harvard cho DOI 10.1080/09650792.2019.1652196" |
| **Sửa reference list** (chuyển từ APA, sửa lỗi dấu, sắp xếp ABC) | "Check giúp mình reference list này đúng RMIT Harvard chưa" |
| **Check in-text citation** khớp với reference list | "Bài essay của mình có cite thiếu nguồn nào không?" |
| **Phát hiện nguồn ảo** (AI bịa, DOI sai, link chết, bài bị rút) | "Mấy nguồn này ChatGPT đưa, check xem có thật không" |
| **Ghi nhận dùng AI** theo hướng dẫn RMIT (cập nhật 02/2026) | "Mình dùng ChatGPT để brainstorm, ghi nhận sao cho đúng?" |
| **Tổng hợp nguồn (synthesis)** bằng synthesis matrix — skill `synthesizing` | "Mình có 4 bài báo về TikTok marketing, giúp mình làm synthesis matrix rồi viết đoạn tổng hợp" |

### Skill thứ hai: `synthesizing` 🧩

Biến ghi chú đọc tài liệu thành **synthesis matrix**: mỗi hàng là một *ý* (không phải một bài), mỗi cột là một nguồn, đánh dấu nguồn nào **đồng ý ●**, **đồng ý một phần / góc nhìn khác ◐**, **phản đối ⊘**, hay **đưa ra ý khác ✚**, cộng cột ghi chú về độ mạnh lập luận, mức liên quan và độ tin cậy. Skill tự nhận ra kiểu quan hệ của từng ý (đồng thuận, đa số có ý kiến khác, còn tranh cãi, chỉ một nguồn, khoảng trống), xuất bảng ra Markdown / CSV (mở bằng Excel) / HTML màu để in, rồi hướng dẫn viết đoạn văn tổng hợp với trích dẫn RMIT Harvard. Ví dụ: [`examples/synthesis-matrix.json`](examples/synthesis-matrix.json).

### Kiểm tra nguồn "khoa học" nghĩa là gì?

Một reference trông hợp lý chưa chắc đã có thật — nguồn ảo được tạo ra để *trông* hợp lý. Vì vậy skill không đoán, mà **đối chiếu với các cơ sở dữ liệu độc lập** và báo cáo bằng chứng:

1. **DOI** → tra Crossref + doi.org: DOI có tồn tại không? Có trỏ đúng bài được cite không?
2. **Tìm kiếm thư mục** trên Crossref **và** OpenAlex (2 nguồn độc lập), so khớp tên bài, tác giả, năm.
3. **Sách** → kiểm tra checksum ISBN + Open Library.
4. **Link web** → link còn sống không; nếu chết, tìm bản lưu trên Wayback Machine.
5. **Bài bị rút (retracted)** → cờ `is_retracted` của OpenAlex.
6. Claude kiểm tra thêm phần máy không làm được: tạp chí có đăng chủ đề đó không, số volume/trang có hợp lý không, nguồn có thật sự nói điều bạn cite không.

Mỗi nguồn nhận một kết luận (`VERIFIED`, `FOUND_WITH_ERRORS`, `DOI_MISMATCH`, `NOT_FOUND`, `RETRACTED`, `LINK_DEAD`...) kèm **mức bằng chứng A–E**. Lưu ý: *"không tìm thấy" ≠ "chắc chắn giả"* — tài liệu tiếng Việt, tài liệu nội bộ, báo cáo công ty thường không có trong các cơ sở dữ liệu này. Chi tiết: [`verification-method.md`](skills/rmit-ref/references/verification-method.md).

### Cài đặt

**Cách 1 — Claude Code (plugin):**
```bash
/plugin marketplace add conghien315-dev/rmit-ref
/plugin install rmit-ref@rmit-ref
```

**Cách 2 — copy thủ công (Claude Code):**
```bash
git clone https://github.com/conghien315-dev/rmit-ref.git
cp -r rmit-ref/skills/rmit-ref rmit-ref/skills/synthesizing ~/.claude/skills/
```

**Cách 3 — Claude.ai / Claude Desktop:** nén thư mục `skills/rmit-ref` (và `skills/synthesizing`, mỗi skill một file `.zip`), rồi vào **Settings → Capabilities → Skills → Upload skill**.

**Cách 4 — ChatGPT:** tạo một Custom GPT theo hướng dẫn từng bước trong [`chatgpt/`](chatgpt/README.md) (dán sẵn instructions + Actions tra Crossref/OpenAlex/Open Library).

Yêu cầu: Python 3 (không cần cài thư viện thêm) và kết nối internet để kiểm tra nguồn. Tùy chọn: đặt biến `OPENALEX_API_KEY` (key miễn phí tại openalex.org) nếu kiểm tra nhiều nguồn mỗi ngày.

### Dùng script trực tiếp (không cần Claude)

```bash
python3 skills/rmit-ref/scripts/verify_refs.py my-refs.txt
python3 skills/rmit-ref/scripts/verify_refs.py --from-doi 10.1080/09650792.2019.1652196
python3 skills/rmit-ref/scripts/check_format.py my-refs.txt --text my-essay.txt
python3 skills/synthesizing/scripts/build_matrix.py examples/synthesis-matrix.json --print
```
`my-refs.txt`: mỗi reference một dòng (hoặc cách nhau bằng dòng trống). Có file mẫu trong [`examples/`](examples/).

### Lưu ý quan trọng

- Đây là **công cụ hỗ trợ, không phải công cụ chính thức của RMIT**. [Easy Cite](https://www.lib.rmit.edu.au/easy-cite/) và hướng dẫn của môn học / giảng viên luôn là chuẩn cuối cùng.
- Skill sẽ **không** bịa nguồn hay "làm đẹp" nguồn giả. Nếu nguồn không có thật, cách sửa đúng là tìm nguồn thật và đọc nó.

---

## English

### What it does

- **Build references** in RMIT Harvard from a DOI, URL, title, screenshot or PDF — with matching in-text citations `(Author Year)`, `Author (Year)`, `(Author Year:page)`.
- **Fix reference lists**: converts APA habits (`&`, `p.`, `https://doi.org/`, `Retrieved from`...), sentence case, alphabetical order, `a`/`b` years.
- **Cross-check** in-text citations against the reference list (missing, never cited, `et al.` misuse).
- **Verify sources** against Crossref, OpenAlex, doi.org, Open Library and the Wayback Machine, flagging fabricated (AI-hallucinated) references, borrowed/phantom DOIs, dead links and retracted papers — each with an evidence tier.
- **AI acknowledgement** and AI-tool references per RMIT's February 2026 guidance.
- **Synthesis** (second skill, `synthesizing`): builds a synthesis matrix — ideas as rows, sources as columns, stance markers (● agree, ◐ partial/different perspective, ⊘ disagree, ✚ alternative) and a notes column on argument strength, relevance and reliability — infers the pattern per idea (consensus, majority with dissent, contested, single-source, gap), exports Markdown/CSV/HTML, and scaffolds synthesised paragraphs with RMIT Harvard citations.

The style rules are distilled from RMIT Library's Easy Cite RMIT Harvard guide: [`rmit-harvard.md`](skills/rmit-ref/references/rmit-harvard.md).

### Install

- **Claude Code plugin:** `/plugin marketplace add conghien315-dev/rmit-ref`, then `/plugin install rmit-ref@rmit-ref`.
- **Manual (Claude Code):** copy `skills/rmit-ref` and `skills/synthesizing` into `~/.claude/skills/`.
- **Claude.ai / Desktop:** zip `skills/rmit-ref` (and `skills/synthesizing`, one zip each) and upload it under Settings → Capabilities → Skills.
- **ChatGPT:** build a Custom GPT with the ready-made instructions and Actions in [`chatgpt/`](chatgpt/README.md).

Optional: set `OPENALEX_API_KEY` (free key from openalex.org) for heavier use — OpenAlex's keyless quota is shared per IP address.

Requires Python 3 (standard library only) and internet access for verification.

### Repository layout

```
.claude-plugin/          plugin + marketplace manifests
skills/rmit-ref/
  SKILL.md               instructions Claude follows
  references/
    rmit-harvard.md      RMIT Harvard rules and templates (from Easy Cite)
    verification-method.md  evidence tiers, verdicts, fabrication patterns, limits
  scripts/
    verify_refs.py       registry-based source verification + DOI → reference drafts
    check_format.py      offline RMIT Harvard linter + in-text cross-check
skills/synthesizing/
  SKILL.md               synthesis-matrix workflow
  references/synthesis-guide.md  patterns, evaluation, paragraph templates, verbs
  scripts/build_matrix.py        matrix JSON → Markdown / CSV / HTML
chatgpt/                 Custom GPT kit (instructions, Action schemas, guide)
examples/                sample reference list, essay and synthesis matrix
```

### Disclaimer

Not affiliated with or endorsed by RMIT University. Easy Cite and your course guide are the final authority. Registry absence is evidence, not proof, of fabrication.

### Contributing

Issues and PRs welcome — especially new source types, Vietnamese-source verification ideas, and test cases where the checker got it wrong.

License: MIT
