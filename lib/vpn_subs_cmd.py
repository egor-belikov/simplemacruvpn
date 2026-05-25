#!/usr/bin/env python3
from __future__ import annotations

"""vpn subs — хранит URL подписок в $VPN_SUBSCRIPTIONS_FILE, preview/init/add/rm."""

import base64
import binascii
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from urllib import error as urlerr
from urllib import parse as urlparse
from urllib import request as urlrequest

CFG = Path(os.environ.get("VPN_SUBSCRIPTIONS_FILE") or "").expanduser()
MIHOMO_DIR = Path(os.environ.get("MIHOMO_DIR") or "").expanduser()
FLAGPAIR = re.compile("[\U0001f1e6-\U0001f1ff]{2}")

URI_PREFIXES = (
    "vless:", "vmess:", "trojan:", "ss:", "socks:",
    "socks5:", "tuic:", "hy2:", "hysteria2:", "hysteria:",
)


def av() -> list[str]:
    a = sys.argv[1:]
    if a and a[0] == "-":
        return a[1:]
    return a


def hdr_lines() -> list[str]:
    return [
        "# URLs подписок Mihomo/V2Ray (HTTPS), одна строка — один адрес.",
        "# init из config.yaml:  vpn subs init",
        "# добавить:              vpn subs add 'https://...'",
        "",
    ]


def mask(url: str) -> str:
    return url if len(url) <= 54 else url[:38] + "\u2026" + url[-12:]


def yaml_names(text: str) -> list[str]:
    out = []
    for m in re.finditer(
        r"^[\t ]*-\t*name:[\t ]*(?:\"([^\"]+)\"|'([^']+)'|([^\t #][^#\n]*))",
        text,
        re.MULTILINE,
    ):
        n = next((x for x in m.groups() if x), "").strip().strip("\"' ")
        if n:
            out.append(n)
    return out


def b64_subscription(raw_bytes: bytes) -> list[str] | None:
    blob = raw_bytes.replace(b"\r", b"").replace(b"\n", b"").strip()
    if not blob:
        return None
    for strict in (True, False):
        try:
            d = base64.b64decode(blob, validate=strict)
        except binascii.Error:
            continue
        t = d.decode("utf-8", "replace").strip("\ufeff ")
        ys = yaml_names(t)
        if ys:
            return ys
        lines = [ln.strip() for ln in t.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if lines:
            return lines
    return None


def parse_body(raw_bytes: bytes) -> tuple[list[str], str]:
    ys = yaml_names(raw_bytes.decode("utf-8", "replace"))
    if ys:
        return ys, "yaml"
    ku = b64_subscription(raw_bytes)
    if ku is not None:
        return ku, "subscription"
    t = raw_bytes.decode("utf-8", "replace").strip("\ufeff ")
    lines = [
        ln.strip()
        for ln in t.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if lines:
        return lines, "lines"
    try:
        j = json.loads(t.encode())
        if isinstance(j, list):
            nm = [
                str(it.get("name") or it.get("remark") or "")
                for it in j
                if isinstance(it, dict)
            ]
            nm = [x for x in nm if x]
            if nm:
                return nm, "json"
    except json.JSONDecodeError:
        pass
    return [], "unknown"


def vmess_comment(line: str) -> str | None:
    ll = line.lower()
    if not ll.startswith("vmess:"):
        return None
    rest = line[6:]
    frag = ""
    if "#" in rest:
        rest, hf = rest.split("#", 1)
        frag = urlparse.unquote(hf)
    pad = "=" * (-len(rest) % 4)
    try:
        js = json.loads(
            base64.b64decode(rest + pad, validate=False).decode("utf-8", "replace")
        )
        return frag or js.get("ps") or js.get("remark") or ""
    except Exception:
        return frag or None


def label_from_uri(raw: str) -> str | None:
    ln = raw.strip().strip("\"' ").replace("\ufeff", "")
    lw = ln.lower()
    if not any(lw.startswith(p) for p in URI_PREFIXES):
        return ln if len(ln) < 380 and "\n" not in ln else None
    if lw.startswith("vmess:"):
        r = vmess_comment(ln)
        if r:
            return str(r)
    pr = urlparse.urlparse(ln)
    if pr.fragment:
        return urlparse.unquote(pr.fragment)
    for k, v in urlparse.parse_qsl(pr.query, keep_blank_values=True):
        kk = k.lower()
        if kk in ("remarks", "remark", "name") and v:
            return urlparse.unquote(v)
    cut = ln if len(ln) <= 240 else ln[:240] + "\u2026"
    return cut


def uniq_labels(entries: list[str]) -> list[str]:
    o = []
    for e in entries:
        lbl = label_from_uri(e)
        if lbl:
            o.append(lbl)
    return list(dict.fromkeys(o))


def uniq_flags(ll: list[str]) -> list[str]:
    xs = []
    for s in ll:
        m = FLAGPAIR.search(s)
        if m and m.group(0) not in xs:
            xs.append(m.group(0))
    return xs


def scrape_config_urls(path: Path) -> list[str]:
    if not path.is_file():
        return []
    txt = path.read_text(encoding="utf-8", errors="replace")
    urls: list[str] = []
    for m in re.finditer(r'^\s*url:\s*["\'](https?://[^"\']+)["\']?', txt, re.MULTILINE):
        token = m.group(1).strip()
        low = token.lower()
        if "meta-rules-dat" in low:
            continue
        if "/sub/" not in token and "subscription" not in low:
            continue
        if token and token not in urls:
            urls.append(token)
    return urls


def read_urls_from_file() -> list[str]:
    if not CFG or not CFG.is_file():
        return []
    xs = []
    for ln in CFG.read_text(encoding="utf-8", errors="replace").splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            xs.append(s.split("|", 1)[-1].strip())
    return xs


def save_urls(us: list[str]) -> None:
    if not CFG:
        print("\u0424\u0430\u0439\u043b \u043f\u0443\u0441\u0442 (VPN_SUBSCRIPTIONS_FILE)", file=sys.stderr)
        sys.exit(1)
    CFG.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="subs-", dir=str(CFG.parent))
    tmppath = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as w:
            for h in hdr_lines():
                if h.strip():
                    w.write(h.rstrip("\n") + "\n")
            for x in us:
                w.write(x.strip() + "\n")
            w.write("")
        shutil.move(str(tmppath), CFG)
        CFG.chmod(0o600)
    finally:
        if tmppath.is_file():
            try:
                tmppath.unlink()
            except OSError:
                pass


def fetch_url(u: str) -> bytes:
    req = urlrequest.Request(
        u,
        headers={"User-Agent": "Clash-Verge/meta (subs preview)"},
    )
    with urlrequest.urlopen(req, timeout=120) as r:
        return r.read()


def do_list():
    bar = "=" * 42
    if not CFG:
        print(bar)
        print(" VPN_SUBSCRIPTIONS_FILE\n")
        sys.exit(1)
    xs = read_urls_from_file()
    print(bar)
    print(" vpn subs \u2192", str(CFG))
    print(bar)
    if xs:
        for i, x in enumerate(xs, start=1):
            print(f"  {i:2}  {mask(x)}")
    else:
        print(
            " (\u041f\u0443\u0441\u0442\u043e)  vpn subs init  \u0438\u043b\u0438  vpn subs add '<url>'"
        )
    print(bar)
    print("  vpn subs preview  \u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u0443\u0437\u043b\u044b \u0441 \u0441\u0435\u0440\u0432\u0435\u0440\u0430")


def do_path():
    print(str(CFG) if CFG else "")


def do_init():
    if not CFG or not MIHOMO_DIR:
        sys.exit(1)
    scraped = scrape_config_urls(MIHOMO_DIR / "config.yaml")
    cur = read_urls_from_file()
    merged = list(dict.fromkeys(cur + scraped))
    save_urls(merged)
    print("[subs] saved", len(merged), "URLs", "\u2192", CFG)


def do_add(parts: list[str]):
    raw = "".join(parts).strip() if parts else ""
    if not raw:
        print("\u0423\u043a\u0430\u0436\u0438: vpn subs add 'https://...'", file=sys.stderr)
        sys.exit(1)
    u = urlparse.urlsplit(raw)
    if u.scheme not in ("http", "https"):
        print("\u041d\u0443\u0436\u0435\u043d https:// \u0441\u0441\u044b\u043b\u043a\u0430", file=sys.stderr)
        sys.exit(1)
    cur = read_urls_from_file()
    if raw in cur:
        print("[subs] \u0443\u0436\u0435 \u0435\u0441\u0442\u044c")
        return
    cur.append(raw)
    save_urls(cur)
    print("[subs] +\u2192", mask(raw))


def do_rm(which: str):
    try:
        n = int(which)
    except ValueError:
        print("\u041e\u0448\u0438\u0431\u043a\u0430 \u0438\u043d\u0434\u0435\u043a\u0441\u0430", file=sys.stderr)
        sys.exit(1)
    cur = read_urls_from_file()
    if n < 1 or n > len(cur):
        print("\u041d\u0435\u0442 URL \u043d\u043e\u043c\u0435\u0440", n, file=sys.stderr)
        sys.exit(1)
    rm = cur.pop(n - 1)
    save_urls(cur)
    print("[subs] \u0423\u0434\u0430\u043b\u0435\u043d", n, ":", mask(rm))


def do_preview():
    xs = read_urls_from_file()
    if not xs:
        print("[subs] \u0441\u043f\u0438\u0441\u043e\u043a \u043f\u0443\u0441\u0442. \u0421\u043d\u0430\u0447\u0430\u043b\u0430: vpn subs init")
        sys.exit(0)
    B = "=" * 42
    for i, u in enumerate(xs, start=1):
        print(B)
        print(f" [{i}] {mask(u)}")
        print(B)
        try:
            blob = fetch_url(u)
        except urlerr.URLError as e:
            print(" \u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438:", e)
            continue
        lines, fmt = parse_body(blob)
        lbls = uniq_labels(lines) if lines else []
        fg = uniq_flags(lbls)
        print(f" raw: {fmt} | \u0437\u0430\u043f\u0438\u0441\u0435\u0439: {len(lines)} | \u0438\u043c\u0451\u043d: {len(lbls)}")
        if fg:
            print(" \u0444\u043b\u0430\u0433\u0438 \u0443 \u0443\u0437\u043b\u043e\u0432:", " ".join(fg))
        for name in lbls[:40]:
            print(" ", name)
        if len(lbls) > 40:
            print(" ... +" + str(len(lbls) - 40) + " \u0435\u0449\u0451")


def usage():
    print(
        dedent(
            """\
        vpn subs [list]
        vpn subs path
        vpn subs init   — добавить URLs из MIHOMO_DIR/config.yaml
        vpn subs preview  — узлы со всех подписок в файле (нужен интернет)
        vpn subs add '<https://...>'
        vpn subs rm <n> — удалить строку номером n из list
            """
        )
    )


def main():
    xs = av()
    if not xs:
        xs = ["list"]
    cmd = xs[0]
    tail = xs[1:]

    if cmd in ("help", "-h", "--help"):
        usage()
        return
    if cmd in ("ls", "l", "list"):
        do_list()
    elif cmd == "path":
        do_path()
    elif cmd in ("init", "seed"):
        do_init()
    elif cmd in ("preview", "fetch", "pull"):
        do_preview()
    elif cmd == "add":
        do_add(tail)
    elif cmd in ("rm", "del", "remove"):
        if not tail:
            print("\u0423\u043a\u0430\u0436\u0438 \u043d\u043e\u043c\u0435\u0440: vpn subs rm 1", file=sys.stderr)
            sys.exit(1)
        do_rm(tail[0])
    else:
        print("\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430\u044f \u043f\u043e\u0434\u043a\u043e\u043c\u0430\u043d\u0434\u0430:", cmd)
        usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
