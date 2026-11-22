#!/usr/bin/env python3
# Sender v1.0 beta 18 (desde la beta 17), para el panel v2.1:
# - AUTODESCUBRIMIENTO: el panel (la Pi) se anuncia en la red cada 5 s (UDP 5007) y el sender lo encuentra solo.
#   PI_IP = "AUTO" (o vacío): usa el primer panel que oye (si hay varios, el de tu mismo comandante).
#   PI_IP = "192.168.x.y": se sigue usando esa IP; solo si esa Pi lleva 60 s sin anunciarse y otra sí, se cambia a la otra
#   (la Pi cambió de IP).
# - objetivo fijado: nombre interno del subsistema («subraw»), para que el botón NÚCLEO del panel lo reconozca en
#   cualquier idioma.
# Uso:  python patch_sender_v100b18.py elite_sender.py   (deja una copia elite_sender.py.bak100b17)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if 'SENDER_VER = "v1.0b18"' in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b17"' not in s:
    sys.exit("Este parche es para el sender v1.0b17")
shutil.copy(P, P + ".bak100b17")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('SENDER_VER = "v1.0b17"', 'SENDER_VER = "v1.0b18"')
rep('''"subsys": e.get("Subsystem_Localised"), "subhealth": e.get("SubsystemHealth"), "t": time.time(),''',
    '''"subsys": e.get("Subsystem_Localised"), "subhealth": e.get("SubsystemHealth"), "t": time.time(),
                      "subraw": (e.get("Subsystem") or "").lower(),''')
rep('''def send(obj):
    out = obj''', '''def send(obj):
    if not PI_IP:
        return                                               # v1.0b18: aún no se ha encontrado el panel
    out = obj''')
rep('''_v096_load()
print("Sender", SENDER_VER)''', '''_v096_load()

# ---- v1.0b18: autodescubrimiento del panel (la Pi se anuncia por UDP 5007) ----
HOLA_PORT = 5007
PI_AUTO = PI_IP.strip().upper() in ("", "AUTO")
if PI_AUTO:
    PI_IP = ""
PANELES = {}                                                 # ip -> (hora, versión, cmdr)

def hola_loop():
    global PI_IP
    try:
        so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        so.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        so.bind(("0.0.0.0", HOLA_PORT))
    except OSError as e:
        print("Autodescubrimiento no disponible:", e, flush=True)
        return
    while True:
        try:
            data, addr = so.recvfrom(256)
        except OSError:
            continue
        if not data.startswith(b"ELITEPANEL-HOLA|"):
            continue
        ver, cmdr = (data[16:].decode("utf-8", "ignore").split("|") + ["", ""])[:2]
        ip, now = addr[0], time.time()
        PANELES[ip] = (now, ver, cmdr)
        if ip == PI_IP:
            continue
        cur = PANELES.get(PI_IP)
        if PI_IP and ((cur is None and not PI_AUTO) or (cur and now - cur[0] < 60)):
            continue                                         # el panel de siempre sigue ahí (o es una IP fija sin aviso)
        mio = (ranks.get("cmdr") or "").lower()
        if mio and cmdr.lower() != mio and any(c.lower() == mio and now - t < 60 for t, _, c in PANELES.values()):
            continue                                         # hay otro panel de tu comandante: ese manda
        antes = PI_IP
        PI_IP = ip
        print(time.strftime("%H:%M:%S"), "PANEL ENCONTRADO en", ip, ver, cmdr,
              f"(antes {antes})" if antes else "", flush=True)

threading.Thread(target=hola_loop, daemon=True).start()
print("Sender", SENDER_VER)''')
rep('''print("Enviando a", PI_IP, PORT)''',
    '''print("Enviando a", PI_IP or "(buscando el panel en la red...)", PORT)''')
open(P, "w", encoding="utf-8").write(s)
print("Sender actualizado a v1.0b18. Puedes poner PI_IP = 'AUTO' arriba del todo para que busque el panel solo.")
