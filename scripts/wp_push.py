#!/usr/bin/env python3
"""Tạo trang giới thiệu / chính sách cho WordPress (Flatsome) từ .env.

Lệnh:
  check   Kiểm tra kết nối REST, theme, WooCommerce, SSH, vị trí menu
  build   Dựng thử ra thư mục out/ (không gửi lên site), báo biến còn thiếu
  push    Tạo/cập nhật trang trên site (mặc định bản nháp), menu, cài đặt
Chỉ dùng thư viện chuẩn Python 3.8+.
"""
import argparse, base64, datetime, json, os, re, shlex, ssl, subprocess, sys
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TPL_DIR = SKILL_DIR / "templates"

# slug, tiêu đề, file mẫu, nhóm (info = giới thiệu, policy = vào menu chính sách)
PAGES = [
    ("gioi-thieu", "Giới thiệu", "gioi-thieu.html", "info"),
    ("lien-he", "Liên hệ", "lien-he.html", "info"),
    ("huong-dan-mua-hang", "Hướng dẫn mua hàng", "huong-dan-mua-hang.html", "policy"),
    ("chinh-sach-doi-tra", "Chính sách đổi trả và hoàn tiền", "chinh-sach-doi-tra.html", "policy"),
    ("chinh-sach-bao-hanh", "Chính sách bảo hành", "chinh-sach-bao-hanh.html", "policy"),
    ("chinh-sach-van-chuyen", "Chính sách vận chuyển và giao nhận", "chinh-sach-van-chuyen.html", "policy"),
    ("chinh-sach-thanh-toan", "Chính sách thanh toán", "chinh-sach-thanh-toan.html", "policy"),
    ("chinh-sach-bao-mat", "Chính sách bảo mật thông tin", "chinh-sach-bao-mat.html", "policy"),
    ("dieu-khoan-su-dung", "Điều khoản sử dụng", "dieu-khoan-su-dung.html", "policy"),
    ("giai-quyet-khieu-nai", "Quy trình giải quyết khiếu nại", "giai-quyet-khieu-nai.html", "policy"),
]
OPTIONAL = {"cf7_shortcode", "map_embed", "zalo"}   # trống thì thôi, không chặn đăng
PRIVACY_SLUG, TERMS_SLUG = "chinh-sach-bao-mat", "dieu-khoan-su-dung"

# bọc nội dung chữ dài vào khung hẹp của Flatsome (vẫn sửa được trong UX Builder)
POLICY_WRAP = ('[section padding="30px" padding__sm="15px"][row][col span="10" span__sm="12" '
               'span__md="12"]\n{body}\n[/col][/row][/section]')


# ---------------------------------------------------------------- .env
def load_env(path):
    p = Path(path).expanduser()
    if not p.exists():
        sys.exit(f"Không thấy file {p}. Copy .env.example thành .env rồi điền.")
    env = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        env[k.strip()] = v
    for k in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"):
        if not env.get(k) or "xxxx" in env[k] or "tenmiencuakhach" in env[k]:
            sys.exit(f"Thiếu hoặc chưa điền {k} trong {p}")
    env["WP_URL"] = env["WP_URL"].rstrip("/")
    return env


def biz_vars(env):
    v = {k[4:].lower(): val for k, val in env.items() if k.startswith("BIZ_") and val}
    v.setdefault("website", env["WP_URL"])
    v["cap_nhat"] = datetime.date.today().strftime("%d/%m/%Y")
    return v


# ---------------------------------------------------------------- render
def render(tpl_file, vars_, missing):
    text = (TPL_DIR / tpl_file).read_text(encoding="utf-8")

    def sub(m):
        key = m.group(1)
        if key in vars_:
            return vars_[key]
        if key in OPTIONAL:
            return ""
        missing.add(key)
        return f"<mark>[CẦN ĐIỀN: {key}]</mark>"
    return re.sub(r"\{\{(\w+)\}\}", sub, text)


def build_content(slug, group, tpl_file, vars_, missing):
    body = render(tpl_file, vars_, missing)
    # mẫu "info" đã có sẵn shortcode UX Builder; mẫu "policy" là HTML thuần
    return POLICY_WRAP.format(body=body) if group == "policy" else body


# ---------------------------------------------------------------- REST
class WP:
    def __init__(self, env):
        self.base = env["WP_URL"]
        tok = base64.b64encode(f"{env['WP_USER']}:{env['WP_APP_PASSWORD']}".encode()).decode()
        self.headers = {"Authorization": f"Basic {tok}", "Accept": "application/json",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (wp-trang-chinh-sach skill)"}
        self.ctx = None
        if env.get("WP_VERIFY_SSL", "1") == "0":
            self.ctx = ssl._create_unverified_context()
        self.query_mode = False

    def url(self, route, params=None):
        qs = urllib.parse.urlencode(params or {})
        if self.query_mode:
            return f"{self.base}/?rest_route=/{route}" + (f"&{qs}" if qs else "")
        return f"{self.base}/wp-json/{route}" + (f"?{qs}" if qs else "")

    def call(self, method, route, data=None, params=None):
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(self.url(route, params), data=body, method=method,
                                     headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=40, context=self.ctx) as r:
                return json.loads(r.read().decode() or "null")
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            raise RuntimeError(f"{method} {route} → HTTP {e.code}: {detail}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Không kết nối được {self.base}: {e.reason}")

    def connect(self):
        try:
            return self.call("GET", "")
        except RuntimeError as e:
            if "404" in str(e):
                self.query_mode = True       # permalink "Cơ bản"
                return self.call("GET", "")
            raise


# ---------------------------------------------------------------- SSH / WP-CLI
def cli_available(env):
    return bool(env.get("SSH_HOST") or env.get("WP_PATH"))


def wp_cli(env, args):
    """Chạy WP-CLI trên VPS qua SSH, hoặc cục bộ nếu không có SSH_HOST. Trả (ok, output)."""
    wp = env.get("WP_CLI", "wp")
    path = env.get("WP_PATH", ".")
    root = " --allow-root" if env.get("SSH_USER") == "root" else ""
    remote = f"cd {shlex.quote(path)} && {wp} {args}{root}"
    if env.get("SSH_HOST"):
        cmd = ["ssh", "-p", env.get("SSH_PORT", "22"), "-o", "BatchMode=yes",
               "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new"]
        if env.get("SSH_KEY"):
            cmd += ["-i", str(Path(env["SSH_KEY"]).expanduser())]
        cmd += [f"{env.get('SSH_USER', 'root')}@{env['SSH_HOST']}", remote]
    else:
        cmd = ["bash", "-lc", remote]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


# ---------------------------------------------------------------- commands
def cmd_check(env, a):
    wp = WP(env)
    info = wp.connect()
    print(f"✓ Site: {info.get('name')} — REST OK")
    ns = info.get("namespaces", [])
    print(f"  WooCommerce: {'có' if 'wc/v3' in ns else 'KHÔNG thấy'}")
    try:
        me = wp.call("GET", "wp/v2/users/me", params={"context": "edit"})
        caps = me.get("capabilities", {})
        print(f"✓ Đăng nhập: {me.get('name')} — quyền sửa trang: "
              f"{'có' if caps.get('edit_pages') else 'KHÔNG'}, menu: "
              f"{'có' if caps.get('edit_theme_options') else 'KHÔNG'}")
    except RuntimeError as e:
        sys.exit(f"✗ Xác thực lỗi: {e}\n  Nếu 401: host có thể chặn header Authorization "
                 f"(xem mục Sự cố trong SKILL.md).")
    try:
        th = [t for t in wp.call("GET", "wp/v2/themes", params={"status": "active"})]
        t = th[0] if th else {}
        name = (t.get("name") or {}).get("raw") or t.get("stylesheet")
        flat = "flatsome" in (t.get("stylesheet", "") + str(t.get("template", ""))).lower()
        print(f"  Theme đang chạy: {name}{'  ✓ Flatsome' if flat else '  ⚠ không phải Flatsome'}")
    except RuntimeError as e:
        print(f"  (không đọc được theme: {e})")
    try:
        locs = wp.call("GET", "wp/v2/menu-locations")
        print("  Vị trí menu:", ", ".join(f"{k}→{v.get('menu') or '-'}" for k, v in locs.items()))
    except RuntimeError:
        print("  (không đọc được vị trí menu)")
    if cli_available(env):
        ok, out = wp_cli(env, "core version")
        print(f"{'✓' if ok else '✗'} WP-CLI/SSH: {out[:200]}")
    else:
        print("  SSH/WP-CLI: chưa cấu hình → bước gán Trang bảo mật phải làm tay")


def cmd_build(env, a):
    v, missing = biz_vars(env), set()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for slug, title, f, group in select(a):
        (out / f"{slug}.html").write_text(build_content(slug, group, f, v, missing), encoding="utf-8")
    print(f"Đã dựng {len(select(a))} trang vào {out}/")
    report_missing(missing)


def report_missing(missing):
    if missing:
        print("⚠ Biến còn thiếu:", ", ".join(f"BIZ_{m.upper()}" for m in sorted(missing)))
    else:
        print("✓ Không còn biến thiếu")


def select(a):
    if a.only:
        want = set(a.only.split(","))
        return [p for p in PAGES if p[0] in want]
    return PAGES


def cmd_push(env, a):
    v, missing = biz_vars(env), set()
    pages = select(a)
    built = {s: build_content(s, g, f, v, missing) for s, t, f, g in pages}
    report_missing(missing)
    status = "publish" if a.publish else "draft"
    if a.publish and missing and not a.allow_missing:
        sys.exit("✗ Còn biến thiếu — không đăng công khai. Điền đủ .env hoặc dùng --allow-missing.")
    if a.dry_run:
        for s, t, f, g in pages:
            print(f"[dry-run] {s}: {len(built[s])} ký tự → {status}")
        return
    wp = WP(env)
    wp.connect()
    ids = {}
    for slug, title, f, group in pages:
        found = wp.call("GET", "wp/v2/pages", params={"slug": slug, "status": "any", "context": "edit"})
        payload = {"title": title, "slug": slug, "content": built[slug]}
        if found:
            pid = found[0]["id"]
            if a.no_overwrite:
                print(f"= {slug}: đã có (#{pid}), bỏ qua"); ids[slug] = pid; continue
            if not a.publish and found[0]["status"] == "publish":
                payload["status"] = "publish"      # không hạ trang đang đăng về nháp
            else:
                payload["status"] = status
            r = wp.call("POST", f"wp/v2/pages/{pid}", payload)
            print(f"~ {slug}: cập nhật #{pid} ({r['status']})")
        else:
            payload["status"] = status
            r = wp.call("POST", "wp/v2/pages", payload)
            print(f"+ {slug}: tạo mới #{r['id']} ({r['status']})")
        ids[slug] = r["id"]
        print(f"   {r.get('link')}")
    if not a.no_menu:
        setup_menu(wp, env, pages, ids, a)
    if not a.no_settings:
        setup_settings(env, ids)
    if status == "draft":
        print("\nĐang là BẢN NHÁP. Xem lại rồi chạy lại với --publish để đăng.")


def setup_menu(wp, env, pages, ids, a):
    name, loc = env.get("MENU_NAME", "Chính sách"), env.get("FOOTER_MENU_LOCATION", "footer")
    try:
        menus = wp.call("GET", "wp/v2/menus", params={"per_page": 100, "context": "edit"})
        menu = next((m for m in menus if m["name"] == name), None)
        if not menu:
            menu = wp.call("POST", "wp/v2/menus", {"name": name})
            print(f"+ menu \"{name}\" #{menu['id']}")
        items = wp.call("GET", "wp/v2/menu-items", params={"menus": menu["id"], "per_page": 100})
        have = {i.get("object_id") for i in items}
        order = len(items)
        for slug, title, f, group in pages:
            if group != "policy" or ids.get(slug) in have:
                continue
            order += 1
            wp.call("POST", "wp/v2/menu-items", {
                "title": title, "status": "publish", "type": "post_type", "object": "page",
                "object_id": ids[slug], "menus": menu["id"], "menu_order": order})
            print(f"  + menu: {title}")
        locs = wp.call("GET", "wp/v2/menu-locations")
        if loc not in locs:
            print(f"⚠ Không có vị trí '{loc}'. Có: {', '.join(locs)}. Gán menu thủ công "
                  f"(Giao diện → Menu) hoặc sửa FOOTER_MENU_LOCATION.")
            return
        cur = locs[loc].get("menu")
        if cur in (0, None, menu["id"]):
            wp.call("POST", f"wp/v2/menus/{menu['id']}", {"locations": [loc]})
            print(f"✓ Menu \"{name}\" gán vào vị trí '{loc}'")
        else:
            print(f"⚠ Vị trí '{loc}' đang dùng menu #{cur} khác — KHÔNG ghi đè. "
                  f"Gán tay hoặc dùng widget footer.")
    except RuntimeError as e:
        print(f"⚠ Bước menu lỗi ({e}) — thêm menu tay ở Giao diện → Menu.")


def setup_settings(env, ids):
    if not cli_available(env):
        print("\nLÀM TAY (chưa có SSH/WP-CLI):\n"
              "  • Cài đặt → Riêng tư → chọn trang \"Chính sách bảo mật thông tin\"\n"
              "  • WooCommerce → Cài đặt → Nâng cao → Trang → Điều khoản và điều kiện "
              "→ \"Điều khoản sử dụng\"")
        return
    todo = [(PRIVACY_SLUG, "wp_page_for_privacy_policy"), (TERMS_SLUG, "woocommerce_terms_page_id")]
    for slug, opt in todo:
        if slug in ids:
            ok, out = wp_cli(env, f"option update {opt} {ids[slug]}")
            print(f"{'✓' if ok else '⚠'} {opt} = #{ids[slug]}  {'' if ok else out[:150]}")
    ok, out = wp_cli(env, "cache flush")
    print(f"{'✓' if ok else '·'} cache flush {'' if ok else '(bỏ qua)'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "build", "push"])
    ap.add_argument("--env", default=".env")
    ap.add_argument("--only", help="slug cách nhau dấu phẩy, vd chinh-sach-doi-tra,gioi-thieu")
    ap.add_argument("--out", default="out")
    ap.add_argument("--publish", action="store_true", help="đăng công khai (mặc định: nháp)")
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--no-overwrite", action="store_true")
    ap.add_argument("--no-menu", action="store_true")
    ap.add_argument("--no-settings", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    env = load_env(a.env)
    try:
        {"check": cmd_check, "build": cmd_build, "push": cmd_push}[a.command](env, a)
    except RuntimeError as e:
        sys.exit(f"✗ {e}")


if __name__ == "__main__":
    main()
