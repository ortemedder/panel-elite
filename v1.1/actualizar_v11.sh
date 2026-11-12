#!/bin/bash
# Actualiza el panel v1.1 con esta version completa (ya no hay cadena de parches).
# Cambia solo el codigo (panel.py, panel_run.py, partes/ y el sonido); tus ajustes y datos de ~/panel-v11 no se tocan.
# Antes guarda una copia del codigo anterior en ~/panel-v11/copias/ por si hay que volver atras.
# Uso: bash actualizar_v11.sh      (desde la carpeta donde descomprimiste el zip)
set -u
ORIG="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/panel-v11"
[ -d "$ORIG/panel-v11/partes" ] || { echo "No encuentro panel-v11/partes junto a este script"; exit 1; }
if [ ! -f "$DEST/panel_run.py" ]; then
    echo "No hay v1.1 instalada en $DEST: la instalo"
    exec bash "$ORIG/instalar_v11.sh"
fi
OLD=$(grep -ho 'PANEL_VER = "[^"]*' "$DEST"/partes/*.py 2>/dev/null | head -1 | cut -d'"' -f2 | cut -d' ' -f1)
NEW=$(grep -ho 'PANEL_VER = "[^"]*' "$ORIG"/panel-v11/partes/*.py | head -1 | cut -d'"' -f2 | cut -d' ' -f1)
mkdir -p "$DEST/copias"
COPIA="$DEST/copias/codigo_${OLD:-anterior}_$(date +%Y%m%d_%H%M).tar.gz"
tar -czf "$COPIA" -C "$DEST" panel.py panel_run.py partes 2>/dev/null && echo "== Copia del codigo ${OLD:-anterior}: $COPIA"
rm -rf "$DEST/partes"
cp -r "$ORIG/panel-v11/partes" "$DEST/"
cp "$ORIG/panel-v11/panel.py" "$ORIG/panel-v11/panel_run.py" "$ORIG/panel-v11/sonido_inicio.wav" "$DEST/"
rm -rf "$DEST/partes/__pycache__" "$DEST/__pycache__"
cp "$ORIG/cambiar_panel.sh" "$HOME/" 2>/dev/null
cp "$ORIG/actualizar_v11.sh" "$ORIG/subir_v11.sh" "$ORIG/prueba_sonido.sh" "$HOME/" 2>/dev/null
echo "== Codigo ${OLD:-?} -> $NEW"
bash "$HOME/cambiar_panel.sh" v11
echo
echo "Si algo va mal, para volver al codigo anterior:"
echo "   rm -rf $DEST/partes && tar -xzf $COPIA -C $DEST && sudo systemctl restart elite-panel"
