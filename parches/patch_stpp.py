import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak39")
s = open(p, encoding="utf-8").read()
old = '''        if now - stdock["t"] >= 15:
            return view_station_info(surf, d, st)'''
if "stpp" in s:
    print("ya estaba"); raise SystemExit
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace(old, '''        if now - stdock["t"] >= 15:
            S = (d or {}).get("sysinfo") or {}
            stpp = S.get("pp") or S.get("pp_conf") or S.get("powers")
            if stpp and (now - stdock["t"] - 15) % 15 >= 10:
                return view_pp(surf, d, flags, now)
            return view_station_info(surf, d, st)''', 1)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.39 · 29/10/2026 11:15"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
