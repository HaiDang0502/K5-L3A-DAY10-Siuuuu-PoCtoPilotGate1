# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): Siuuuu
- Lớp: `L3A`
- Repo của bàn: `K5-L3A-DAY10-Siuuuu-PoCtoPilotGate1`
- Thẻ sự cố đã bốc (S1–S8): S4

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; thêm dòng nếu cần. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 | Đặng Thanh Hải | 2A202603570 | Kỹ sư cổng (chạy lệnh, `guards.py`) | ✔ |
|   2 | Lê Hải Bắc | 2A202603710 | Kỹ sư cổng (trace, behavioral test, `monitors.py`) | |
|   3 | Hoàng Gia Khiêm | 2A202603540 | Sản phẩm và kinh doanh | |
|   4 | Lê Nhật Linh | 2A202603514 | Vận hành và pháp lý | |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## DangThanhHai-2A202603570

### Phần việc phụ trách

Kỹ sư cổng 1, trưởng nhóm, máy chạy mọi lệnh chính thức. Phiếu B: B0, B1, B7.1; Phiếu C: C0, C1, C7. File: `lab10/guards.py`; lệnh 1, 2, 4, 5, 6, 7.

### Đóng góp cụ thể

Ký tiêu chí trước lần đo đầu; chạy base, after, prepared; viết 3 cổng vòng 1 (G1 tiền khớp nguồn sự thật + ghim chính sách theo ngày, G2 lỗi hãng đúng kiện, G3 bỏ PII khỏi thông báo cho hãng); chốt vòng 1.

### Bằng chứng

Commit `1ae6b1b` (Sign acceptance criteria), `bffc297` (chốt vòng 1); `runs/R-base-before-20261118-145250-b45eeb`, `runs/R-base-after-20261118-145447-a601d0`, `runs/R-base-prepared-20261118-145503-a601d0`; checkpoint `9ba05ad4`.

### Exit ticket

**Một điều học được:** Chốt cổng trước khi biết thẻ S4 giúp tách phần an toàn khỏi phần vận hành: ở mốc prepared, tiền hoàn sai và lỗi oan cho hãng đều về 0, nhưng vẫn còn 11 ca ùn. Tôi phải đọc cả ba mốc và đối chiếu với tiêu chí đã ký, không chỉ nhìn số lỗi bằng 0.

**Một điều còn chưa chắc:** G1 và G2 dựa vào tracking DB và chính sách theo ngày. Nếu dữ liệu nguồn ghi sai nguyên nhân trễ hoặc ngày giao, cổng vẫn có thể quyết định sai. Cần đối soát dữ liệu thật và chạy lại khi chính sách đổi trước Gate 2.

**Sử dụng AI:** Tôi đã dùng trợ lý AI để soạn nháp cổng và phiếu; tôi và nhóm đọc lại, kiểm tra bằng report và chịu trách nhiệm giải thích các con số.

## LeHaiBac-2A202603710

### Phần việc phụ trách

Kỹ sư cổng 2. Phiếu A: câu 1.3, 1.5; Phiếu B: B2, B7.2, B7.3; Phiếu C: C2, C5, C6, C8, C9. File: `lab10/monitors.py`.

### Đóng góp cụ thể

Dò trace `T-002@55` và điền bảng soát lỗi; hai ticket hiểm (`O-1002`, `O-1026`) cho behavioral test.

### Bằng chứng

Phiếu B mục B2, B7.3; Phiếu A mục A2 (cột Offline), A3.

### Exit ticket

**Một điều học được:** Trace của một ticket cho thấy đường đi tới lỗi, còn behavioral test trên ticket khác kiểm tra cổng có giữ được quy tắc hay không. Với S4, `review_peak_per_hour` tăng từ 1 ở bộ nền lên 20 ở mốc prepared; chỉ nhìn `pass_rate` sẽ bỏ sót hàng chờ của người duyệt.

**Một điều còn chưa chắc:** Ngưỡng cảnh báo > 5 ca/giờ dựa trên công suất giả định 6 ca/giờ của một người. Khi pilot thật, cần đo thời gian duyệt từng loại ca và thời điểm ticket tới để biết cảnh báo có đủ sớm không.

## HoangGiaKhiem-2A202603540

### Phần việc phụ trách

Sản phẩm và kinh doanh. Phiếu A: câu 1.1, 1.6, A5; Phiếu B: B3, B7.4, B8; Phiếu C: C10, C12. File: `config/acceptance_criteria.json`, `config/operating_gates.json` mục `business`.

### Đóng góp cụ thể

Ngưỡng tiêu chí (pass_rate 0,97, pass_k 0,95, an toàn = 0, chi phí ≤ 6.000đ, ROI ≥ 0,3, ca ùn 0); `decision_rule`; cổng business (trần ngày 1.500.000đ, 1.500đ LLM/ticket); quyết định v1.

### Bằng chứng

`config/acceptance_criteria.json` (hash `19cf5b70`); Phiếu A mục A4; Phiếu B mục B7.4, B8.

### Exit ticket

**Một điều học được:** Tiêu chí phải ký trước khi nhìn số, và mỗi ngưỡng phải đi kèm hành động ("Nếu … thì chúng tôi sẽ …"). Khi ký ngưỡng chi phí ≤ 6.000đ/ticket và ROI ≥ 0,3, tôi mới thấy "thêm người trực cho hết ùn" không phải lời giải miễn phí. Mỗi người thêm tốn phí giữ chỗ, có thể đẩy chi phí vượt ngưỡng đã ký. Quyết định đúng phải khớp cả chất lượng lẫn tiền và người, không chỉ pass_rate.

**Một điều còn chưa chắc:** Các con số tôi đặt (trần hoàn tự động 1.500.000đ/ngày, ROI ≥ 0,3, 1 người duyệt 6 ca/giờ) đều dựa trên dữ liệu mock của một ngày. Tôi chưa chắc chúng còn đúng khi chạy pilot thật: ngày sale thì Finance đổi ngân sách theo ngày, tỉ lệ hàng vỡ/thất lạc mỗi kho khác nhau. Cần đo lại trong pilot trước Bước đánh giá 2.

## LeNhatLinh-2A202603514

### Phần việc phụ trách

Vận hành và pháp lý. Phiếu A: câu 1.2, 1.4; Phiếu B: B4, B5, B7.5, B7.6; Phiếu C: C4, C11. File: `config/operating_gates.json` mục `operations`, `legal`; `submission/submission.json`.

### Đóng góp cụ thể

HAZOP vòng 1 (5 dòng kỹ thuật + 4 dòng ngoài kỹ thuật), checklist 9 nhóm có PIC, cổng operations/legal, runbook 1–3 và giờ cao điểm (đo thử 2 người trực ở `R-base-after-20261118-145856-4ec698`).

### Bằng chứng

Phiếu B mục B4, B5, B7.5, B7.6; `config/operating_gates.json`.

### Exit ticket

**Một điều học được:** Cổng an toàn chuyển thêm ca cho người duyệt có thể làm vận hành quá tải. Ở mốc prepared của S4, 11 ca bị ùn và chờ lâu nhất 136 phút; thêm người trực cố định cũng tăng chi phí. Vì vậy runbook cần có người chịu trách nhiệm, ngưỡng gọi thêm người và điều kiện thu hẹp phạm vi.

**Một điều còn chưa chắc:** Số liệu mock chưa cho biết người trực mất bao lâu với ca vỡ hoặc thất lạc trong ngày sale thật. Cần đo hàng chờ theo giờ, thời gian xử lý thực tế và kiểm tra việc trực ca có làm đúng ngưỡng dừng trước khi mở rộng pilot.
