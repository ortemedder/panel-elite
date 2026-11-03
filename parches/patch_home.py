import shutil, re, sys
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak5")
s = open(p, encoding="utf-8").read()
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.split("\n")[0]); ok = False; return
    s = s.replace(old, new, 1)

rep('ui = {"view": 0,', 'ui = {"view": 100,')
rep("111: 11, 112: 11, ", "")
rep("PARENT = {", "PARENT = {0: 100, ")
rep('73: "XENOBIOLOGÍA", 111: "SESIÓN", 112: "EN VIVO"}', '73: "XENOBIOLOGÍA", 100: "EN VIVO"}')
rep("11: view_sub11, 111: view_session, 112: view_live,", "11: view_session, 100: view_live,")
rep('    if v and BACK.collidepoint(x, y):\n        ui["view"] = PARENT.get(v, 0)',
    '    if BACK.collidepoint(x, y):\n        ui["view"] = 0 if v == 100 else PARENT.get(v, 0)')
rep('ui["idle_on"] = not online and ui["view"] == 0 and', 'ui["idle_on"] = not online and ui["view"] in (0, 100) and')
rep('put(surf, F["btn"], "< MENÚ", BACK.center', 'put(surf, F["btn"], "MENÚ" if v == 100 else "< INICIO" if v == 0 else "< MENÚ", BACK.center')
s, n = re.subn(r'\n( +)if v:\n(\1 +pygame\.draw\.rect\(surf, ORANGE, BACK)', r'\n\1if True:\n\2', s, count=1)
if not n: print("NO ENCONTRADO: if v: (barra superior)"); ok = False
L = s.split("\n")
try:
    j = next(i for i, l in enumerate(L) if 'ui["view"] = 111 + i' in l)
    k = j
    while not L[k].lstrip().startswith("elif v == 11"):
        k -= 1
    del L[k:j + 1]
except StopIteration:
    print("NO ENCONTRADO: bloque de toque del 11"); ok = False
s = "\n".join(L)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
