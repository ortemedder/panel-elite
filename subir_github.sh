#!/bin/bash
# Sube a GitHub (ortemedder/panel-elite) el panel actual. Uso: bash ~/subir_github.sh
# Necesita el token guardado una vez:  git config --global credential.helper store  (y un push a mano)
set -u
REPO=~/panel-elite
cd "$REPO" || { echo "No encuentro $REPO"; exit 1; }
git pull -q --rebase 2>/dev/null
mkdir -p pc parches
cp ~/panel.py .
cp ~/fondo_*.jpg . 2>/dev/null
[ -d ~/naves ] && cp -r ~/naves .
cp ~/patch_*.py parches/ 2>/dev/null
cp ~/backup_panel.sh ~/subir_github.sh ~/actualizar.sh ~/sonido_hdmi.sh ~/quitar_pantalla_pequena.sh ~/instalar.sh ~/panel_run.py . 2>/dev/null
[ -d ~/ingenieros ] && cp -r ~/ingenieros .
[ -f ~/pc/elite_sender.py ] && cp ~/pc/elite_sender.py pc/        # el sender, si lo dejas en ~/pc
git add -A
if git diff --cached --quiet; then
    echo "Nada nuevo que subir."; exit 0
fi
if git diff --cached --name-only | grep -qi "inara_clave"; then
    echo "¡OJO! inara_clave.txt iba a subirse. Cancelado."; git reset -q; exit 1
fi
VER=$(grep -m1 -o 'PANEL_VER = "v[^ "]*' panel.py | cut -d'"' -f2)
git commit -q -m "Panel $VER · $(date '+%d/%m/%Y %H:%M')" || { echo "Fallo al hacer el commit (¿falta git config user.name / user.email?)"; exit 1; }
git push -q || { echo "Fallo al subir (¿token caducado?)"; exit 1; }
# cada version (o beta) queda marcada con su etiqueta, p. ej. v1.0b1
if ! git rev-parse -q --verify "refs/tags/$VER" >/dev/null; then
    git tag "$VER" && git push -q origin "$VER"
fi
echo "Subido a GitHub: $VER"
