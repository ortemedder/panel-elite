#!/usr/bin/env python3
# Sender v1.0 beta 20 (desde la beta 19), para el panel v2.2b5:
# - DATOS VENDIDOS: al vender exploración manda los sistemas vendidos, lo cobrado y lo que valía cada sistema (según
#   lo escaneado con el sender encendido; el juego solo da el total).
# - VENTA EN EL MERCADO: toneladas, producto, total cobrado y beneficio (TotalSale - precio medio pagado).
# - HORA en cada derribo del registro de combate.
# Uso:  python patch_sender_v100b20.py elite_sender.py   (deja una copia elite_sender.py.bak100b19)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
s = open(P, encoding="utf-8").read()
if 'SENDER_VER = "v1.0b20"' in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b19"' not in s:
    sys.exit("Este parche es para el sender v1.0b19 (aplica antes patch_sender_v100b19.py)")
shutil.copy(P, P + ".bak100b19")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('SENDER_VER = "v1.0b19"', 'SENDER_VER = "v1.0b20"')
rep('''        systems = e.get("Systems") or [d.get("SystemName", "") for d in e.get("Discovered") or []]
        for sysname in systems:
            for k in [k for k in unsold if k.startswith(sysname)]:
                unsold.pop(k)''', '''        systems = e.get("Systems") or [d.get("SystemName", "") for d in e.get("Discovered") or []]
        vend = []
        for sysname in systems:
            v_ = 0
            for k in [k for k in unsold if k.startswith(sysname)]:
                v_ += unsold.pop(k) or 0
            vend.append(f"{sysname.replace('|', ' ').replace(';', ' ')}:{int(v_)}")
        if LIVE[0] and systems:                             # v1.0b20: DATOS VENDIDOS
            note("datavend", f"{len(systems)}|{int(e.get('TotalEarnings', 0))}|{int(e.get('Bonus', 0))}|" + ";".join(vend[:40]))''')
rep('''        combat["kills"].insert(0, [tgt[:28], rew, kind])''',
    '''        combat["kills"].insert(0, [tgt[:28], rew, kind, int(iso2epoch(e.get("timestamp")) or time.time())])''')
rep('''    elif ev == "MarketSell" and LIVE[0]:
        note("mktsell",''', '''    elif ev == "MarketSell" and LIVE[0]:
        n_, tot_ = e.get("Count", 0), e.get("TotalSale", 0)
        note("venta", f"{n_}|{(e.get('Type_Localised') or e.get('Type') or '').replace('|', ' ')}|{tot_}|"
                      f"{tot_ - (e.get('AvgPricePaid') or 0) * n_}|{e.get('AvgPricePaid') or 0}")   # v1.0b20
        note("mktsell",''')
open(P, "w", encoding="utf-8").write(s)
print("Sender actualizado a v1.0b20")
