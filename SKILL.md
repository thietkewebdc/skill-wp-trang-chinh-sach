---
name: wp-trang-chinh-sach-gioi-thieu
description: Tạo và đăng bộ trang GIỚI THIỆU + CHÍNH SÁCH (bảo mật, điều khoản, đổi trả, bảo hành, vận chuyển, thanh toán, khiếu nại, hướng dẫn mua hàng, liên hệ) lên website WordPress/Flatsome/WooCommerce của khách, theo luật Việt Nam. Khách chỉ cần điền file .env (URL, tài khoản, mật khẩu ứng dụng, tùy chọn SSH VPS/hosting). Dùng khi người dùng nói "tạo trang chính sách", "trang giới thiệu cho web", "chính sách đổi trả/bảo mật/vận chuyển", "đưa trang chính sách lên wordpress", "bộ trang pháp lý cho web bán hàng", hoặc gọi /wp-trang-chinh-sach-gioi-thieu.
---

# Trang giới thiệu & chính sách cho WordPress (Flatsome, web bán hàng)

Đầu vào: một file `.env` do khách điền. Đầu ra: 10 trang trên site (mặc định **bản nháp**), menu footer "Chính sách", đã gán Trang bảo mật (Cài đặt → Riêng tư) và Điều khoản (WooCommerce).

Thư mục skill: `~/.claude/skills/wp-trang-chinh-sach-gioi-thieu/`
- `.env.example` – mẫu `.env` để gửi cho khách
- `scripts/wp_push.py` – `check` / `build` / `push` (chỉ dùng thư viện chuẩn Python)
- `templates/*.html` – 10 mẫu, biến dạng `{{ten_thuong_hieu}}` ↔ `BIZ_TEN_THUONG_HIEU` trong .env

## Quy trình

1. **Chuẩn bị .env.** Làm việc trong thư mục riêng của khách (vd `~/Documents/code/khach-<ten>/`). Copy `.env.example` thành `.env` ở đó. Gửi khách phần hướng dẫn lấy Mật khẩu ứng dụng (ghi sẵn trong .env.example). Không dán mật khẩu khách vào chat, không commit `.env`.
2. **Phỏng vấn điền BIZ_\***. Hỏi một lượt: tên thương hiệu và pháp nhân, MST, địa chỉ, hotline/email/Zalo, bán gì, câu chuyện và sứ mệnh, thời hạn đổi trả/bảo hành, phí ship, thanh toán. Khách chưa có thì để trống, trang sẽ hiện `[CẦN ĐIỀN: …]` và **không cho đăng**.
3. **Kiểm tra kết nối:** `python3 <skill>/scripts/wp_push.py check --env .env`. Phải thấy: đăng nhập OK có quyền sửa trang, theme Flatsome, WooCommerce, vị trí menu, SSH OK (nếu có).
4. **Dựng thử:** `... build --env .env --out out` rồi đọc `out/*.html`, đối chiếu thông tin với trang sản phẩm/checkout thật của site (vd thời hạn đổi trả phải khớp mọi chỗ). Chỉnh nội dung theo ngành nếu cần (xem mục Tùy biến).
5. **Đẩy lên nháp:** `... push --env .env`. Báo khách xem lại từng trang ở WP Admin.
6. **Đăng:** khi khách duyệt, `... push --env .env --publish`. Script từ chối nếu còn biến thiếu.
7. **Soát cuối:** mở từng link, kiểm tra footer có menu, Cài đặt → Riêng tư đã chọn trang, form liên hệ gửi được (nếu dùng CF7).

Cờ hữu ích: `--only chinh-sach-doi-tra,gioi-thieu`, `--dry-run`, `--no-overwrite` (không đè trang đã có), `--no-menu`, `--no-settings`.

Chạy lại là **cập nhật** theo slug, không tạo trùng. Trang đang `publish` không bị hạ về nháp.

## Quyền truy cập khách cần cấp

| Thứ | Để làm gì | Bắt buộc |
|---|---|---|
| `WP_URL`, `WP_USER` (Administrator), `WP_APP_PASSWORD` | Tạo/sửa trang, menu qua REST API | Có |
| SSH VPS/hosting (`SSH_HOST`, `SSH_USER`, `SSH_KEY`, `WP_PATH`) | Gán Trang bảo mật/Điều khoản bằng WP-CLI, xóa cache | Không (không có thì làm tay 2 bước, script in hướng dẫn) |

Khuyên khách: tạo user SSH riêng quyền tối thiểu, dùng khóa SSH (không mật khẩu), thu hồi Mật khẩu ứng dụng sau khi xong. Hosting cPanel/shared thường không có SSH: bỏ trống khối SSH.

## Luật và nội dung (cần nhớ)

- Mẫu dựa trên: Luật Bảo vệ quyền lợi người tiêu dùng 2023, Nghị định 13/2023/NĐ-CP và Luật Bảo vệ dữ liệu cá nhân, Nghị định 52/2013 và 85/2021 về TMĐT. **Trước khi giao, kiểm tra văn bản còn hiệu lực** và nhắc khách: đây là mẫu chuẩn hóa, không thay thế tư vấn pháp lý.
- Web TMĐT bán hàng nên đăng ký/thông báo website với Bộ Công Thương (online.gov.vn) và gắn biểu tượng "Đã thông báo" ở footer; skill không làm bước này, nhắc khách.
- Không bịa số liệu: thông tin thiếu để trống, không tự điền.
- Quy chế sàn TMĐT (nhiều người bán) không có trong bộ mẫu: viết riêng.

## Flatsome

- `gioi-thieu`, `lien-he`: shortcode UX Builder (`[section][row][col][title][ux_text][button]`), mở "Sửa bằng UX Builder" chỉnh được. Muốn đẹp hơn (banner ảnh, icon box, đội ngũ) thì sửa template theo `flatsome-ux-builder` (`references/01`, `02`).
- Trang chính sách: HTML thuần bọc `[section][row][col span="10"]`, không có `<h1>` vì Flatsome đã hiện tiêu đề trang.
- Menu: gán vào vị trí `FOOTER_MENU_LOCATION` (mặc định `footer`). **Không ghi đè** nếu vị trí đó đã có menu khác, script cảnh báo; khi đó thêm bằng widget/Menu tay hoặc đổi vị trí.
- Form liên hệ: điền `BIZ_CF7_SHORTCODE` nếu site có Contact Form 7; không thì dùng element Form của Flatsome sau.

## Tùy biến

- Thêm/bớt trang: sửa danh sách `PAGES` đầu `wp_push.py` và thêm file trong `templates/`.
- Biến mới: thêm `{{ten_bien}}` vào template và `BIZ_TEN_BIEN` vào .env (biến tùy chọn thêm vào `OPTIONAL` trong script).
- Ngành đặc thù (thực phẩm, mỹ phẩm, thuốc, điện tử): thêm đoạn quy định riêng vào chính sách đổi trả/bảo hành trước khi đăng.

## Sự cố thường gặp

- **401 / rest_not_logged_in** dù đúng mật khẩu: host chặn header Authorization. Thêm vào `.htaccess` đầu file: `SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1` (hoặc `RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]`). Plugin bảo mật (Wordfence, iThemes) hoặc Cloudflare WAF cũng có thể chặn REST.
- **Không có mục Mật khẩu ứng dụng:** site chưa HTTPS (chỉ local mới bỏ qua), hoặc plugin bảo mật tắt tính năng.
- **404 `/wp-json/`:** permalink "Cơ bản"; script tự chuyển sang `?rest_route=`, nhưng nên đổi permalink "Tên bài viết".
- **SSL tự ký/local:** `WP_VERIFY_SSL=0`.
- **WP-CLI báo chạy root:** script tự thêm `--allow-root` khi `SSH_USER=root`.
- **Menu không hiện ở footer:** vị trí không đúng, chạy `check` để xem tên vị trí thật của theme/child theme.
