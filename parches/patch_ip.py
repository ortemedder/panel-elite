import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak47")
s = open(p, encoding="utf-8").read()
if "def my_ip" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''IPC = {"ip": None, "t": 0}

def my_ip():
    import socket
    if time.time() - IPC["t"] > 30:
        IPC["t"] = time.time()
        try:
            sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sk.connect(("192.168.0.1", 9))
            IPC["ip"] = sk.getsockname()[0]
            sk.close()
        except OSError:
            IPC["ip"] = None
    return IPC["ip"]

'''
rep("def draw_idle(", SNIP + "def draw_idle(")
old = '    put(surf, F["small"], PANEL_VER, (290, 270), GREEN, anchor="center")\n'
rep(old, old + '    ip = my_ip()\n    put(surf, F["small"], f"IP {ip}" if ip else "SIN RED", (290, 286), DIM if ip else RED, anchor="center")\n')
rep("\n]\n\ndef view_changelog", '\n    ("0.47", "IP de la Pi en la pantalla del reloj"),\n]\n\ndef view_changelog')
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.47 · 29/10/2026 13:50"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
