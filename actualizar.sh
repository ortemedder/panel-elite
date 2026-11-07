#!/bin/bash
# Actualiza el panel: mira su version y aplica en orden los parches que falten (estan en la misma carpeta
# que este script o en tu carpeta personal). Cada parche guarda su copia de seguridad (panel.py.bakXX).
# Uso:   bash ~/actualizar.sh
DIR="$(cd "$(dirname "$0")" && pwd)"
PANEL="$HOME/panel.py"
# version de partida -> parche que la lleva a la siguiente
CADENA="v0.99k:patch_v100b1.py"
ver() { grep -m1 -o 'PANEL_VER = "v[^ "]*' "$PANEL" | cut -d'"' -f2; }
[ -f "$PANEL" ] || { echo "No encuentro $PANEL"; exit 1; }
echo "Panel en $(ver)"
hecho=0
while :; do
    v=$(ver); p=""
    for par in $CADENA; do [ "${par%%:*}" = "$v" ] && p="${par#*:}"; done
    [ -z "$p" ] && break
    f=""; for c in "$DIR/$p" "$HOME/$p"; do [ -f "$c" ] && f="$c" && break; done
    if [ -z "$f" ]; then echo "Falta el parche $p (para pasar de $v). Copialo junto a este script."; break; fi
    echo "== $v -> $p"
    python3 "$f" "$PANEL" || { echo "El parche $p ha fallado: no sigo."; exit 1; }
    hecho=1
done
if [ $hecho = 1 ]; then
    sudo systemctl restart elite-panel && echo "Panel reiniciado en $(ver)"
else
    echo "Nada que actualizar ($(ver))"
fi
