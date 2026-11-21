# Panel Elite v1.1 · parte 24: MERCADO con la carga de ahora (v1.1.10d)
#   El sender manda el mercado solo cuando abres el mercado (o cambia), con la carga de ese momento. Si después
#   entregabas o vendías la carga, MERCADO seguía con «TU BODEGA AQUÍ … VENDIENDO TODO» de antes.
#   Ahora las filas se recalculan con la bodega actual; sin carga sale «BODEGA VACÍA · LO MEJOR PAGADO AQUÍ».
def mkt_recuenta(d):
    m = d.get("market")
    if not isinstance(m, dict) or not (m.get("sell") or m.get("sell0")):
        return d
    base = m.get("sell0") or m.get("sell")              # las filas que mandó el sender (con su carga de entonces)
    ahora = {}
    for c in d.get("cargo") or []:
        if len(c) > 1:
            k = str(c[0])[:26]
            ahora[k] = ahora.get(k, 0) + (c[1] or 0)
    filas = []
    for r in base:
        n = ahora.get(str(r[0])[:26], 0)
        if n > 0:
            filas.append([r[0], n] + list(r[2:]))
    filas.sort(key=lambda r: -r[1] * r[2])
    d["market"] = dict(m, sell0=base, sell=filas)
    return d
