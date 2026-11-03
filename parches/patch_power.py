import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak36")
s = open(p, encoding="utf-8").read()
if "def view_sub124" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- 12.4 ajustes: salir, reiniciar, apagar, preferencias ----------
POWER = [("1", "SALIR"), ("2", "REINICIAR"), ("3", "APAGAR"), ("4", "PREFERENCIAS")]

def view_sub124(surf, d, flags, now):
    c, until = ui["confirm"]
    for i, (n, name) in enumerate(POWER):
        sure = c == ("pw", i) and time.time() < until
        draw_button(surf, grid(i, 2, 2), n, "¿SEGURO?" if sure else name, F["num"], filled=sure,
                    lit=flash.get((1240, i), 0) > now)

def power_tap(i):
    import subprocess
    if i == 3:
        ui["view"] = 1244; return
    c, until = ui["confirm"]
    if c != ("pw", i) or time.time() > until:
        ui["confirm"] = (("pw", i), time.time() + 3); return
    ui["confirm"] = (None, 0)
    tap_flash((1240, i))
    cmd = [["systemctl", "stop", "elite-panel"], ["systemctl", "reboot"], ["systemctl", "poweroff"]][i]
    subprocess.Popen(["sudo", "-n"] + cmd)

'''
rep("def view_sub12", SNIP + "def view_sub12")
rep("124: view_settings", "124: view_sub124, 1244: view_settings")
rep("124: 12}", "124: 12, 1244: 124}") if "124: 12}" in s else rep("124: 12,", "124: 12, 1244: 124,")
rep('127: "MERCADO"', '127: "MERCADO", 1244: "PREFERENCIAS"')
L = s.split("\n")
old = [i for i, l in enumerate(L) if re.match(r"\s*elif v == 124\s*:", l)]
if old:
    L[old[0]] = L[old[0]].replace("v == 124", "v == 1244")
    print("toque de preferencias movido al 1244 (línea", old[0] + 1, ")")
else:
    print("AVISO: no encontré 'elif v == 124:'")
    for i, l in enumerate(L):
        if "124" in l and ("v ==" in l or "view" in l):
            print("  ", i + 1, l.strip()[:90])
t = next((i for i, l in enumerate(L) if l.strip() == "elif v == 71:"), None)
if t is None:
    print("NO ENCONTRADO: toque"); ok = False
else:
    ind = L[t][:len(L[t]) - len(L[t].lstrip())]
    L[t:t] = [ind + "elif v == 124:", ind + "    for i in range(4):",
              ind + "        if grid(i, 2, 2).collidepoint(x, y):", ind + "            power_tap(i); return"]
s = "\n".join(L)
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.36 · 29/10/2026 03:00"', s, count=1)
if ok and old:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada: pégame lo de arriba")
