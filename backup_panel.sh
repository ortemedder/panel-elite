#!/bin/bash
# Copia de seguridad completa del panel Elite (PI4ELITE). Uso:  bash ~/backup_panel.sh
# Guarda en ~/backups/panel_<version>_<fecha>.tar.gz todo lo necesario para reinstalar en una SD nueva.
set -u
cd ~
mkdir -p backups
VER=$(grep -o 'PANEL_VER = "v[0-9.]*[a-z]*' panel.py 2>/dev/null | grep -o 'v[0-9.]*[a-z]*' || echo vX)
F=backups/panel_${VER}_$(date +%Y%m%d_%H%M).tar.gz
TMP=$(mktemp -d)

# lista de paquetes instalados (para reinstalarlos de golpe)
dpkg --get-selections > "$TMP/paquetes_apt.txt" 2>/dev/null
pip3 freeze 2>/dev/null > "$TMP/paquetes_pip.txt"
crontab -l > "$TMP/crontab.txt" 2>/dev/null
cat > "$TMP/RESTAURAR.txt" <<'EOF'
RESTAURAR EN UNA SD NUEVA (Raspberry Pi OS, usuario ortem, nombre PI4ELITE, IP 192.168.0.94)
1. Copia el .tar.gz a /home/ortem y descomprime todo en su sitio:
     sudo tar xzf panel_*.tar.gz -C /
2. Paquetes:  sudo apt install $(grep -v deinstall /home/ortem/restaurar/paquetes_apt.txt | cut -f1)   (o solo python3-pygame python3-evdev python3-numpy espeak-ng)
3. Programador:  crontab /home/ortem/restaurar/crontab.txt   (si tenía algo)
4. Servicios:  sudo systemctl daemon-reload && sudo systemctl enable --now elite-panel elite-hid
5. Reinicia:  sudo reboot
EOF

# todo el directorio de ortem (panel, fotos, sonidos, notas, json, parches, repo...) menos copias y caches
sudo tar czf "$F" --ignore-failed-read \
  --exclude=home/ortem/backups --exclude=home/ortem/.cache --exclude='*.bak*' --exclude='__pycache__' \
  -C / home/ortem \
  usr/local/bin/elite-hid.sh \
  $(cd / && ls -d etc/systemd/system/elite* 2>/dev/null) \
  boot/firmware/config.txt boot/firmware/cmdline.txt etc/asound.conf etc/hostname etc/hosts \
  etc/NetworkManager/system-connections \
  --transform "s|^${TMP#/}|home/ortem/restaurar|" "${TMP#/}" 2>/dev/null
sudo chown ortem "$F"
rm -rf "$TMP"
ls -1t backups/panel_*.tar.gz 2>/dev/null | tail -n +5 | xargs -r rm --      # se guardan las 4 ultimas
echo "Copia hecha: $F ($(du -h "$F" | cut -f1))"
echo "Contenido:"; tar tzf "$F" | grep -v '/$' | sed 's|^home/ortem/||' | head -40
echo "..."; ls -lh backups | tail -5
echo
echo "IMPORTANTE: saca la copia de la SD (si muere la SD, muere la copia). Desde el PC:"
echo "  scp ortem@192.168.0.94:~/$F ."
