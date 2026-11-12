#!/bin/bash
# Instala el panel v1.1 en ~/panel-v11 (la b20 de tu carpeta personal no se toca).
# Copia (no mueve) tus ajustes y datos de la b20 para que la v1.1 arranque igual que la tuya.
# Uso: bash instalar_v11.sh      (desde la carpeta donde descomprimiste el zip)
set -u
ORIG="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/panel-v11"
[ -d "$ORIG/panel-v11/partes" ] || { echo "No encuentro panel-v11/partes junto a este script"; exit 1; }
mkdir -p "$DEST"
cp -r "$ORIG/panel-v11/." "$DEST/"
echo "== Codigo v1.1 copiado a $DEST"
n=0
for f in "$HOME"/*.json "$HOME"/*.txt "$HOME"/*.jpg "$HOME"/*.png "$HOME"/*.wav "$HOME"/*.ogg "$HOME"/*.html; do
    [ -f "$f" ] || continue
    case "$(basename "$f")" in panel.log*|*.bak*) continue;; esac
    [ -e "$DEST/$(basename "$f")" ] && continue          # lo que ya tenga la v1.1 no se pisa
    cp -p "$f" "$DEST/" && n=$((n+1))
done
for d in naves ingenieros avatares sonidos voces piper; do
    [ -d "$HOME/$d" ] && [ ! -e "$DEST/$d" ] && ln -s "$HOME/$d" "$DEST/$d"
done
echo "== $n archivos de datos copiados (ajustes, notas, viajes, logos, fondos...)"
cp "$ORIG/cambiar_panel.sh" "$ORIG/actualizar_v11.sh" "$ORIG/subir_v11.sh" "$ORIG/prueba_sonido.sh" "$HOME/" 2>/dev/null
bash "$HOME/cambiar_panel.sh" v11
