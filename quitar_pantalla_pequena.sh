#!/bin/bash
# Desactiva la pantalla pequena de 3,5" (SPI): comenta su linea dtoverlay en config.txt, con copia de seguridad.
# Para volver a ponerla: quita el # de esa linea (o recupera la copia) y reinicia.
CFG=/boot/firmware/config.txt; [ -f $CFG ] || CFG=/boot/config.txt
grep -n -E '^dtoverlay=(piscreen|tft35a|waveshare35|mhs35|ads7846)' $CFG || { echo "No hay ninguna pantalla pequena activa en $CFG"; exit 0; }
BAK="$CFG.bak$(date +%Y%m%d%H%M)"
sudo cp $CFG "$BAK"
sudo sed -i -E 's/^(dtoverlay=(piscreen|tft35a|waveshare35|mhs35|ads7846).*)$/#\1/' $CFG
echo "Hecho (copia en $BAK). Ahora:  sudo reboot"
