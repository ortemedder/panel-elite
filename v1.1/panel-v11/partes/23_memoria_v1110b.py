# Panel Elite v1.1 · parte 23: EMITIR sin fugas de memoria (v1.1.10b)
#   pygame pierde la imagen entera cada vez que guarda un JPEG en memoria (BytesIO): con EMITIR a 10 imágenes/s
#   el panel subía cientos de MB en minutos y no bajaba al desconectar. Ahora el JPEG se escribe en un fichero
#   en RAM (/dev/shm) y se lee: sin fuga. Además, EMITIR se apaga solo si el panel pasa del 30 % de la RAM.
_JPG_DIR = "/dev/shm" if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK) else "/tmp"

def jpg_bytes(surf):
    f = os.path.join(_JPG_DIR, f"panel_{os.getpid()}_{threading.get_ident()}.jpg")
    pygame.image.save(surf, f)
    with open(f, "rb") as fh:
        return fh.read()

def mem_loop_v1110b():
    while True:
        time.sleep(15)
        try:
            p = mem_rss_pct()
            if p > 30 and cfg.get("stream"):
                cfg["stream"] = False
                plog(f"EMITIR apagado: el panel usaba el {p:.0f} % de la RAM")
                set_alert("EMITIR APAGADO", f"el panel usaba el {p:.0f} % de la RAM · vuelve a encenderlo en AJUSTES", RED, 10)
        except Exception:
            pass

threading.Thread(target=mem_loop_v1110b, daemon=True, name="memoria2").start()
