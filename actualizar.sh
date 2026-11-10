#!/bin/bash
# Actualiza el panel: mira su version y aplica en orden los parches que falten (estan en la misma carpeta
# que este script o en tu carpeta personal). Cada parche guarda su copia de seguridad (panel.py.bakXX).
# Uso:   bash ~/actualizar.sh
DIR="$(cd "$(dirname "$0")" && pwd)"
PANEL="$HOME/panel.py"
# version de partida -> parche que la lleva a la siguiente
CADENA="v0.99f:patch_v099g.py v0.99g:patch_v099h_korzo.py v0.99i:patch_v099j.py v0.99j:patch_v099k.py v0.99k:patch_v100b1.py v1.0b1:patch_v100b2.py v1.0b2:patch_v100b3.py v1.0b3:patch_v100b4.py v1.0b4:patch_v100b5.py v1.0b5:patch_v100b6.py v1.0b6:patch_v100b6b.py v1.0b6b:patch_v100b7.py v1.0b7:patch_v100b8.py v1.0b8:patch_v100b9.py v1.0b9:patch_v100b10.py v1.0b10:patch_v100b10b.py v1.0b10b:patch_v100b10c.py v1.0b10c:patch_v100b11.py v1.0b11:patch_v100b12.py v1.0b12:patch_v100b12b.py v1.0b12b:patch_v100b12c.py v1.0b12c:patch_v100b13.py v1.0b13:patch_v100b14.py v1.0b14:patch_v100b15.py v1.0b15:patch_v100b16.py v1.0b16:patch_v100b16b.py v1.0b16b:patch_v100b17.py v1.0b17:patch_v100b17b.py v1.0b17b:patch_v100b18.py v1.0b18:patch_v100b19.py v1.0b19:patch_v100b19b.py v1.0b19b:patch_v100b20.py"
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
