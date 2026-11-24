#!/usr/bin/env python3
# Sender v1.0 beta 19 (desde la beta 18), para el panel v2.2b2:
# - EDMC SOLO: al arrancar el juego (y al abrir el sender con el juego ya abierto) mira si EDMarketConnector está
#   abierto y, si no, lo abre (lo que sube tus datos a Inara). Arriba del sender:
#     EDMC_AUTO = True / False   (False: no hace nada)
#     EDMC_EXE  = ""             (vacío: lo busca solo en Archivos de programa; si no, la ruta del .exe)
#   El panel enseña «EDMC ABIERTO» o «NO ENCUENTRO EDMC».
# Uso:  python patch_sender_v100b19.py elite_sender.py   (deja una copia elite_sender.py.bak100b18)
#       python patch_sender_v100b19.py elite_sender.py no   (igual, pero con EDMC_AUTO = False)
import shutil, sys
P = sys.argv[1] if len(sys.argv) > 1 else "elite_sender.py"
AUTO = "False" if len(sys.argv) > 2 and sys.argv[2].lower() in ("no", "false", "0") else "True"
s = open(P, encoding="utf-8").read()
if 'SENDER_VER = "v1.0b19"' in s:
    sys.exit("Ya estaba aplicado")
if 'SENDER_VER = "v1.0b18"' not in s:
    sys.exit("Este parche es para el sender v1.0b18")
shutil.copy(P, P + ".bak100b18")

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"No encuentro ({s.count(old)}): " + old[:70])
    s = s.replace(old, new)

rep('SENDER_VER = "v1.0b18"', 'SENDER_VER = "v1.0b19"')
rep('PORT = 5005\n', f'''PORT = 5005
EDMC_AUTO = {AUTO}         # v1.0b19: abrir EDMarketConnector (Inara) al arrancar el juego si no está abierto
EDMC_EXE = ""              # vacío = lo busco solo; si no, la ruta, p. ej. r"D:\\Juegos\\EDMarketConnector\\EDMarketConnector.exe"
''')
rep('''    handle_v100b3(e)
    if ev == "SystemsShutdown":''', '''    handle_v100b3(e)
    if ev == "LoadGame":
        edmc_check("juego")
    if ev == "SystemsShutdown":''')
rep('''threading.Thread(target=hola_loop, daemon=True).start()
print("Sender", SENDER_VER)''', '''threading.Thread(target=hola_loop, daemon=True).start()

# ---- v1.0b19: abrir EDMC (Inara) si no está abierto ----
EDMC = {"t": 0}

def _edmc_rutas():
    out = []
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA"),
                 os.path.join(os.environ.get("LOCALAPPDATA") or "", "Programs")):
        if base:
            out.append(os.path.join(base, "EDMarketConnector", "EDMarketConnector.exe"))
    return out

def _abierto(exe):
    import subprocess
    r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe}", "/NH"], capture_output=True, text=True, timeout=15,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return exe.lower() in (r.stdout or "").lower()

def _edmc_run(motivo):
    import subprocess
    try:
        if motivo == "inicio" and not _abierto("EliteDangerous64.exe"):
            return                                           # el juego no está abierto: nada
        if _abierto("EDMarketConnector.exe"):
            print("EDMC ya estaba abierto", flush=True)
            return
        exe = EDMC_EXE.strip() or next((p for p in _edmc_rutas() if os.path.isfile(p)), "")
        if not exe or not os.path.isfile(exe):
            print("NO ENCUENTRO EDMC: pon su ruta en EDMC_EXE (arriba del sender)", flush=True)
            note("edmc", "no|" + (exe or ""))
            return
        subprocess.Popen([exe], cwd=os.path.dirname(exe), close_fds=True,
                         creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        print("EDMC ABIERTO:", exe, flush=True)
        note("edmc", "ok|" + exe)
    except Exception as e:
        print("No he podido abrir EDMC:", e, flush=True)

def edmc_check(motivo):
    if not EDMC_AUTO or os.name != "nt" or (motivo != "inicio" and not LIVE[0]) or time.time() - EDMC["t"] < 60:
        return
    EDMC["t"] = time.time()
    threading.Thread(target=_edmc_run, args=(motivo,), daemon=True).start()

print("Sender", SENDER_VER)''')
rep('''startup_scan()
LIVE[0] = True''', '''startup_scan()
LIVE[0] = True
edmc_check("inicio")''')
open(P, "w", encoding="utf-8").write(s)
print("Sender actualizado a v1.0b19" + ("" if AUTO == "True" else " (EDMC_AUTO = False)"))
