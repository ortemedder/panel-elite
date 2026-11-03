import shutil
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak8")
s = open(p, encoding="utf-8").read()
old = "    for row in top[:7]:"
if old not in s:
    print("NO ENCONTRADO: bucle de cuerpos"); raise SystemExit
s = s.replace(old, '''    per = 7
    pages = max(1, (len(top) + per - 1) // per)
    pg = ui.get("page71", 0) % pages
    if pages > 1:
        put(surf, F["small"], f"pág {pg + 1}/{pages}  (toca para pasar)", (W // 2, H - 34), DIM, anchor="center")
    for row in top[pg * per:(pg + 1) * per]:''', 1)
L = s.split("\n")
j = next((i for i, l in enumerate(L) if l.strip() == "elif v == 72:"), None)
if j is None:
    print("NO ENCONTRADO: toque del 72"); raise SystemExit
ind = L[j][:len(L[j]) - len(L[j].lstrip())]
L[j:j] = [ind + "elif v == 71:", ind + "    ui['page71'] = ui.get('page71', 0) + 1; return"]
open(p, "w", encoding="utf-8").write("\n".join(L))
print("OK")
