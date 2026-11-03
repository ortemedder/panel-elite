import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak22")
s = open(p, encoding="utf-8").read()
old = '(("SRV", W // 4, in_srv), ("A PIE", 3 * W // 4, on_foot))'
new = '((("RHINO" if "rhino" in ((d or {}).get("srvtype") or "").lower() else "SRV"), W // 4, in_srv), ("A PIE", 3 * W // 4, on_foot))'
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace(old, new, 1)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.22 · 29/10/2026 00:30"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
