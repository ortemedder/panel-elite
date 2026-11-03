import shutil
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak7")
s = open(p, encoding="utf-8").read()
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:60]); ok = False; return
    s = s.replace(old, new, 1)

rep('''    put(surf, F["small"], "MAPEADOS", (W - 8, y), DIM, anchor="topright")''',
'''    put(surf, F["small"], "MAPEADOS", (W - 8, y), DIM, anchor="topright")
    if ex.get("edsm_n"):
        put(surf, F["small"], f"EDSM: {ex['edsm_n']} cuerpos", (150, y), BLUE)''')
rep('''        put(surf, F["btn"], "Nada destacable escaneado aún", (W // 2, y + 60), DIM, anchor="center")''',
'''        msg = "Consultando EDSM..." if ex.get("edsm_st") == "consultando" else "Nada destacable escaneado aún"
        put(surf, F["btn"], msg, (W // 2, y + 60), DIM, anchor="center")''')
rep('''    for name, cls, dist, first, mapped, val in top[:7]:''',
'''    for row in top[:7]:
        name, cls, dist, first, mapped, val = row[:6]
        src = row[6] if len(row) > 6 else None''')
rep('''        put(surf, F["small"], "1º" if first else "", (318, y + 4), GREEN)
        put(surf, F["small"], "MAPEADO" if mapped else "SIN MAPEAR", (342, y + 4), BLUE if mapped else DIM)''',
'''        if src == "edsm":
            put(surf, F["small"], "EDSM", (342, y + 4), BLUE)
        else:
            put(surf, F["small"], "1º" if first else "", (318, y + 4), GREEN)
            put(surf, F["small"], "MAPEADO" if mapped else "SIN MAPEAR", (342, y + 4), BLUE if mapped else DIM)''')
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
