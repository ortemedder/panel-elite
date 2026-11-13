# Panel Elite v1.1 · parte 06: galnet objetivos y voz (lineas 3749-5568 del panel entero)
# ---------- 12.10 objetivos comunitarios ----------
CG_URL = "https://api.orerve.net/2.0/website/initiatives/list?lang=es"
cgoals = {"list": [], "t": 0, "err": "", "page": 0, "d": None}

def _first(it, *keys):
    for k in keys:
        v = it.get(k)
        if v not in (None, "", []):
            return v
    return None

def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None

def cg_fetch():
    import urllib.request
    req = urllib.request.Request(CG_URL, headers={"User-Agent": "PanelElite/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    items = data.get("activeInitiatives") if isinstance(data, dict) else data
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        out.append({"title": str(_first(it, "title", "name") or "?"),
                    "sys": str(_first(it, "starsystem_name", "system_name", "systemName", "system") or ""),
                    "market": str(_first(it, "market_name", "marketName", "station_name", "station") or ""),
                    "expiry": str(_first(it, "expiry", "end_date", "endDate", "expires") or ""),
                    "qty": _num(_first(it, "qty", "current_qty", "progress", "current")),
                    "target": _num(_first(it, "target_qty", "targetQty", "target")),
                    "text": galnet_text(str(_first(it, "objective", "bulletin", "description") or ""))[:300]})
    return out

def cg_loop():
    while True:
        try:
            cgoals["list"], cgoals["t"], cgoals["err"] = cg_fetch(), time.time(), ""
            time.sleep(1800)
        except Exception as e:
            cgoals["err"] = str(e)[:60]
            print("objetivos:", e, flush=True)
            time.sleep(600)

threading.Thread(target=cg_loop, daemon=True).start()

def cg_secs(exp):
    import calendar
    e = (exp or "").replace("Z", "")
    for txt, fmt in ((e[:19], "%Y-%m-%dT%H:%M:%S"), (e[:19], "%Y-%m-%d %H:%M:%S"), (e[:10], "%Y-%m-%d")):
        try:
            return calendar.timegm(time.strptime(txt, fmt)) - time.time()
        except ValueError:
            continue
    return None

CG_KEEP = 2 * 86400            # los cerrados se ven 2 dias y desaparecen

def cg_all(d):
    mine = [dict(g, me=True) for g in ((d or {}).get("mycg") or [])]
    names = {g["title"].lower() for g in mine}
    done = cgoals.setdefault("done", {})
    out = []
    for g in mine + [g for g in cgoals["list"] if g["title"].lower() not in names]:
        sec = cg_secs(g.get("expiry", ""))
        closed = bool(g.get("complete")) or (sec is not None and sec <= 0)
        if closed:
            t0 = done.setdefault(g["title"].lower(), time.time())
            gone = (-sec if sec is not None and sec <= 0 else time.time() - t0)
            if gone > CG_KEEP:
                continue
        out.append(dict(g, closed=closed))
    return [g for g in out if not g["closed"]] + [g for g in out if g["closed"]]

_CGF = {}

def cg_band(surf, r, g):
    """Ficha cerrada: velo oscuro y banda oblicua roja CERRADO."""
    veil = pygame.Surface((r.w, r.h)); veil.set_alpha(150); veil.fill(BLACK)
    surf.blit(veil, r.topleft)
    f = _CGF.get("f") or _CGF.setdefault("f", pygame.font.Font(None, 30))
    band = pygame.Surface((int(r.w * 0.7), 30), pygame.SRCALPHA)
    band.fill(RED)
    tx = f.render("CERRADO", True, WHITE)
    band.blit(tx, tx.get_rect(center=band.get_rect().center))
    band = pygame.transform.rotate(band, 10)
    surf.blit(band, band.get_rect(center=r.center).topleft)
    if g.get("me"):
        put(surf, F["small"], "cobra la recompensa", (r.centerx, r.bottom - 16), GREEN, anchor="center")

def cg_left(exp):
    import calendar
    e = (exp or "").replace("Z", "")
    for txt, fmt in ((e[:19], "%Y-%m-%dT%H:%M:%S"), (e[:19], "%Y-%m-%d %H:%M:%S"), (e[:10], "%Y-%m-%d")):
        try:
            sec = calendar.timegm(time.strptime(txt, fmt)) - time.time()
            break
        except ValueError:
            continue
    else:
        return exp[:16]
    if sec <= 0:
        return "terminado"
    dd, hh = int(sec // 86400), int(sec % 86400 // 3600)
    return f"quedan {dd}d {hh}h" if dd else f"quedan {hh}h {int(sec % 3600 // 60)}m"

def _tier(t):
    m = re.search(r"\d+", t or "")
    return int(m.group()) if m else None

CG_PER = 2
CG_PAGE = pygame.Rect(W - 118, TOP + 2, 110, 28)

def view_cgoals(surf, d, flags, now):
    cgoals["d"] = d
    L = cg_all(d)
    pages = max(1, (len(L) + CG_PER - 1) // CG_PER)
    pg = cgoals["page"] % pages
    if cgoals["err"] and not L:
        info, col = cgoals["err"], RED
    elif cgoals["t"]:
        na = sum(1 for g in L if not g.get("closed"))
        info, col = f"{na} activo{'s' if na != 1 else ''} · actualizado " + time.strftime("%H:%M", time.localtime(cgoals["t"])), DIM
    else:
        info, col = "descargando...", DIM
    put(surf, F["small"], info, (8, TOP + 9), col, W - 140)
    if pages > 1:
        draw_button(surf, CG_PAGE, f"PÁG {pg + 1}/{pages} >", None, F["small"])
    if not L:
        put(surf, F["btn"], "No hay objetivos comunitarios activos", (W // 2, (H + TOP) // 2), DIM, anchor="center")
        return
    for i, g in enumerate(L[pg * CG_PER:(pg + 1) * CG_PER]):
        r = pygame.Rect(6, TOP + 34 + i * 116, W - 12, 110)
        me = g.get("me")
        pygame.draw.rect(surf, GREEN if me else DIM, r, 1, border_radius=5)
        put(surf, F["btn"], g["title"], (r.x + 8, r.y + 4), ORANGE, r.w - 16)
        where = " · ".join(x for x in (g.get("sys", "").upper(), g.get("market", "")) if x)
        put(surf, F["small"], where, (r.x + 8, r.y + 24), WHITE, r.w - 140)
        left = "COMPLETADO" if g.get("complete") else cg_left(g.get("expiry", ""))
        put(surf, F["small"], left, (r.right - 8, r.y + 24), GREEN if g.get("complete") else BLUE, anchor="topright")
        bar = pygame.Rect(r.x + 8, r.y + 44, r.w - 16, 14)
        pygame.draw.rect(surf, DIM, bar, 1)
        t, top = _tier(g.get("tier")), _tier(g.get("top"))
        if t is not None and top:
            pct, txt = min(1.0, t / top), f"NIVEL {t} de {top}"
        elif g.get("qty") is not None and g.get("target"):
            pct = min(1.0, g["qty"] / g["target"]); txt = f"{fnum(g['qty'], 0)} / {fnum(g['target'], 0)}"
        else:
            pct, txt = None, ""
        if pct is not None:
            pygame.draw.rect(surf, GREEN if me else ORANGE, (bar.x + 2, bar.y + 2, int((bar.w - 4) * pct), bar.h - 4))
        put(surf, F["small"], txt, (r.x + 8, r.y + 62), GREEN if me else ORANGE)
        if me:
            if g.get("contrib"):
                put(surf, F["small"], f"{fnum(g['contrib'], 0)} pilotos", (r.right - 8, r.y + 62), DIM, anchor="topright")
            mine = f"TU APORTACIÓN: {fnum(g.get('mine') or 0, 0)}"
            if g.get("band"):
                mine += f"   ·   estás en el {g['band']}% mejor"
            if g.get("toprank"):
                mine += "   ·   TOP"
            put(surf, F["small"], mine, (r.x + 8, r.y + 82), GREEN, r.w - 16)
        elif g.get("text"):
            put(surf, F["small"], g["text"].replace("\n", " "), (r.x + 8, r.y + 82), DIM, r.w - 16)
        if g.get("closed"):
            cg_band(surf, r, g)

VIEWS[132] = view_cgoals
MENU[132] = "OBJETIVOS COMUNITARIOS"
PARENT[132] = 12


# ---------- pantalla de SALIR ----------
def draw_bye(surf):
    surf.fill(BLACK)
    _orig_rect(surf, ORANGE, (0, 0, W, H), 2)
    put(surf, F["num"], "PANEL PARADO", (W // 2, 70), ORANGE, W - 20, anchor="center")
    put(surf, F["btn"], "El shell está en la pantalla HDMI", (W // 2, 125), WHITE, W - 20, anchor="center")
    put(surf, F["small"], "Para volver a arrancar el panel:", (W // 2, 175), DIM, anchor="center")
    put(surf, F["btn"], "sudo systemctl start elite-panel", (W // 2, 200), GREEN, W - 20, anchor="center")
    put(surf, F["small"], "o reinicia la Pi", (W // 2, 235), DIM, anchor="center")
    put(surf, F["small"], PANEL_VER.split(" · ")[0], (W // 2, H - 20), DIM, anchor="center")


# ---------- v0.58: 12 AJUSTES, pestanas de informacion y engranaje ----------
TABS = [[(3, "NAVEGACIÓN"), (128, "NOTAS")],
        [(4, "CARGA/MISIÓN"), (125, "MATERIALES")],
        [(8, "ESTACIÓN"), (127, "MERCADO"), (126, "PORTANAVES")],
        [(11, "DÍA"), (130, "GALNET"), (132, "OBJ.COM"), (123, "RANGOS")]]
TAB_OF = {129: 128, 131: 130}          # pantallas de detalle -> su pestana
GEAR = pygame.Rect(W - 50, 2, 46, TOP - 8)      # engranaje a la derecha del todo
MENU.update({12: "AJUSTES", 11: "RESUMEN DEL DÍA"})
for _v in (123, 125, 126, 127, 128, 130, 132):
    PARENT[_v] = 0
PARENT.update({121: 12, 122: 12, 1244: 12, 1245: 12}); MENU[1244] = "OPCIONES"

def tab_group(v):
    v = TAB_OF.get(v, v)
    for g in TABS:
        if any(t == v for t, _ in g):
            return g, v
    return None, v

def tab_rects(v):
    g, cur = tab_group(v)
    if not g:
        return []
    out, x = [], BACK.right + 4
    for t, name in g:
        w = F["small"].size(name)[0] + 16
        out.append((t, name, pygame.Rect(x, 35, w, 19), t == cur))
        x += w + 3
    return out

def draw_tabs(surf, v):
    for t, name, r, on in tab_rects(v):
        new = t == 130 and galnet["new"]
        col = GREEN if new else ORANGE
        if on:
            pygame.draw.rect(surf, col, r, border_radius=4)
            put(surf, F["small"], name, r.center, BLACK, anchor="center")
        else:
            pygame.draw.rect(surf, col if new else DIM, r, 1, border_radius=4)
            put(surf, F["small"], name, r.center, col, anchor="center")

def draw_gear(surf, v, now):
    on = v in (12, 121, 122, 1244, 1245)
    col = WHITE if flash.get(("gear",), 0) > now else ORANGE
    if on:
        pygame.draw.rect(surf, ORANGE, GEAR, 2, border_radius=6)
    cx, cy = GEAR.center
    rot = now * 40                                   # gira despacio (40 grados por segundo)
    for a in range(8):
        r_ = math.radians(a * 45 + rot)
        pygame.draw.line(surf, col, (cx + 11 * math.cos(r_), cy + 11 * math.sin(r_)),
                         (cx + 17 * math.cos(r_), cy + 17 * math.sin(r_)), 6)
    pygame.draw.circle(surf, col, (cx, cy), 13)
    pygame.draw.circle(surf, BLACK, (cx, cy), 5)
    if power["now"] and int(now * 2) % 2 == 0:
        draw_bolt(surf, GEAR.x - 20, 28, RED)

def tap_topbar(x, y, v):
    if x >= GEAR.x - 4:
        tap_flash(("gear",)); ui["view"] = 12; return True
    for t, _, r, _ in tab_rects(v):
        if r.inflate(2, 10).collidepoint(x, y):
            ui["view"] = t; ui["page4"] = 0; return True
    return False

SET12 = [("OPCIONES", 1244), ("ESTILO", "style"), ("BORDES", "borders"), ("ICONOS", "icons"),
         ("VERSIONES", 1245), ("LOG", 121), ("STREAM", 122), ("PANTALLA", 160),
         ("SALIR", 0), ("REINICIAR", 1), ("APAGAR", 2), ("MANUAL", 140)]

def SET12_ROWS():
    return (len(SET12) + 3) // 4                         # v1.1: con la CALCULADORA, 4 filas

def view_sub12(surf, d, flags, now):
    c, until = ui["confirm"]
    for i, it in enumerate(SET12):
        if not it:
            continue
        name, act = it
        r = grid(i, 4, SET12_ROWS())
        sub = {"style": "CABINA" if style["cab"] else "CLÁSICO",
               "borders": "SÍ" if style.get("borders", True) else "NO",
               "icons": "SÍ" if ICONS_ON[0] else "NO",
               "stackchan": sc_estado() if "sc_estado" in globals() else "",
               "bigmode": BIGMODES.get(cfg.get("bigmode", "4"), "4 CUADROS")}.get(act) if isinstance(act, str) else (
                   f"{BIGMODES.get(cfg.get('bigmode', '4'), '4 CUADROS')} · {'ALTA' if cfg.get('sharp') else 'NORMAL'}" if act == 160 else None)
        if i in (8, 9, 10):
            sure = c == ("pw", act) and time.time() < until
            draw_button(surf, r, "¿SEGURO?" if sure else name, None if sure else "toca 2 veces", F["btn"],
                        filled=sure, lit=flash.get((1240, act), 0) > now)
        else:
            draw_button(surf, r, name, sub, F["btn"], filled=(act == "style" and style["cab"]) or (act == "stackchan" and bool(cfg.get("stackchan"))),
                        lit=flash.get((12, i), 0) > now)

def tap_sub12(x, y):
    for i, it in enumerate(SET12):
        if not it or not grid(i, 4, SET12_ROWS()).collidepoint(x, y):
            continue
        name, act = it
        if i in (8, 9, 10):
            power_tap(act); return
        tap_flash((12, i))
        if act == "style":
            style_toggle()
        elif act == "borders":
            borders_toggle()
        elif act == "icons":
            icons_toggle()
        elif act == "stackchan":
            cfg["stackchan"] = not cfg.get("stackchan", False); save_cfg()
        elif act == "bigmode":
            order = list(BIGMODES)
            cfg["bigmode"] = order[(order.index(cfg.get("bigmode", "4")) + 1) % len(order)]
            save_cfg()
        else:
            ui["view"] = act
        return

VIEWS[12] = view_sub12


# ---------- alimentacion de la Pi (vcgencmd get_throttled) ----------
power = {"now": False, "past": False, "warned": 0, "ok": False}

def power_loop():
    while True:
        try:
            out = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=5).stdout
            v = int(out.strip().split("=")[1], 16)
            power.update(now=bool(v & 1), past=bool(v & 0x10000), ok=True, cap=bool(v & 0x6))
            if power["now"] and time.time() - power["warned"] > 600 and ev_on("power"):
                power["warned"] = time.time()
                set_alert("BAJA TENSIÓN", "a la Pi le falta corriente: revisa la alimentación", RED, 5)
        except Exception:
            pass
        time.sleep(10)

threading.Thread(target=power_loop, daemon=True).start()

def draw_bolt(surf, x, y, col, k=1.0):
    pts = [(6, 0), (0, 11), (5, 11), (2, 20), (11, 7), (6, 7), (9, 0)]
    pygame.draw.polygon(surf, col, [(x + px * k, y + py * k) for px, py in pts])

def power_box(surf, r):
    pygame.draw.rect(surf, DIM, r, 1, border_radius=6)
    put(surf, F["small"], "ALIMENTACIÓN", (r.centerx, r.y + 10), DIM, anchor="midtop")
    if not power["ok"]:
        txt, col = "sin datos", DIM
    elif power["now"]:
        txt, col = "¡BAJA!", RED
    elif power["past"]:
        txt, col = "AVISOS", ORANGE
    else:
        txt, col = "CORRECTA", GREEN
    put(surf, F["btn"], txt, (r.centerx, r.centery + 2), col, r.w - 8, anchor="center")
    sub = "ahora mismo" if power["now"] else "desde que arrancó" if power["past"] else ""
    if sub:
        put(surf, F["small"], sub, (r.centerx, r.bottom - 22), DIM, r.w - 8, anchor="midtop")


# ---------- registro de errores: /tmp/claude-0/s/t53/panel.log y pantalla LOG ----------
import builtins, traceback, os as _os
PANEL_LOG = os.path.join(PANEL_DIR, "panel.log")
_err_seen = {}

def plog_base(*a, **k):
    msg = " ".join(str(x) for x in a)
    builtins.print(msg, flush=True)
    try:
        if _os.path.exists(PANEL_LOG) and _os.path.getsize(PANEL_LOG) > 300000:
            _os.replace(PANEL_LOG, PANEL_LOG + ".1")
        with open(PANEL_LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("%d/%m %H:%M:%S ") + msg + "\n")
    except OSError:
        pass
    if lock.acquire(timeout=0.2):
        try:
            state["log"].append("[PANEL] " + msg)
        finally:
            lock.release()

print = plog_base

def log_exc(where, e):
    key = (where, type(e).__name__, str(e)[:80])
    if time.time() - _err_seen.get(key, 0) > 300:          # el mismo error, como mucho cada 5 min
        _err_seen[key] = time.time()
        plog(f"ERROR en {where}: {e}\n" + "".join(traceback.format_exc().splitlines(True)[-4:]))

sys_excepthook = None
def _hook(t, e, tb):
    plog("ERROR GRAVE: " + "".join(traceback.format_exception(t, e, tb)))
import sys as _sys
_sys.excepthook = _hook
threading.excepthook = lambda a: plog(f"ERROR en hilo {a.thread.name if a.thread else '?'}: " +
                                       "".join(traceback.format_exception(a.exc_type, a.exc_value, a.exc_traceback)))


# ---------- EMITIR: las pantallas por la red (http://IP:8080) ----------
# Solo gasta CPU mientras alguien esta mirando: si no hay nadie conectado no se copia ni se comprime nada.
STREAM_PORT = 8080
stream = {"clients": 0, "big": None, "small": None, "seq": 0, "jpg": {}, "srv": None, "err": ""}
stream_lock = threading.Lock()
VOICE_JS = r"""
<script>
const ST = (()=>{ try { return JSON.parse(localStorage.getItem('vozpanel') || '{}'); } catch(e) { return {}; } })();
function guardar(){ try { localStorage.setItem('vozpanel', JSON.stringify(ST)); } catch(e) {} }
let ctx = null;
function audio(){ if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)(); return ctx; }
function tono(f0, f1, dur, t0){
  const c = audio(), o = c.createOscillator(), g = c.createGain(), vol = 0.25 * (ST.vol ?? 1);
  o.frequency.setValueAtTime(f0, t0); o.frequency.linearRampToValueAtTime(f1 || f0, t0 + dur);
  g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(vol, t0 + .01);
  g.gain.setValueAtTime(vol, t0 + dur - .02); g.gain.linearRampToValueAtTime(0, t0 + dur);
  o.connect(g).connect(c.destination); o.start(t0); o.stop(t0 + dur);
}
function pitido(tipo){
  if (ST.pitidos === false) return 0;
  const c = audio(); c.resume(); let t = c.currentTime;
  if (tipo === 'alarm') { for (let k = 0; k < 2; k++) { tono(880, 880, .15, t); tono(660, 660, .15, t + .2); t += .4; } return .8; }
  if (tipo === 'jump')  { tono(200, 1200, 1.2, t); return 1.2; }
  tono(660, 990, .18, t); return .2;
}
function vocesEs(){ return speechSynthesis.getVoices().filter(v => v.lang.toLowerCase().startsWith('es')); }
const dicho = {};
function decir(a){
  const txt = ((a.titulo || '') + '. ' + (a.dato || '')).replace(/[¡!¿?>|·_]/g, ' ').replace(/\s+/g, ' ').trim();
  if (!txt || Date.now() - (dicho[txt] || 0) < 30000) return;
  dicho[txt] = Date.now();
  const espera = pitido(a.tipo);
  if (ST.voz === false) return;
  setTimeout(() => {
    const u = new SpeechSynthesisUtterance(txt);
    const v = vocesEs().find(x => x.name === ST.nombre) || vocesEs()[0];
    if (v) { u.voice = v; u.lang = v.lang; } else u.lang = 'es-ES';
    u.rate = ST.vel ?? 1.0; u.pitch = ST.tono ?? 0.9; u.volume = ST.vol ?? 1;
    speechSynthesis.speak(u);
    const e = document.getElementById('ultimo'); if (e) e.textContent = txt;
  }, espera * 1000 + 150);
}
let desde = -1;
async function sondeo(){
  const est = document.getElementById('estado');
  try {
    const j = await (await fetch('/avisos?desde=' + desde, {cache: 'no-store'})).json();
    if (desde < 0 || j.seq < desde) desde = j.seq;          // al abrir (o si la Pi reinicia) no lee lo antiguo
    else { j.items.forEach(decir); desde = j.seq; }
    if (est) { est.textContent = 'CONECTADO A LA PI'; est.style.color = '#3ad13a'; }
  } catch(e) { if (est) { est.textContent = 'SIN CONEXIÓN CON LA PI'; est.style.color = '#e03030'; } }
  setTimeout(sondeo, 1000);
}
function activar(){
  audio().resume();
  const ov = document.getElementById('activar'); if (ov) ov.style.display = 'none';
  const u = new SpeechSynthesisUtterance(' '); speechSynthesis.speak(u);
}
window.addEventListener('load', () => {
  sondeo();
  setTimeout(() => { if (audio().state === 'running') activar(); }, 300);   // OBS: ya puede sonar sin tocar
});
</script>
<div id="activar" onclick="activar()" style="position:fixed;inset:0;background:rgba(0,0,0,.85);color:#ff8c00;
 display:flex;align-items:center;justify-content:center;font:bold 28px Segoe UI,Arial;cursor:pointer;z-index:9">
 TOCA AQUÍ PARA ACTIVAR LA VOZ</div>
"""

CLICK_JS = """<script>
(function(){const im=document.querySelector('img');if(!im)return;im.style.cursor='pointer';
im.addEventListener('click',ev=>{const r=im.getBoundingClientRect(),nw=im.naturalWidth,nh=im.naturalHeight;if(!nw)return;
const sc=Math.min(r.width/nw,r.height/nh),dx=(r.width-nw*sc)/2,dy=(r.height-nh*sc)/2;
const x=Math.round((ev.clientX-r.left-dx)/sc),y=Math.round((ev.clientY-r.top-dy)/sc);
if(x<0||y<0||x>=nw||y>=nh)return;
fetch('/tap?x='+x+'&y='+y+'&w='+nw+'&h='+nh+'&s='+(im.src.indexOf('/panel')>=0?'p':'h'),{cache:'no-store'});});})();
document.addEventListener('keydown',ev=>{const k={Escape:'esc',Backspace:'esc',m:'m',M:'m',a:'a',A:'a',Tab:'tab'}[ev.key];
if(!k)return;ev.preventDefault();fetch('/key?k='+k,{cache:'no-store'});});
</script>"""

STREAM_HTML = ("<!doctype html><html><head><meta charset='utf-8'><title>Panel Elite</title></head>"
               "<body style='margin:0;background:#000;overflow:hidden'>"
               "<img src='/hdmi' style='width:100vw;height:100vh;object-fit:contain'>" + CLICK_JS + VOICE_JS +
               "</body></html>").encode()

VOZ_HTML = ("""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Voz del panel Elite</title>
<style>body{margin:0;background:#000;color:#ff8c00;font-family:Segoe UI,Arial,sans-serif;padding:20px}
h1{margin:0}.d{color:#a05800}select,input{background:#111;color:#ff8c00;border:1px solid #a05800;font-size:16px;padding:5px;margin:4px}
button{background:#000;color:#ff8c00;border:2px solid #ff8c00;border-radius:6px;font-size:16px;padding:8px 14px;margin:4px;cursor:pointer}
label{display:block;margin:8px 0}#ultimo{color:#fff}</style></head><body>
<h1>VOZ DEL PANEL</h1><p class="d">Deja esta pestaña abierta (puede estar minimizada). La voz la pone este PC; la Pi solo manda el texto.</p>
<p id="estado" class="d">conectando...</p>
<label>Voz: <select id="nombre"></select></label>
<label>Velocidad <input id="vel" type="range" min="0.6" max="1.6" step="0.1"></label>
<label>Tono <input id="tono" type="range" min="0.5" max="1.5" step="0.1"></label>
<label>Volumen <input id="vol" type="range" min="0.1" max="1" step="0.1"></label>
<label><input id="vozon" type="checkbox"> Hablar</label>
<label><input id="pitidos" type="checkbox"> Pitidos</label>
<button onclick="decir({tipo:'ok',titulo:'Prueba de voz',dato:'Panel Elite '+Date.now()%1000})">PROBAR</button>
<p class="d">Último aviso: <span id="ultimo">-</span></p>
""" + VOICE_JS + """
<script>
function rellenar(){
  const sel = document.getElementById('nombre'); sel.innerHTML = '';
  vocesEs().forEach(v => { const o = document.createElement('option'); o.value = o.textContent = v.name; sel.appendChild(o); });
  if (ST.nombre) sel.value = ST.nombre;
}
speechSynthesis.onvoiceschanged = rellenar; rellenar();
const C = {vel: 1.0, tono: 0.9, vol: 1};
for (const k of ['vel', 'tono', 'vol']) { const e = document.getElementById(k); e.value = ST[k] ?? C[k]; e.oninput = () => { ST[k] = +e.value; guardar(); }; }
document.getElementById('nombre').onchange = e => { ST.nombre = e.target.value; guardar(); };
const vz = document.getElementById('vozon'), pt = document.getElementById('pitidos');
vz.checked = ST.voz !== false; pt.checked = ST.pitidos !== false;
vz.onchange = () => { ST.voz = vz.checked; guardar(); }; pt.onchange = () => { ST.pitidos = pt.checked; guardar(); };
</script></body></html>""").encode()

# avisos para el PC (solo texto)
feed = {"seq": 0, "items": []}

def feed_add(tipo, titulo, dato):
    with stream_lock:
        feed["seq"] += 1
        feed["items"].append({"n": feed["seq"], "tipo": tipo, "titulo": titulo or "", "dato": dato or ""})
        del feed["items"][:-20]

def stream_jpeg(which):
    import io
    with stream_lock:
        seq = stream["seq"]
        old = stream["jpg"].get(which)
        if old and old[0] == seq:
            return old[1]
        surf = stream["big"] if which == "big" and stream["big"] is not None else stream["small"]
        if surf is None:
            return None
        buf = io.BytesIO()
        pygame.image.save(surf, buf, "x.jpg")
        data = buf.getvalue()
        stream["jpg"][which] = (seq, data)
        return data

def stream_start():
    if stream["srv"]:
        return
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            path = self.path.split("?")[0]
            if path in ("/", "/ver"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(STREAM_HTML.replace(b"/hdmi", b"/panel") if "pequena" in self.path else STREAM_HTML)
                return
            if path == "/key":
                k = self.path.split("k=", 1)[-1][:4]
                if k == "esc":
                    on_tap(*BACK.center)
                elif k == "m":
                    ui["view"] = 0
                elif k == "a":
                    ui["view"] = 12
                elif k == "tab":
                    hdmi_toggle()
                self.send_response(204)
                self.end_headers()
                return
            if path == "/tap":
                try:
                    q = dict(kv.split("=", 1) for kv in self.path.split("?", 1)[1].split("&"))
                    remote_tap(int(q["x"]), int(q["y"]), int(q["w"]), int(q["h"]), q.get("s", "h"))
                except Exception:
                    pass
                self.send_response(204)
                self.end_headers()
                return
            if path == "/manual":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(manual_html())
                return
            if path == "/voz":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(VOZ_HTML)
                return
            if path == "/avisos":
                try:
                    desde = int(self.path.split("desde=")[1].split("&")[0])
                except (IndexError, ValueError):
                    desde = -1
                with stream_lock:
                    data = json.dumps({"seq": feed["seq"], "items": [a for a in feed["items"] if a["n"] > desde]})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(data.encode())
                return
            if path not in ("/hdmi", "/panel"):
                self.send_error(404); return
            which = "big" if path == "/hdmi" else "small"
            if stream["clients"] >= 3:                   # b16: como mucho 3 a la vez
                self.send_error(503); return
            try:
                self.connection.settimeout(10)           # b16: si no puede enviar en 10 s, se corta
            except Exception:
                pass
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            stream["clients"] += 1
            last = -1
            try:
                while cfg.get("stream"):
                    if stream["seq"] == last:
                        time.sleep(0.05); continue
                    last = stream["seq"]
                    jpg = stream_jpeg(which)
                    if jpg:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg))
                        self.wfile.write(jpg + b"\r\n")
            except Exception:
                pass
            finally:
                stream["clients"] -= 1

    try:
        srv = ThreadingHTTPServer(("0.0.0.0", STREAM_PORT), H)
        srv.daemon_threads = True
        stream["srv"] = srv
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"EMITIR: http://{my_ip()}:{STREAM_PORT}")
    except OSError as e:
        stream["err"] = str(e)[:40]
        print("EMITIR:", e)


if cfg.get("stream"):
    pass   # se arranca en main() cuando ya estan los ajustes cargados

# ---------- VOZ de la nave (espeak-ng) ----------
voice = {"alert": None, "xa": None, "proc": None, "last": {}}



def voice_watch():
    a, x = ui.get("alert"), xa.get("a")
    if a is not voice["alert"]:
        voice["alert"] = a
        if a and snd_on(a.get("ev")):
            voice_say(f'{a.get("text", "")}. {a.get("sub", "")}')
            if cfg.get("stream"):
                k = a.get("kind")
                feed_add("jump" if k == "jump" else "ok" if k in ("ok", "galnet") else "alarm", a.get("text"), a.get("sub"))
    if x is not voice["xa"]:
        voice["xa"] = x
        if x and snd_on(x.get("ev")):
            voice_say(f'{x.get("title", "")}. {x.get("big", "")}')
            if cfg.get("stream"):
                feed_add("alarm" if x.get("col") == RED else "ok", x.get("title"), x.get("big"))


# ---------- MANUAL (12 AJUSTES > MANUAL y http://IP:8080/manual) ----------
# Marcas: "# " titulo   "- " punto   "@r" rojo "@n" naranja "@v" verde "@a" azul "@m" marron "@g" gris
CREADOR = "CMDR ORTEM ED DER  ·  ortemedder@gmail.com"
MANUAL = [
("INICIO", "PRIMEROS PASOS", """
# Qué es
Panel táctil para Elite Dangerous: botones que pulsan teclas del juego y pantallas con los datos de tu nave en tiempo real.
# Cómo funciona
- En el PC de juego corre elite_sender.py: lee los ficheros del juego (Status.json y el journal) y los envía por la red a esta Pi.
- La Pi los muestra y, en la Pi 4, pulsa las teclas en el PC como si fuera un teclado USB.
- En el PC, control_sender.pyw tiene los botones INICIAR y PARAR del sender.
# Para empezar
- Enciende la Pi: arranca sola en la pantalla del reloj.
- En el PC pulsa INICIAR en el control del sender y abre Elite.
- Al entrar en el juego el panel pasa solo a EN VIVO.
- En elite_sender.py, PI_IP tiene que ser la IP de esta Pi: {ip}
# Tocar la pantalla
- Toque corto en los botones. En listas y textos, tocar pasa de página.
- < MENÚ (arriba a la izquierda) vuelve atrás.
# Ratón y teclado
- Con un ratón o un teclado con touchpad conectado a la Pi: clic izquierdo = tocar.
- Clic derecho o TAB: la pantalla HDMI cambia entre PANEL (los menús, para manejarlos con el ratón) y TABLERO (los cuadros de datos).
- ESC = atrás  ·  M = menú  ·  A = ajustes.
- En la página web del PC (EMITIR) también funcionan ESC, M, A y TAB.
# Teclas del juego
- Con el sender v0.77 el PC manda tus controles (el fichero .binds que usa el juego) y cada botón usa tu tecla.
- AJUSTES > OPCIONES > TECLAS: el fichero leído y los botones sin tecla de teclado, con una tecla libre que puedes asignar en el juego.
- Un botón sin tecla pone SIN TECLA y al tocarlo avisa.
# Menú principal y música del juego (con el sender v0.80)
- Al salir al menú principal: las dos pantallas pasan al reloj con EN EL MENÚ PRINCIPAL y sale el resumen de la sesión. Al volver a la partida el mapa empieza de cero.
- Música de combate: el panel pasa a COMBATE (a pie, a EN VIVO) antes del primer disparo. Se apaga en CAMBIO AUTO.
- Música thargoide: aviso ENCUENTRO THARGOIDE. Se apaga en ALERTAS y en SONIDO Y VOZ.
- Abrir el menú de Powerplay del juego lleva a NAVEGACIÓN > POWERPLAY; el de escuadrón, a la ficha ESCUADRÓN (nombre, tu rango, ala y amigos).
# Inara (solo lectura, con el sender v0.81)
- Pon tu clave de Inara (la misma de EDMC) en inara_clave.txt junto a elite_sender.py. La Pi no la ve.
- Opcional: inara_cmdrs.txt con otros comandantes, uno por línea (hasta 30: todo tu escuadrón). En ESCUADRÓN, tocando pasas las páginas: 6 por página, primero los conectados (en verde).
- La ficha ESCUADRÓN muestra el nombre real de tu rango y, de los otros CMDR, su nave, rango de combate y escuadrón. Se lee al arrancar y luego cada hora. Lo que sube a Inara lo sigue haciendo EDMC.
# Combate a pie
- EN VIVO a pie muestra siempre botiquines (+), células (rayo) y explosivos con barritas según el máximo de tu traje (Dominator 3/3/2, Maverick 2/1/1, Artemis 1/1/1). Rojo con 1 o ninguno.
- En combate (te atacan o hay bajas en el último minuto) la pantalla pasa a EN COMBATE en grande: salud, escudo, bajas, botiquines y células, créditos sin cobrar y explosivos.
- Al lanzar una granada: «quedan X de Y».
# Cierre de emergencia del juego
- (cuenta atrás de 3 segundos) Tres toques seguidos sobre la barra de arriba, entre MENÚ y el engranaje (el nombre del sistema); abajo sale «toque 1 de 3», «2 de 3»: pantalla roja con cuenta atrás rápida 3-2-1 y el sender del PC cierra Elite Dangerous (taskkill). Tocar en cualquier sitio cancela.
- Necesita el sender v0.84. La primera vez Windows puede preguntar por el cortafuegos: permite redes privadas.
- Se desactiva en AJUSTES > OPCIONES > CERRAR JUEGO.
# Salud crítica
- A pie, si la salud baja del 30 %: las dos pantallas en rojo parpadeando deprisa 3 segundos con ¡SALUD XX %! ¡BOTIQUÍN YA!, y luego un borde rojo parpadeando hasta que te cures. Se apaga en ALERTAS > SALUD BAJA (A PIE).
# Novedades v0.87
- Objetivos comunitarios cerrados: al final, tapados con una banda roja CERRADO («cobra la recompensa» si participaste); desaparecen a los 2 días.
- En la pantalla grande, las bajas a pie salen en el cuadro SRV / A PIE y los derribos en nave en el cuadro 3, sin tapar los demás.
- En combate de nave la pantalla grande pasa a COMBATE (sin MERCADO ni GALNET), también en Operations.
- CMDR fijado: con Inara salen su escuadrón, rango de combate y nave (ALIADO en verde si es de tu escuadrón). Se guarda 72 horas.
- EDSM: si no responde por los bloqueos de LaLiga sale «EDSM bloqueado (¿fútbol?)» y el sender lo reintenta cada 10 minutos.
# Naves (v0.88, con el sender v0.88)
- Toca el nombre de la nave en EN VIVO: pestañas NAVE (salto, combustible, carga, masa, valor y todos los módulos con su ingeniería y salud; los dañados arriba en rojo) y FLOTA (dónde está cada nave, traer: tiempo y precio, y salto, carga y armas para comparar).
- Al cambiar de nave salen todos sus datos a pantalla completa 15 segundos (toca para cerrar).
- Avisos: transferencia en camino, NAVE TRANSFERIDA al llegar y módulos por debajo del 80 %.
- En EN VIVO nave: SRV A BORDO 2/2, SRV FUERA, CAZA LISTO, CAZA RECONSTRUYENDO...
- El sender guarda tus naves en naves.json (junto a elite_sender.py); la FLOTA se actualiza al abrir el astillero.
# Novedades v0.89
- Transporte: al reservar la lanzadera o el transporte militar, EN VIVO muestra TRANSPORTE RESERVADO con 5:00 para subir (verde; naranja con menos de 2 min; rojo parpadeando en el último). Al minuto: «¡SUBE A LA LANZADERA!»; si se acaba, TRANSPORTE PERDIDO.
- A bordo: fase (embarque, despegue, supercrucero, aproximación, llegada), altitud y gravedad; en el transporte militar, la zona de combate, la facción y su estado.
- Totales de carrera (de las estadísticas del juego más lo de la partida): en RANGOS abajo; «total» de bajas a pie en EN VIVO y EN COMBATE; bonos y recompensas en el REGISTRO DE COMBATE; y en los avisos «BAJA nº X · total N», «DERRIBO nº X · bonos N».
- LUCES y VISIÓN NOCTURNA destellan en blanco al encenderlas y luego cogen su color.
- Operations: la ficha de la nave sale ya en la pantalla de carga y se refresca al llegar el equipamiento.
# Novedades v0.90
- NAVEGACIÓN: línea de saltos con hasta 10 estrellas (amarillo recolectable, rojo no, azul parpadeando neutrones, blanco parpadeando enana blanca), con la actual → la siguiente y los saltos que quedan. Avanza con cada salto.
- Atraque en un portanaves: su foto de fondo (fondo_portanaves.jpg o fondo_escuadron.jpg junto a panel.py) y el rótulo TU PORTANAVES / PORTANAVES DE ESCUADRÓN / PORTANAVES.
- PORTANAVES: tu portanaves ya no sale en el sistema del de escuadrón; abajo, el sistema del PORTANAVES DE ESCUADRÓN.
- MENÚ PRINCIPAL abajo en la pantalla de inicio; al atracar se quita el modo combate; SESIÓN TERMINADA 20 s (toca para quitarla); RECOLECTABLE en verde neón; la ficha de nave no enseña valor 0.
# Novedades v0.90c
- El daño del chorro de una estrella de neutrones o enana blanca ya no pone la pantalla en COMBATE.
- Si el destino es un portanaves (marcado en el mapa o la ruta acaba en el sistema del tuyo o del de escuadrón), sale su foto en pequeño en NAVEGACIÓN y en el cuadro 2 de la pantalla grande.
# Novedades v0.91
- Al pedir atraque sale la foto de cada tipo de sitio de fondo: Coriolis, Orbis, Ocellus, Dodec, base asteroide, puesto avanzado, mega nave, puerto y puesto planetario y asentamiento (fondo_*.jpg junto a panel.py).
# Novedades v0.92
- El escáner del sistema, el de superficie y lanzar drones ya no ponen la pantalla en COMBATE.
- Aviso TE ESCANEAN (bodega, delitos, pasajeros...) con quien tengas fijado; en rojo si llevas carga ilegal o robada. Fuera de la zona de no disparar de una estación también activa el modo combate.
- La foto de la estación sale también atracado (más oscura) y en pequeño en la ruta al marcar una estación como destino (tipo sacado de EDSM o de donde ya has estado: estaciones.json junto al sender).
- 5 A PIE: toca «SALUDOS >» arriba a la derecha: los 8 gestos (asígnales tecla en el juego: Gesto 1 a 8).
- Operations: el portanaves de operaciones con su foto (fondo_operaciones.jpg); al atracar en la mega nave, cuenta atrás de 15:00 abajo a la derecha (aviso al último minuto).
- Al embarcar se quita la alerta de escudos de a pie.
- Destino a un portanaves: el tuyo con saldo, gastos aproximados y semanas, servicios, atraque y salto; los de otros, sus servicios de la última vez y si te denegaron el atraque.
# Novedades v0.93
- MERCADO: solo el de la estación donde estás atracado; si no lo has abierto, sus precios de EDSM, o «abre su mercado». En un portanaves alterna cada 10 s con el último mercado de otra estación del sistema.
- AJUSTES > OPCIONES > MERCADO: CON CARGA (de fábrica: en la pantalla grande solo sale si llevas carga; si no, SESIÓN), SIEMPRE o NUNCA.
- Fotos de naves (carpeta naves/ junto a panel.py): de fondo en la ficha a pantalla completa, en pequeño en NAVE y en FLOTA.
- Transporte: 5:20 para subir en estación y 6:00 en un planeta. FPS en verde. Foto del destino más grande.
- NAVEGACIÓN: facción de la estación de destino y tu reputación (HOSTIL en rojo y aviso ¡DESTINO HOSTIL!).
# Novedades v0.94
- 11 RESUMEN DEL DÍA (pestaña DÍA): suma todas las partidas del día (se pone a cero a las 00:00) con la fecha del juego y el tiempo jugado.
- La línea de AMIGOS dice sus nombres.
- Fotos de la nave principal (Inara) de otros CMDR: al fijarlos y en la lista del ESCUADRÓN. Se apagan en OPCIONES > FOTOS CMDR.
- 4 CARGA/MISIÓN se abre en MISIONES si tienes; si no, en BODEGA (y así sale en la pantalla grande).
- BATALLA TERMINADA a pie: al reservar transporte, subir a la nave o tras 2 min sin bajas, resumen de bajas, créditos, duración y consumibles (el juego no dice si ganaste).
# Novedades v0.95
- RESUMEN DEL DÍA: BAJAS a pie · en nave por separado.
- Atracado en la mega nave: el cuadro de GALNET pasa a REGISTRO DE COMBATE.
- Operations: la «Nave de investigación» (masacre en mega nave) sale con la foto de la mega nave; el Runner con la de operaciones.
# Novedades v0.96
- AJUSTES > VERSIONES dice la versión del panel y del sender; si no coinciden, aviso al arrancar.
- Foto de la nave que fijas (NPC o comandante), por su tipo real.
- Dinero sin cobrar: desde cuántos días (RESUMEN DEL DÍA) y aviso al arrancar si son 2 días o más, o más de 50 M.
- Base de ingeniero: aviso al atracar y salta a MATERIALES.
- NAVEGACIÓN: «combustible para ~N saltos» (rojo si quedan menos de 3).
- Interdicción: dice si es COMANDANTE o NPC.
- MINERÍA: toneladas por hora y créditos por hora aproximados. POWERPLAY: méritos de esta semana y cuánto falta para el corte (jueves 9:00).
- Al tocar, el panel responde al momento. Cada 5 minutos apunta en el LOG qué pantallas tardan más en dibujarse.
# Novedades v0.97
- Con misiones activas, el cuadro de la pantalla grande se queda en MISIONES (sin GALNET).
- Ingenieros (38, de nave y de a pie; carpeta ingenieros/ junto a panel.py): al llegar a su sistema, aviso INGENIERO EN EL SISTEMA con tu rango; en NAVEGACIÓN su ficha con cara (y la foto de su base si la marcas como destino), base, planeta y lo que mejora; en NAVEGACIÓN, «ING.» si el destino de la ruta es su sistema.
# Novedades v0.98
- Pantalla HDMI táctil (por ejemplo una de 7" con táctil USB), junto a la pequeña: en modo PANEL se maneja tocando igual que la pequeña; en 4 CUADROS, tocar un cuadro lo abre en grande y una pulsación larga (más de 1 segundo) vuelve a 4 CUADROS. También en AJUSTES > OPCIONES > PANTALLA HDMI.
# Novedades v0.99
- VOZ con Piper (voz natural): carpeta piper/ junto a panel.py con piper/piper y es.onnx. Las frases ya dichas se guardan en piper/cache y suenan al momento. Si no está Piper, se usa espeak-ng.
- La pantalla grande solo pasa a COMBATE en nave con las armas sacadas; al guardarlas se quita (los avisos siguen saliendo).
# Novedades v0.99 (reloj)
- La cuenta atrás de la mega nave usa la hora del PC: funciona aunque el reloj de la Pi vaya mal.
# Novedades v0.99j
- MEGA NAVE a mano: en Operations sale abajo a la derecha el cuadro MEGA NAVE · TOCA (15:00). Al tocarlo empieza la cuenta atrás de 15 minutos; tocarlo otra vez la vuelve a poner en 15:00 (segunda planta). Aviso al último minuto.
# Novedades v0.99k
- Vigilante: si la pantalla se queda congelada más de 45 segundos, el panel apunta en el LOG dónde se atascó («PANEL COLGADO») y se reinicia solo.
# Novedades v1.0 beta 1
- NAVEGACIÓN: la foto del destino es más grande; los datos de encima usan todo el ancho.
- Voz: «cr» se lee «créditos» («2,5 M cr» = 2,5 millones de créditos; «250k cr» = 250 mil créditos).
- Fotos de otros CMDR: su avatar de Inara (si no tiene, la foto de su nave). Se guardan en avatares/.
- Pantalla grande: RAM en % y velocidad de la CPU en MHz junto a la CPU y la temperatura (y en las líneas TIEMPOS del LOG).
- Aviso si el reloj de la Pi no tiene la hora de internet y si queda menos del 10 % de espacio en la tarjeta SD.
- HDMI en modo PANEL: el borde de estado sale una sola vez, alrededor del panel.
- ESCUDOS CAÍDOS ya no se queda puesto al perder el caza o cambiar de nave.
# Novedades v1.0 beta 2
- Pantalla HDMI en modo PANEL: el borde de estado va por el borde exterior de la pantalla.
- 4 CUADROS: los botones de cada cuadro (COMBATE, PIPS...) funcionan al tocarlos. Tocar fuera de un botón abre el cuadro en grande, como antes.
- Los MHz salen en naranja solo si la Pi se está frenando (calor o falta de corriente); bajar a 1200 MHz en reposo es normal.
# Novedades v1.0 beta 3
- Teclas por la red: si la Pi no está enchufada al PC por USB, los botones mandan las teclas por wifi al sender (hace falta el sender v1.0b3).
- VIAJES (pestaña en NAVEGACIÓN y cuadro de la pantalla grande en VIAJE): mapa de tus saltos; la línea es más gruesa cuanto más repites la ruta. 1 SEM / 1 MES / 3 MESES / TODO y ZONA / GALAXIA. Los viajes largos van en una línea con el número de saltos; si se salen del mapa, flecha con el destino y la distancia.
- COMBATE + CAZA: sale al lanzar el caza. Objetivo arriba (escudo, casco y hace cuánto se escaneó), 6 teclas de combate y 6 órdenes al caza. Mientras el caza está fuera, la pantalla grande sigue en COMBATE.
- Pantalla del sistema: hora del último tick del BGS y si el BGS ha cambiado desde tu última visita. Aviso TICK DEL BGS.
- Merc Coin: el «+N» es lo ganado hoy.
- LOG: aviso si el vigilante ha reiniciado el panel hoy.
# Novedades v1.0 beta 4
- COMBATE, COMBATE + CAZA y CAZA con pestañas: se puede abrir cualquiera a mano.
- VIAJES con zoom: tocar el mapa lo amplía x2 donde tocas (hasta x64); el botón − aleja. Con zoom salen más nombres.
- Pantalla del sistema: tick del BGS de ESE sistema con datos de EDCAS (próximo tick con su margen, último tick y gráfica de la hora del tick de los últimos días). Aviso al empezar la ventana. Si EDCAS no tiene datos, el tick general.
- Las alertas ya no cortan el texto: la letra se hace más pequeña o se parte en dos líneas.
- MI FACCIÓN (pestaña FACCIÓN en DÍA y en ESCUADRÓN): todos los sistemas de tu facción, primero los que están en peligro, con influencia, ventaja sobre la 2ª facción, estados, conflictos y cambio desde el dato anterior. Los datos los sube a GitHub la escucha de EDDN. En la pantalla de espera, el recuadro alterna 20 s GALNET y 20 s tu facción.
# Novedades v1.0 beta 5
- Menú: el botón 9 es ahora FACCIÓN. CAZA está dentro de 6 COMBATE (pestañas COMBATE | COMBATE + CAZA | CAZA).
- Pantalla de espera: los datos de la facción en letra más pequeña (caben más sistemas) y con la hora del último dato.
- FACCIÓN: al lado del nombre, la hora de la última actualización en rosa (naranja si tiene más de un día). Tocar un sistema abre su ficha: quién lo controla, todas las facciones con su influencia y estados, Powerplay, seguridad, economía, población y la distancia desde donde estás. Páginas con los botones < >.
# Novedades v1.0 beta 6
- FACCIÓN: estados en colores (verde = buenos, naranja = malos, rojo = guerra, elecciones o retirada), «ZC ×N» si hay zonas de conflicto vistas, y a la derecha cuántos comandantes han pasado hoy (rojo si es el triple de lo normal). Los sistemas en guerra o elecciones salen los primeros y parpadeando.
- Ficha del sistema con tres pestañas: FACCIONES (con los estados de tu facción y qué hacer en los malos), ACTIVIDAD (comandantes por día de la última semana, zonas de conflicto de las últimas 24 h y portanaves vistos) y ZONA (minimapa de 20 al con el Powerplay de alrededor; tocar un sistema tuyo abre su ficha).
- Aviso urgente (rojo, alarma y voz) de guerra, guerra civil y elecciones en tu facción: al aparecer, al arrancar, cada hora mientras juegas y al terminar (ganada o perdida). También aviso de TRÁFICO ALTO si hay mucho movimiento y baja tu influencia. Se apaga en ALERTAS: GUERRA / ELECCIONES DE TU FACCIÓN.
- Necesita la escucha de EDDN nueva (v3) en la Orange Pi.
- 6b: con NITIDEZ ALTA los estados ya no se montan unos sobre otros, ni los nombres de VIAJES, y «ESPERANDO A ELITE DANGEROUS» sale entero.
# Novedades v1.0 beta 7
- Pantalla de espera: 20 s la normal (foto, hora y GALNET) y 20 s una pantalla entera de tu facción, con su logo (logo_faccion.png junto a panel.py), un radar con tus sistemas en su posición (los controlados brillan, los que están en guerra o elecciones parpadean en rojo), un recuadro de ALERTAS, los sistemas controlados con su influencia y una cinta que va pasando con los estados de todos tus sistemas.
# Novedades v1.0 beta 8
- La pantalla de Caballeros de Sion ya no muestra los datos de la Pi (CPU, MHz, temperatura, RAM, FPS).
- PRUEBA: tercera pantalla de espera, ACTIVIDAD GALÁCTICA en directo. Mientras se ve, la Pi escucha EDDN y enciende un destello en cada salto que hace un comandante (naranja si es en tus sistemas). 10 s la galaxia entera y 10 s tu zona. A la derecha: saltos por minuto, comandantes activos, comandantes en tus sistemas hoy y los últimos saltos. Necesita: sudo apt install python3-zmq. En la Pi 3 viene apagada.
# Novedades v1.0 beta 9
- Pantalla de espera: botón FIJAR arriba a la derecha. Deja quieta la pantalla que estás viendo (normal, facción o actividad) sin que deje de moverse ni de actualizarse; el botón pasa a SEGUIR en rojo parpadeando. Con ACTIVIDAD fijada, tocar el mapa cambia entre la galaxia y tu zona. Al entrar al juego se suelta sola. Tocar fuera del botón sigue abriendo el menú.
# Novedades v1.0 beta 10
- Pantalla de espera: el botón FIJAR / SEGUIR es más pequeño y lleva el logo de Elite (negro al girar, con el planeta rojo cuando está fijada).
- Menú 7 EXPLORACIÓN: botones 7 RADAR (pantalla de tu facción) y 8 ACTIVIDAD (EDDN en directo). A pantalla entera; el botón de arriba a la derecha vuelve al menú 7. En RADAR, tocar un sistema abre su ficha; en ACTIVIDAD, tocar el mapa cambia entre galaxia y tu zona.
- Radar de la facción (también en la pantalla de espera): tocar un sistema abre su ficha. Flechas de tendencia de la influencia en los controlados.
- Aviso (con voz) si un sistema controlado baja del 40 % o la segunda facción se acerca a menos de 5 puntos; sale también en ALERTAS del radar.
- Actividad galáctica: encendida por defecto si la Pi tiene python3-zmq (también en la Pi 3). Cuando alguien salta a uno de tus sistemas, el punto brilla y sale «COMANDANTE EN …». Contador de saltos vistos hoy en tus sistemas.
- Ficha del sistema: botón IR. Copia el nombre al portapapeles del PC; en el mapa galáctico, Ctrl+V. Necesita el sender v1.0b5.
- (10c) AJUSTES > OPCIONES: botón FLUJO DATOS EDDN con el estado del escucha (OK y hace cuánto se subió a GitHub; en rojo si lleva más de 7 h sin subir o EDDN está desconectado). Tocarlo da el detalle.
- (10b) Menú 7: el botón < MENÚ vuelve a funcionar.
- Al arrancar, la Pi sincroniza la hora; si no hay NTP, la toma de un servidor web y avisa con HORA CORREGIDA.
# Novedades v1.1.8
- 9 FACCIÓN es ahora un submenú: 1 SISTEMAS, 2 BGS, 3 RADAR, 4 ACTIVIDAD, 5 ESCUADRÓN, 6 AMIGOS, 7 OBJ. COMUNIDAD, 8 RANGOS. SISTEMAS y BGS tienen pestañas para pasar de una a otra, igual que ESCUADRÓN y AMIGOS. El botón < de RADAR y ACTIVIDAD vuelve al menú 9.
- 7 EXPLORACIÓN: solo exploración (EXPLORACIÓN, SISTEMA, EXOBIO, YACIMIENTOS, DIARIO y ALIEN).
- 11 RESUMEN DEL DÍA: pestañas DÍA · GALNET · CALCULADORA.
- 12 AJUSTES: solo ajustes (la calculadora pasa al 11; ROBOT sigue aquí).
# Novedades v1.1.7
- Una sola versión: junta la rama del ROBOT (StackChan, v1.1.2 a v1.1.6) con las novedades de esta.
- MERCADO (y ventana 3): franja roja parpadeante con la bodega llena y naranja «QUEDAN N t» al 95 %. Al llenarse estando atracado suena la compuerta (ALERTAS / SONIDO > BODEGA LLENA).
- MERCADO en tu depósito de construcción: «ENTREGA AQUÍ LOS MATERIALES · N t» en verde parpadeante si llevas carga que le sirve.
- Sonidos propios: interdicción (motor que se para), tu facción gana una guerra o toma el control (tambores), pasajeros entregados (llamada de aeropuerto, con aviso) y construcción terminada (tráiler épico, con aviso). Se quitan en ALERTAS / SONIDO.
- Lista FACCIÓN (menú 9): botón BGS > arriba a la derecha.
# Novedades v1.1.6 a v1.1.2 (ROBOT)
- 12 AJUSTES > ROBOT: la StackChan de M5Stack reacciona a los avisos sin necesitar EMITIR (UDP 5007), enseña las fotos del panel y pone la cara de color con el peligro, la recarga de combustible y a pie.
# Novedades v1.1.1
- NAVEGACIÓN: la lista de RUTA se desplaza (arrastrando o con las flechas) y ya no la tapa la línea de política. Cada salto con sus marcas: NEUTRONES / ENANA BLANCA en rojo, CDSN (y GUERRA, ELECCIONES o RETIRADA si las hay), ANARQUÍA o SEG. BAJA según EDSM. En la cabecera: ETA, hora de llegada y combustible con el que llegas (o «hay que repostar»).
- Tocar un salto de la ruta abre su ficha: estrella, tu facción si está, y los datos de EDSM (o «EDSM NO LO CONOCE · posible primer descubrimiento»). Botón IR para copiarlo en el mapa galáctico.
- Avisos de ruta: PRÓXIMO SALTO enana blanca o estrella de neutrones, QUEDAN 2 SALTOS y al entrar en un sistema CDSN en guerra, elecciones o retirada (se quitan en ALERTAS).
- Pestaña BGS (menú FACCIÓN): la web cdsn-web en el panel, con tarjetas, filtros, orden por columnas y las 11 columnas en la HDMI con NITIDEZ ALTA. Tocar un sistema abre su ficha.
- Ficha del sistema: pestaña INFLUENCIA con la gráfica del histórico (escucha v5) y los últimos cambios.
- RADAR y avisos con las mismas reglas que la web: RETIRADA, VENTAJA BAJA (menos de 5 puntos) y BAJADA (3 puntos o más desde ayer). Flecha de tendencia con el histórico.
- Tick: si EDCAS no responde, se usa el del escucha del pueblo (el sistema mejor medido o el de la galaxia + 24 h).
- RESUMEN DEL DÍA: «DÓNDE COMPRAR HOY» con las estaciones donde has atracado que venden lo que le falta a tu construcción (tocar copia el sistema en el PC).
- Al atracar con una construcción pendiente, la ventana 3 de la pantalla grande enseña MERCADO con lo que se vende para tu colonia aunque lleves la bodega vacía. Si EDSM no responde, el aviso «AQUÍ HAY N MATERIALES» sale con los datos del mercado del juego.
- Arreglado: error del panel nítido con el estilo CABINA al cambiar de pantalla.
- Más rápido: el mapa del SISTEMA dibuja las órbitas unas 10 veces más rápido y el panel arranca antes (guarda las partes ya compiladas).
# Novedades v1.1
- Versión depurada: el mismo panel que la v1.0b20, con el código limpio y repartido en partes (partes/). Se actualiza con la versión completa, sin parches. Necesita el sender v1.0b13.
- COLONIZACIÓN descuenta de la bodega todos los materiales (también los de nombre largo como Equipamiento de supervivencia o Estabilizadores de superficie).
- Aviso al atracar en el depósito: «LLEVAS N t PARA ESTA CONSTRUCCIÓN · descárgalas aquí».
- Aviso en rojo al abrir el mercado fuera del depósito con carga de tu construcción («NO LA VENDAS AQUÍ»), y si la vendes («HAS VENDIDO…»). Se quita en ALERTAS > COLONIA: NO VENDER LA CARGA.
- PASAJEROS: pestaña nueva en 4 CARGA/MISIÓN (número, tipo, VIP, buscados, destino, tiempo y recompensa), en la pantalla grande en lugar de CARGA o VIAJES, avisos al embarcar, al atracar donde se bajan, con menos de 20 minutos y si te escanean con pasajeros buscados. RESUMEN DEL DÍA: pasajeros llevados hoy.
- Tick de cada sistema (con el escucha del pueblo v4): en la ficha del sistema el último tick y el próximo previsto; en el RADAR un reloj azul en los que tienen el tick en la próxima hora.
- CALCULADORA con cinta en AJUSTES > CALCULAR (tocar una línea de la cinta recupera el resultado).
- Reloj LCD de 7 segmentos (gasta mucha menos CPU): AJUSTES > PANTALLA > RELOJ. De entrada AEROPUERTO en la Pi 4 y LCD en la Pi 3.
- En los puertos planetarios el reloj de atraque empieza en 10:00.
- Al entrar en supercrucero, la pantalla grande pasa sola a 4 CUADROS (CAMBIO AUTO > SUPERCRUCERO).
- Sonido de Elite al encender y al apagar el panel (ALERTAS / SONIDO > ENCENDER / APAGAR).
- SESIÓN TERMINADA SIN CRÉDITOS en lugar de «+0 cr».
- ACTIVIDAD GALÁCTICA sin errores, más ligera y sin conectarse y desconectarse de EDDN cada minuto.
# Novedades v1.0 beta 20
- Al cargar la partida, cuando termina la ficha de la nave, la pantalla grande pasa a 4 CUADROS (con una pulsación larga se vuelve al PANEL).
- Nuevo subir_todo.sh: sube todo el proyecto a GitHub (panel, parches, imágenes, los dos senders y el escucha), nunca las claves ni los datos personales.
# Novedades v1.0 beta 19b
- Arreglado el error del RADAR al arrastrar la lista de SISTEMAS CONTROLADOS.
# Novedades v1.0 beta 19
- Voz: lee las abreviaturas completas (toneladas, millones, mil, segundos luz, años luz, metros por segundo, kilómetros, zona de conflicto, comandantes) y no lee los «#23».
- Velocímetro cerca de un planeta (calculado con la latitud y longitud, aproximado): en la nave, reloj de arco junto al altímetro (velocidad sobre el suelo y total; la escala según tu nave; verde lento, naranja normal, rojo rápido). En el SRV y el Rhino, reloj de 0-40 m/s (se amplía solo), km/h y brújula con el rumbo; en 4 CUADROS sustituye al MAPA.
- Aviso BAJANDO RÁPIDO CERCA DEL SUELO (por debajo de 250 m a más de 35 m/s, o de 60 m a más de 15 m/s). Se apaga en ALERTAS.
- Caja negra: si te destruyen, el LOG guarda los últimos 60 s de altura, velocidad vertical y sobre el suelo.
- Avisos repetidos seguidos (p. ej. 14 «te atacan» en un segundo): uno solo, y en el LOG una línea con ×N.
# Novedades v1.0 beta 18
- ACTIVIDAD GALÁCTICA: fondo nuevo (estrellas más brillantes, neblina naranja en los brazos y núcleo iluminado) y tres botones arriba: GALAXIA, COLONIA y SOL (vuestros sistemas salen en SOL). En la espera rota entre las tres; tocar un botón la deja fija.
- Radar de la facción: SISTEMAS CONTROLADOS con todos; con el dedo se sube y baja por la lista (barrita a la derecha). Tocar un sistema abre su ficha.
- COMBATE no se abre por la música en el minuto siguiente a cualquier despegue, y «te atacan» al atracar o despegar avisa sin cambiar de pantalla.
- 11 DÍA: botón BORRAR (dos toques) para poner a cero lo sin cobrar si se ha quedado mal (sender v1.0b12).
- Fotos de fondo del atraque a 80.
# Novedades v1.0 beta 17b
- El cronómetro de salida de la estación empieza en 5:00.
# Novedades v1.0 beta 17
- Fotos de fondo al atracar y aterrizar más claras (oscurecido 75 en lugar de 55).
- COMBATE ya no se abre al despegar: se ignora la música de combate dentro de la estación, durante el primer minuto tras despegar y mientras atracas; la música «Combat_Unknown» solo lo abre si te atacan o sacas las armas. En el LOG queda apuntado cuándo se ignora.
- Avisos de colonización: «AQUÍ HAY N MATERIALES DE COLONIZACIÓN» y «ESTA ESTACIÓN NO TIENE MATERIALES DE COLONIZACIÓN» (o «AQUÍ NO HAY…» al abrir el mercado).
# Novedades v1.0 beta 16b
- Arreglado «Error en esta pantalla» en MERCADO con el recuadro PARA TU COLONIA (sender v1.0b11).
# Novedades v1.0 beta 16
- EMITIR: la memoria ya no sube sin parar (la Pi 3 de KORZO llegaba al 85 %). Como mucho 3 a la vez, los que se atascan se cortan a los 10 s, en la Pi 3 va a 5 imágenes/s y más pequeño, y si el panel pasa del 60 % de la RAM se apaga EMITIR con un aviso.
- Reloj de atraque desde 9:59.
- El cronómetro de salida de la estación y su rótulo van abajo del todo (también en 4 CUADROS).
- ALTÍMETRO de cinta con velocidad vertical (azul bajando, verde subiendo; rojo si bajas rápido cerca del suelo): pestaña en NAVEGACIÓN y, en la pantalla grande, sustituye a un cuadro al acercarte a un planeta, al aterrizar y en los puertos planetarios. Solo sale cuando el juego da la altura. En el SRV apagado (botón SRV: SÍ/NO en la pestaña).
# Novedades v1.0 beta 15
- Reloj de lamas (como los paneles de aeropuerto, sin sonido): TIEMPO PARA ATRACAR desde 9:55 al concederte el atraque (en ESTACIÓN y en ATRAQUE de la pantalla grande). Naranja, amarillo por debajo de 2 min y rojo parpadeando en el último.
- Al despegar dentro de una estación con hangar (Coriolis, Dodecaedro, Orbis, Ocellus, Bernal, base de asteroide): banda DENTRO DE LA ESTACIÓN con la cuenta de 6 minutos (también en 4 CUADROS). Al salir por la ranura se quita y se abre EN VIVO (CAMBIO AUTO > SALIDA DE LA ESTACIÓN).
- Radar de la facción: tocar un sistema de ALERTAS abre su ficha (y VOLVER lleva al radar).
- Avisos de la facción: EXPANSIÓN EN MARCHA / ACTIVA, ¡EXPANSIÓN CONSEGUIDA! (cuando aparece un sistema nuevo) o SIN ÉXITO (3 días sin sistema nuevo), ¡TOMÁIS EL CONTROL! y PERDÉIS EL CONTROL. Se apagan en ALERTAS.
- COLONIZACIÓN > AQUÍ: usa la estación donde estás atracado (los datos del juego si has abierto su mercado; si no, EDSM, y lo dice) y compara las mercancías por su nombre interno.
- Necesita el sender v1.0b11.
# Novedades v1.0 beta 14
- Aviso de compra para tu construcción: al pedir atraque, si esa estación no vende nada de lo que te falta (según EDSM), «ESTA ESTACIÓN NO VENDE NADA DE LO QUE TE FALTA» y dónde probar en el sistema; si vende algo, «AQUÍ HAY N DE LO QUE TE FALTA». Al abrir el mercado se confirma con los datos del juego. Se apaga en ALERTAS. Necesita el sender v1.0b10.
- COLONIZACIÓN > EN EL SISTEMA: ya no se montan los textos de abajo; los datos de EDSM de más de 30 días salen en gris como DATO ANTIGUO (y se prefiere uno reciente si lo hay).
- EN VIVO: el nombre de la nave en azul, como el del copiloto.
# Novedades v1.0 beta 13
- COLONIZACIÓN: lo que llevas en la bodega se descuenta de lo que falta. En azul lo que ya llevas (recogido, sin entregar); «+N» en azul si solo cubre una parte. La barra tiene dos tramos: entregado (naranja) y en bodega (azul).
- Filtros arriba: TODO, AQUÍ (lo que falta y se vende en esta estación) y EN EL SISTEMA (la mejor estación del sistema para cada mercancía, según EDSM: existencias, precio, distancia, pad y antigüedad). EN EL SISTEMA en verde si hay algo, en rojo si no, en gris consultando. Tocar una fila copia la estación al portapapeles del PC. Necesita el sender v1.0b9.
- MERCADO: el recuadro verde ya descuenta tu bodega; tocarlo abre COLONIZACIÓN > AQUÍ.
- Al atracar en el depósito con carga que le sirve: aviso LLEVAS N t PARA ESTA CONSTRUCCIÓN (se apaga en ALERTAS).
# Novedades v1.0 beta 12c
- Pantalla grande en 4 CUADROS: al estar atracado en un sitio de construcción sale el modo COLONIZACIÓN (COLONIZACIÓN, EN VIVO, MERCADO y ESTACIÓN).
# Novedades v1.0 beta 12b
- COLONIZACIÓN ya no la tapa el cambio automático a ESTACIÓN al atracar: espera 3 s y, si otro cambio automático la quita en los 8 s siguientes, vuelve a ella. Si tocas la pantalla, manda lo que tocas.
# Novedades v1.0 beta 12
- COLONIZACIÓN (antes COLONIA) se abre sola al atracar en un sitio de construcción, una vez por atraque: lo detecta por el tipo de estación o al llegar datos del depósito estando atracado o posado. En el LOG queda apuntado cuándo la abre. Necesita el sender v1.0b8.
- La expansión probable ya no sale en el radar; está en la ficha del sistema que se expande, con el destino probable y la distancia.
- ALERTAS y SONIDO: cada botón lleva su número en pequeño (el mismo #n que sale en la esquina del aviso).
# Novedades v1.0 beta 11
- Radar de la facción: «último piloto hace…» (cuándo entró alguien con EDMC en uno de tus sistemas), cuenta atrás del tick de tu sistema principal (EDCAS), halo azul según los comandantes de hoy, anillo blanco que late en los visitados la última hora, línea HOY con comandantes, zonas de conflicto y portanaves, y las EXPANSIONES con una línea roja parpadeante hacia el destino PROBABLE (el sistema conocido más cercano donde no estáis).
- Radar con zoom: botones + y − (hasta x8). Con zoom salen todos los nombres y tocar una zona vacía la centra. Vuelve a x1 cuando deja de verse.
- COLONIA (pestaña de CARGA/MISIÓN): progreso de tu construcción y lo que falta de cada mercancía (en verde lo que se vende en el mercado donde estás, en blanco lo que llevas). Tocar arriba cambia de construcción; tocar la lista pasa de página. Se abre sola al atracar en un depósito (CAMBIO AUTO). Necesita el sender v1.0b7.
- MERCADO: recuadro verde PARA TU COLONIA con lo que se vende allí y le falta a tu construcción.
- VIAJES: botón + para acercar sobre el centro.
- Avisos: número pequeño en la esquina (#23). Tocarlo lleva a su línea en ALERTAS para apagarlo o encenderlo.
# Enlace energético
- Si llevas el enlace energético en la mano y estás parado 8 segundos (girar con el ratón no cuenta), el panel lo da por recarga: aviso pequeño RECARGANDO y punto de recarga (rayo amarillo) en el MAPA, si no hay otro a menos de 20 m.
- El juego no dice la batería del traje ni la munición: es una aproximación.
- Sin pantalla pequeña la HDMI arranca sola en modo PANEL.
# Según tu equipo
- @v Pi 4 con pantalla táctil y cable USB al PC: funciona todo.
- @n Pi 3: todo menos los botones que pulsan teclas (no puede hacer de teclado USB).
- @n Sin pantalla pequeña ni táctil: solo la pantalla grande de datos, sin menús.
"""),
("PANTALLAS", "LAS PANTALLAS", """
# Pantalla del reloj
Sale cuando el juego no envía datos: tu foto, hora, fecha real y del juego, CMDR, versión, IP y noticias GALNET subiendo. Tócala para abrir el menú.
# EN VIVO
Pantalla de inicio durante el juego. Cambia sola según estés en la nave, a pie o en el SRV. MENÚ (arriba a la izquierda) abre los 12 menús.
# Barra de arriba
- Nombre del sistema (o un aviso en rojo).
- Combustible con su barra.
- En la pantalla grande, a la izquierda de la hora, la fecha del juego.
- AJUSTES > PANTALLA > CONSUMO: CPU del panel, temperatura de la Pi y FPS de la pantalla grande (verde, naranja, rojo).
- Pestañas: algunos menús tienen varias páginas (por ejemplo ESTACIÓN | MERCADO | PORTANAVES). Toca una para cambiar.
- @n El engranaje que gira (a la derecha) lleva a AJUSTES desde cualquier pantalla.
- @r Un rayo rojo parpadeando: a la Pi le falta corriente.
# Cambio automático
Con CAMBIO AUTO (OPCIONES) el panel salta solo a la pantalla útil: al atracar, al lanzar el SRV, si te interdictan o te atacan...
- Toca CAMBIO AUTO para elegir uno a uno qué cambios quieres (verde = activo). TODOS ON / TODOS OFF arriba.
"""),
("MENÚS", "LOS 12 MENÚS", """
- 1 MANDOS: tren, luces, visión nocturna, recogedor, supercrucero, silencio, disipador, chaff, salto, escudo y mapas. Se iluminan si están activos.
- 2 PIPS: reparto de energía y combinaciones rápidas.
- 3 NAVEGACIÓN: destino, ruta, sistema (política) y powerplay; toca para cambiar de cara. Pestaña NOTAS: tus sitios guardados.
- 4 CARGA/MISIÓN: bodega y misiones. Pestaña MATERIALES.
- 5 SRV / RHINO / A PIE: botones del vehículo y a pie. Pestaña MAPA: tu recorrido sobre el planeta.
- 6 COMBATE: botones de combate.
- 7 EXPLORACIÓN: exploración (EDSM), sistema en movimiento, exobiología, yacimientos, diario y alienígenas.
- 8 ESTACIÓN: atraque y ficha de la estación. Pestañas MERCADO y PORTANAVES.
- 9 CAZA: órdenes al caza.
- 10 MINERÍA: prospectores y refinado.
- 11 RESUMEN DEL DÍA: todo lo del día (toca para ver AMIGOS). Pestañas GALNET, OBJ.COM y RANGOS.
- 12 AJUSTES: opciones, estilo, bordes, iconos, versiones, LOG, STREAM, PANTALLA, MANUAL y salir / reiniciar / apagar.
@g Los botones de teclas usan las teclas de tu configuración del juego.
"""),
("PANT. GRANDE", "PANTALLA GRANDE (HDMI)", """
Muestra datos (no se toca) y elige sola el tablero según la situación:
- VIAJE: en vivo, navegación, exploración y sistema (en la grande, el SISTEMA sale a todo lo ancho, sin botones y con la ficha del cuerpo más interesante).
- APROXIMACIÓN (cerca de un planeta o anillo): sistema, exobiología y yacimientos.
- SUPERFICIE (aterrizado, SRV o a pie): exobiología, SRV y MAPA del recorrido. En el Rhino: yacimientos y minería.
- ATRACADO: en vivo, estación, mercado y GALNET. GALNET alterna con CARGA/MISIÓN si llevas carga o misiones, y con OBJETIVOS COMUNITARIOS si hay.
- ATRAQUE: la estación a pantalla completa al conceder el atraque. Luz roja a la izquierda y verde a la derecha, como en la entrada de la estación.
- COMBATE: combate, registro de combate y pips.
- COMBATE A PIE: EN VIVO y SRV / RHINO / A PIE a la izquierda y el MAPA a la derecha.
# Modos (AJUSTES > PANTALLA)
- 4 CUADROS: los cuatro a la vez.
- MIXTO: el cuadro principal grande a la izquierda y los demás pequeños.
- GRANDE: un cuadro a pantalla completa con letra al doble; van rotando cada 10 s.
# Nitidez (AJUSTES > PANTALLA)
- NORMAL: los cuadros se dibujan a 480x320 y se amplían (más ligero).
- ALTA: se dibujan a la resolución real de la HDMI (1024x600): letras y líneas nítidas en todos los modos. Gasta algo más de CPU. Si algún cuadro diera problemas, ese cuadro vuelve solo a NORMAL.
Los avisos salen en las dos pantallas.
"""),
("AVISOS", "AVISOS Y SONIDOS", """
Los avisos importantes ocupan la pantalla unos segundos. Toca para quitarlos.
- @r Rojo: peligro (interdicción, te atacan, escudos caídos, casco, sobrecalentamiento, baja tensión).
- @a Azul: información (salto al hiperespacio, códice, noticias).
- @v Verde: buenas noticias (escudos arriba, sistema sin explorar, amigo conectado, objetivo comunitario).
- @n Naranja: atención (recogida de combustible, misión a punto de caducar).
- BAJA (a pie), DERRIBO (nave) y DERRIBO (SRV): número, créditos y lo que llevas sin cobrar. Azul = bono de combate, verde = recompensa. Lo sin cobrar se guarda en el PC hasta que lo cobras (y se pierde si mueres, como en el juego). Total en 11 SESIÓN.
- @r EN COMBATE (a pie): si en el último minuto te han atacado, ha caído tu escudo o has hecho una baja.
- @n SALUD BAJA a pie: avisa al 75 %, y con alarma al 50 % y al 25 %.
- +1 BOTIQUÍN / CÉLULA / GRANADA al cogerlos (llevas N) y USADO al gastarlos; en rojo y con alarma si no te queda ninguno.
- COBRADO: lo que paga el juego y lo que llevaba sumado el panel (la diferencia suele ser de bonos anteriores o extras).
- @r HAS CAÍDO: al morir a pie (en la zona conservas los bonos).
- LLEGADA A (estación) al salir de supercrucero; en las SEÑALES su nivel de AMENAZA (verde 0-2, naranja 3-4, rojo 5 o más) y las zonas de conflicto.
- @n OPERACIÓN INICIADA / TERMINADA (modo Operations): nave, escuadrón y al terminar el resumen con créditos, derribos, Merc Coin y méritos. Las bajas a pie dentro de la nave de carga no las registra el juego.
- GRANADA / PROYECTOR LANZADO: lo que te queda.
- @r ¡DESPLEGADO!: al bajar del transporte en una zona de combate a pie; EN VIVO muestra bajas, ritmo y bonos.
Debajo del nombre del sistema salen los estados del juego: SOBRECALENTADO, INTERDICCION, PELIGRO, COMBUSTIBLE BAJO y MASS LOCK.
# Activar y desactivar (AJUSTES > OPCIONES)
- ALERTAS: los avisos a pantalla completa. Al tocarlo sale la lista de todos los avisos, por páginas: toca cada uno para activarlo o apagarlo (relleno = activo). Un aviso apagado tampoco suena ni lo dice la voz. TODOS ON / TODOS OFF arriba; PÁG pasa de página.
- SONIDO: los pitidos (alarma, salto y "ok"). Al tocarlo sale la lista SONIDO Y VOZ: elige uno a uno qué avisos pitan y hablan (relleno = suena). Uno apagado aquí se sigue viendo, pero en silencio. De entrada BAJA / DERRIBO va en silencio.
- VOZ: que la Pi lea los avisos (ver VOZ).
"""),
("COLORES", "COLORES Y ESTILO", """
- COLOR (OPCIONES): naranja, azul, verde, morado, rojo o blanco. Cambia el color principal del panel.
- ESTILO (AJUSTES): CLÁSICO (limpio) o CABINA: esquinas cortadas, líneas de escaneo, fondo de hexágonos en el espacio y de puntos en tierra, tinte rojo si hay peligro y azul atracado.
- ICONOS (AJUSTES): el menú principal con dibujos en vez de números.
# Qué significa cada color del texto
- @v Verde: bien, activo, completado.
- @r Rojo: peligro o error.
- @a Azul: información.
- @g Gris: sin datos o apagado.
"""),
("BORDES", "BORDES DE SITUACIÓN", """
Con BORDES activado (AJUSTES > BORDES), el marco de las dos pantallas avisa de tu situación. Puede haber hasta 3 a la vez, uno dentro de otro:
- @r Rojo: te buscan o eres hostil, o el casco está por debajo del 30 %.
- @n Naranja (color del tema): sistema anárquico, sin ley.
- @m Marrón: en tierra (a pie en un planeta o en el SRV).
- @a Azul: atracado.
"""),
("VOZ", "VOZ DE LA NAVE", """
Hay dos voces y se pueden usar a la vez. Ninguna repite el mismo aviso en 30 s.
# Voz de la Pi
- AJUSTES > OPCIONES > VOZ. Suena por el altavoz de la Pi (HDMI o jack).
- Usa espeak-ng: {voz}.
- Voz robótica. Solo gasta CPU mientras habla.
# Voz del PC
- Activa EMITIR y abre en el PC: http://{ip}:8080/voz
- Toca una vez para activarla y deja la pestaña abierta (puede estar minimizada).
- Usa las voces de Windows: elige voz, velocidad, tono y volumen y pulsa PROBAR.
- La Pi solo envía el texto: casi no gasta.
"""),
("EMITIR", "EMITIR: PC, OBS Y VR", """
Ver las pantallas del panel en el PC. AJUSTES > OPCIONES > EMITIR (ahora: {emitir}).
- Pantalla grande con voz: http://{ip}:8080
- Pantalla pequeña: http://{ip}:8080/?pequena
- Solo la voz: http://{ip}:8080/voz
- Este manual: http://{ip}:8080/manual
- VLC (solo imagen): http://{ip}:8080/hdmi
# OBS
Fuente Navegador con la dirección. Marca "Controlar audio mediante OBS" para la voz.
# Manejar el panel desde el PC
Con el ratón del PC: clic sobre la imagen = tocar el panel. Funciona con la pantalla pequeña (?pequena) y con la HDMI en modo PANEL.
# Gafas de VR
Abre la página en el PC de juego y colócala en la cabina con Desktop+ (SteamVR).
@g Solo gasta CPU mientras alguien mira la imagen.
"""),
("EXPLORACIÓN", "EXPLORACIÓN Y MÁS", """
- Exobiología (7.3): especies, valor, distancia entre muestras y brújula para volver a la nave. NAVE AQUÍ corrige dónde está la nave.
- Exploración (7.1): cuerpos del sistema con datos de EDSM; toca para pasar páginas.
- Yacimientos (7.4): señales del planeta y anillos.
- Rhino: franja de altura para desplegarlo; en verde (entre 40 y 7 m) está listo.
- Alienígenas (7.6): thargoides y guardianes. Aviso de SISTEMAS APAGADOS.
- MAPA (5 > MAPA): tu recorrido a pie, en SRV o Rhino (rastro naranja), tu posición y rumbo (flecha verde), la nave, el asentamiento (azul), las bajas (cruces rojas) y las muestras (verde). Donde coges un botiquín sale una cruz verde, una célula de energía un rayo amarillo y las granadas un rombo gris. MARCAR RECARGA pone un rayo con aro donde estás (el juego no avisa al recargar el traje ni al coger munición). Norte arriba; la cuadrícula se ajusta sola. Toca para ver todo el recorrido o 100 m a tu alrededor.
- Notas de viaje (3 > NOTAS): GUARDAR AQUÍ guarda el sitio; toca uno para ver distancia y rumbo.
- GALNET (11 > GALNET): noticias oficiales en español cada 30 min. Las nuevas en verde.
- Objetivos comunitarios (11 > OBJ.COM): los tuyos en verde, con tu aportación.
"""),
("PROBLEMAS", "SI ALGO NO VA", """
- SIN DATOS: el sender no envía. En el PC, control del sender > INICIAR. Revisa PI_IP ({ip}) y que el PC y la Pi estén en la misma red.
- Los botones no pulsan teclas: en la Pi 4 el cable USB-C tiene que ir al PC. La Pi 3 no puede hacer de teclado.
- @r Rayo rojo / BAJA TENSIÓN: usa una fuente de 5,1 V y 3 A y alimenta la pantalla HDMI aparte. Ahora: {pot}.
- No suena: mira OPCIONES > SONIDO. Para el sonido por HDMI, en /etc/asound.conf pon la tarjeta de la HDMI (aplay -l).
- La pantalla grande no se ve: la Pi tiene que arrancar sin escritorio (sudo systemctl set-default multi-user.target).
- "Error en esta pantalla": queda apuntado en AJUSTES > LOG y en panel.log.
- Reiniciar el panel: sudo systemctl restart elite-panel
- Salir al shell: AJUSTES > SALIR (dos toques).
"""),
("ACERCA DE", "ACERCA DE", """
# PANEL ELITE
Panel táctil y tablero de datos para Elite Dangerous.
- Versión: {ver}
- Comandante: CMDR {cmdr}
- IP de esta Pi: {ip}
- Alimentación: {pot}
- Voz de la Pi: {voz}
# Creador
@v {creador}
# Desarrollado con
@a Claude (Anthropic)
# Gracias a
EDSM (datos de sistemas) y Frontier Developments (GALNET y objetivos comunitarios).
@g Proyecto no oficial, sin relación con Frontier Developments. Elite Dangerous es una marca de Frontier Developments.
@g La lista de cambios está en AJUSTES > VERSIONES.
"""),
]

def man_vars():
    pot = ("sin datos" if not power.get("ok") else "BAJA AHORA" if power.get("now")
           else "hubo bajadas desde que arrancó" if power.get("past") else "correcta")
    return {"ip": my_ip() or "IP-de-la-Pi", "ver": PANEL_VER, "cmdr": cfg.get("cmdr", ""), "pot": pot,
            "voz": "instalada" if voice_ok() else "NO instalada (sudo apt install espeak-ng)",
            "emitir": "activado" if cfg.get("stream") else "desactivado", "creador": CREADOR}

def man_text(k):
    t = MANUAL[k][2]
    for key, val in man_vars().items():
        t = t.replace("{" + key + "}", str(val))
    return t.strip("\n")

def man_parse(line):
    kind, col = "p", None
    if line.startswith("# "):
        return "h", None, line[2:]
    if line.startswith("- "):
        kind, line = "li", line[2:]
    if line.startswith("@") and len(line) > 1:
        col, line = line[1], line[2:].lstrip()
    return kind, col, line

def man_col(c):
    return {"r": RED, "n": ORANGE, "v": GREEN, "a": BLUE, "m": BROWN, "g": DIM}.get(c, WHITE)

man = {"topic": 0, "page": 0, "cache": None}

def man_pages(k):
    key = (k, man_text(k))
    if man["cache"] and man["cache"][0] == key:
        return man["cache"][1]
    rows = []
    for raw in key[1].split("\n"):
        if not raw.strip():
            rows.append((None, "", None, 0, 6)); continue
        kind, c, txt = man_parse(raw)
        if kind == "h":
            rows.append(("h", txt, ORANGE, 0, 24)); continue
        ind = 12 if kind == "li" else 0
        for j, t in enumerate(wrap_lines(F["small"], txt, W - 20 - ind)):
            rows.append(("li" if kind == "li" and j == 0 else "p", t, man_col(c), ind, 17))
    pages, cur, h = [], [], 0
    avail = H - TOP - 30
    for r in rows:
        if cur and (h + r[4] > avail or (r[0] == "h" and h + 60 > avail)):
            pages.append(cur); cur, h = [], 0
        if not cur and r[0] is None:
            continue
        cur.append(r); h += r[4]
    if cur:
        pages.append(cur)
    man["cache"] = (key, pages)
    return pages

def view_manual(surf, d, flags, now):
    for i, (short, title, _) in enumerate(MANUAL):
        draw_button(surf, grid(i, 4, 3), str(i + 1), short, F["num"], lit=flash.get((140, i), 0) > now)

def view_manual_page(surf, d, flags, now):
    k = man["topic"]
    pages = man_pages(k)
    pg = max(0, min(man["page"], len(pages) - 1))
    y = TOP + 4
    for kind, txt, col, ind, h in pages[pg]:
        if kind == "h":
            put(surf, F["btn"], txt, (8, y + 2), ORANGE, W - 16)
        elif kind:
            if kind == "li":
                pygame.draw.circle(surf, col if col != WHITE else ORANGE, (12, y + 7), 2)
            put(surf, F["small"], txt, (10 + ind, y), col, W - 20 - ind)
        y += h
    pygame.draw.line(surf, DIM, (8, H - 22), (W - 8, H - 22))
    put(surf, F["small"], "< atrás", (8, H - 18), DIM)
    put(surf, F["small"], f"{MANUAL[k][1]}   ·   pág {pg + 1}/{len(pages)}", (W // 2, H - 18), ORANGE, W - 160, anchor="midtop")
    put(surf, F["small"], "sigue >" if pg < len(pages) - 1 else "índice >", (W - 8, H - 18), DIM, anchor="topright")

def tap_manual(x, y):
    if ui["view"] == 140:
        for i in range(len(MANUAL)):
            if grid(i, 4, 3).collidepoint(x, y):
                tap_flash((140, i)); man.update(topic=i, page=0)
                MENU[141] = "MANUAL · " + MANUAL[i][1]; ui["view"] = 141; return
        return
    n = len(man_pages(man["topic"]))
    if x < W // 3:
        if man["page"] == 0:
            ui["view"] = 140
        else:
            man["page"] -= 1
    else:
        if man["page"] >= n - 1:
            ui["view"] = 140
        else:
            man["page"] += 1

def manual_html():
    import html as _h
    C = {"r": "#e03030", "n": "#ff8c00", "v": "#3ad13a", "a": "#50a0ff", "m": "#9a5a28", "g": "#888"}
    out = ["<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Manual del Panel Elite</title>"
           "<style>body{background:#000;color:#ddd;font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:auto;padding:20px;line-height:1.5}"
           "h1,h2,h3{color:#ff8c00}h2{border-bottom:1px solid #a05800;padding-bottom:4px;margin-top:36px}a{color:#ff8c00}"
           "nav a{display:inline-block;margin:3px 10px 3px 0}code{color:#3ad13a}@media print{body{background:#fff;color:#000}}</style></head><body>",
           "<h1>MANUAL DEL PANEL ELITE</h1>",
           "<p>" + _h.escape(PANEL_VER) + " · CMDR " + _h.escape(cfg.get("cmdr", "")) + "</p><nav>"]
    out += [f"<a href='#t{i}'>{i + 1}. {_h.escape(t)}</a>" for i, (_, t, _) in enumerate(MANUAL)]
    out.append("</nav>")
    for i, (_, title, _) in enumerate(MANUAL):
        out.append(f"<h2 id='t{i}'>{i + 1}. {_h.escape(title)}</h2>")
        ul = False
        for raw in man_text(i).split("\n"):
            if not raw.strip():
                continue
            kind, c, txt = man_parse(raw)
            txt = _h.escape(txt)
            txt = re.sub(r"(https?://\S+)", r"<a href='\1'>\1</a>", txt)
            if c:
                txt = f"<span style='color:{C.get(c, '#ddd')}'>{txt}</span>"
            if kind == "li" and not ul:
                out.append("<ul>"); ul = True
            if kind != "li" and ul:
                out.append("</ul>"); ul = False
            out.append(f"<h3>{txt}</h3>" if kind == "h" else f"<li>{txt}</li>" if kind == "li" else f"<p>{txt}</p>")
        if ul:
            out.append("</ul>")
    out.append("</body></html>")
    return "\n".join(out).encode()

VIEWS.update({140: view_manual, 141: view_manual_page})
MENU.update({140: "MANUAL", 141: "MANUAL"})
PARENT.update({140: 12, 141: 140})


# ---------- MAPA de recorrido (a pie, SRV y Rhino sobre un planeta) ----------
track = {"body": None, "pts": [], "kills": [], "items": [], "last": None, "zoom": 0}
YELLOW = (255, 215, 0)
GREY = (150, 150, 150)
ITEM_KIND = {"healthpack": "med", "energycell": "cell"}
FOOT_MAX_V = 20.0                          # m/s: mas rapido que esto, a pie, es ir en el transporte
TRACK_MAX, TRACK_STEP = 2000, 3.0          # puntos guardados como mucho / metros entre puntos

def track_update(d, now):
    b = (d or {}).get("bio") or {}
    lat, lon, R = b.get("lat"), b.get("lon"), b.get("R")
    if lat is None or not R:
        return
    body = (d or {}).get("body") or b.get("body")
    if body != track["body"]:                          # otro planeta: mapa nuevo
        track.update(body=body, pts=[], kills=[], items=[], last=None)
    out = (d.get("Flags2", 0) & 1) or (d.get("Flags", 0) & (1 << 26))
    if not out or d.get("Flags2", 0) & 2:              # en taxi o en el transporte no se apunta
        return
    elink_check(d, now, lat, lon, R)
    raw = track.get("raw")
    if d.get("Flags2", 0) & 1 and not d.get("Flags", 0) & (1 << 26):
        # posicion nueva: la velocidad se mide sobre 1 s como minimo (el juego da la posicion a saltos)
        if raw is None or now - raw[2] >= 1.0:
            if raw is not None and now - raw[2] < 10:
                track["fast"] = hav(raw[:2], (lat, lon), R) / (now - raw[2]) > FOOT_MAX_V
            track["raw"] = (lat, lon, now)
        if track.get("fast"):
            pts_ = track["pts"]
            if pts_ and pts_[-1] is not None:
                k_ = len(pts_)
                while k_ > 0 and pts_[k_ - 1] is not None:
                    k_ -= 1
                if len(pts_) - k_ < 5:
                    del pts_[k_:]                      # trozo suelto de 1-4 puntos: fuera
                if pts_ and pts_[-1] is not None:
                    pts_.append(None)                  # corte: no se une con una raya
            track["last"] = None
            return
    if track["last"] is None or hav(track["last"], (lat, lon), R) >= TRACK_STEP:
        track["pts"].append((lat, lon))
        track["last"] = (lat, lon)
        del track["pts"][:-TRACK_MAX]

ELINK_SECS, ELINK_STILL, ELINK_NEAR = 8.0, 1.0, 20.0    # segundos parado, margen (m), sin otro punto a (m)
ELINK = {"t0": None, "pos": None, "done": False}

def elink_check(d, now, lat, lon, R):
    """Enlace energetico en la mano y parado: recargando (el juego no dice la bateria del traje)."""
    w = str(((d or {}).get("live") or {}).get("weapon") or "").lower()
    holding = d.get("Flags2", 0) & 1 and any(k in w for k in ("rechargetool", "energylink", "enlace"))
    if not holding:
        ELINK.update(t0=None, pos=None, done=False)
        return
    if ELINK["pos"] is None or hav(ELINK["pos"], (lat, lon), R) > ELINK_STILL:
        ELINK.update(t0=now, pos=(lat, lon), done=False)
        return
    if ELINK["done"] or now - ELINK["t0"] < ELINK_SECS:
        return
    ELINK["done"] = True
    near = any(k_ == "recharge" and hav((la, lo), (lat, lon), R) < ELINK_NEAR for k_, la, lo in track["items"])
    if not near:
        track["items"].append(("recharge", lat, lon))
        del track["items"][:-300]
    if ev_on("elink"):
        ui["toast"] = ("RECARGANDO  ·  enlace energético" if near else "PUNTO DE RECARGA GRABADO", now + 4)
        if not near and snd_on("elink"):
            voice_say("Punto de recarga grabado")
            if cfg.get("stream"):
                feed_add("ok", "PUNTO DE RECARGA GRABADO", "")

def draw_toast(surf, now):
    t = ui.get("toast")
    if not t or now > t[1]:
        return
    f = F["small"]
    w_ = f.size(t[0])[0] + 20
    r = pygame.Rect((W - w_) // 2, H - 26, w_, 22)
    pygame.draw.rect(surf, BLACK, r, border_radius=6)
    pygame.draw.rect(surf, YELLOW, r, 1, border_radius=6)
    put(surf, f, t[0], r.center, YELLOW, anchor="center")

def track_item(kind):
    with lock:
        d = state["data"]
    b = (d or {}).get("bio") or {}
    if b.get("lat") is not None:
        track["items"].append((kind, b["lat"], b["lon"]))
        del track["items"][:-300]
        return True
    return False

def track_kill():
    with lock:
        d = state["data"]
    b = (d or {}).get("bio") or {}
    if b.get("lat") is not None:
        track["kills"].append((b["lat"], b["lon"]))
        del track["kills"][:-200]

MAP_STEPS = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000)

def fmt_m(m):
    return f"{m / 1000:g} km".replace(".", ",") if m >= 1000 else f"{m:g} m"

def draw_map(surf, r, d, now):
    d = d or {}
    b = d.get("bio") or {}
    lat, lon, R = b.get("lat"), b.get("lon"), b.get("R")
    fs = F["small"]
    if lat is None or not R:
        put(surf, F["btn"], "Sin posición en un planeta", (r.centerx, r.centery - 10), DIM, r.w - 16, anchor="center")
        put(surf, fs, "El mapa funciona a pie, en SRV o en Rhino sobre un planeta", (r.centerx, r.centery + 12),
            DIM, r.w - 16, anchor="midtop")
        return
    k = math.cos(math.radians(lat))
    def xy(p):
        return (R * math.radians(p[1] - lon) * k, R * math.radians(p[0] - lat))
    trail_all = [xy(p) if p is not None else None for p in track["pts"]]
    trail = [p for p in trail_all if p is not None]
    marks = []
    ship = ship_pos(b)
    if ship:
        marks.append(("ship", xy(ship)))
    sp = (d.get("footcz") or {}).get("spos")
    if sp and (not sp[2] or sp[2] == d.get("body")):
        marks.append(("base", xy(sp)))
    marks += [("kill", xy(p)) for p in track["kills"]]
    marks += [("bio", xy(p)) for p in (b.get("pts") or []) if p]
    marks += [(k_, xy((la, lo))) for k_, la, lo in track["items"]]
    me = (0.0, 0.0)
    zm = track["zoom"] % 3
    if zm == 1:
        minx, maxx, miny, maxy = -100, 100, -100, 100
    elif zm == 0:
        # ZONA: centrado en ti, con lo ultimo que has recorrido y las ultimas bajas (sin puntos lejanos sueltos)
        rec = trail[-150:] + [m[1] for m in marks if m[0] == "kill"][-30:]
        far = [max(abs(p[0]), abs(p[1])) for p in rec]
        far = sorted(f_ for f_ in far if f_ < 1500)
        ext = far[int(len(far) * 0.8)] if far else 40
        ext = max(ext, 40)
        minx, maxx, miny, maxy = -ext, ext, -ext, ext
    else:
        allp = trail + [m[1] for m in marks] + [me]
        minx, maxx = min(p[0] for p in allp), max(p[0] for p in allp)
        miny, maxy = min(p[1] for p in allp), max(p[1] for p in allp)
    w_, h_ = max(maxx - minx, 40), max(maxy - miny, 40)
    cx_, cy_ = (minx + maxx) / 2, (miny + maxy) / 2
    mg = 1.08 if zm == 0 else 1.25
    sc = min(r.w / (w_ * mg), r.h / (h_ * mg))
    def scr(p):
        return (int(r.centerx + (p[0] - cx_) * sc), int(r.centery - (p[1] - cy_) * sc))
    span = max(r.w, r.h) / sc
    step = next((s_ for s_ in MAP_STEPS if span / s_ <= 8), MAP_STEPS[-1])
    old = surf.get_clip()
    surf.set_clip(r)
    gc = tuple(max(18, c // 3) for c in DIM[:3])
    gx = math.floor((cx_ - r.w / 2 / sc) / step) * step
    while scr((gx, 0))[0] <= r.right:
        x = scr((gx, 0))[0]
        pygame.draw.line(surf, gc, (x, r.y), (x, r.bottom))
        gx += step
    gy = math.floor((cy_ - r.h / 2 / sc) / step) * step
    while scr((0, gy))[1] >= r.y:
        y = scr((0, gy))[1]
        pygame.draw.line(surf, gc, (r.x, y), (r.right, y))
        gy += step
    pts = [scr(p) if p is not None else None for p in trail_all] + [scr(me)]
    n = len(pts)
    for i in range(1, n):
        if pts[i - 1] is None or pts[i] is None:
            continue
        f_ = 0.25 + 0.75 * i / n                        # lo antiguo se va apagando
        pygame.draw.line(surf, tuple(int(c * f_) for c in ORANGE[:3]), pts[i - 1], pts[i], 2)
    for kind, p in marks:
        x, y = scr(p)
        if kind == "ship":
            pygame.draw.polygon(surf, ORANGE, [(x, y - 8), (x + 7, y), (x, y + 8), (x - 7, y)])
            put(surf, fs, "NAVE", (x + 10, y - 7), ORANGE)
        elif kind == "base":
            pygame.draw.rect(surf, BLUE, (x - 6, y - 6, 12, 12), 2)
            put(surf, fs, (sp[3] if sp and len(sp) > 3 else "ASENTAMIENTO")[:22], (x + 10, y - 7), BLUE)
        elif kind == "kill":
            pygame.draw.line(surf, RED, (x - 4, y - 4), (x + 4, y + 4), 2)
            pygame.draw.line(surf, RED, (x - 4, y + 4), (x + 4, y - 4), 2)
        elif kind == "med":
            pygame.draw.line(surf, GREEN, (x - 6, y), (x + 6, y), 4)
            pygame.draw.line(surf, GREEN, (x, y - 6), (x, y + 6), 4)
        elif kind == "cell":
            draw_bolt(surf, x - 4, y - 8, YELLOW, 0.75)
        elif kind == "recharge":
            pygame.draw.circle(surf, YELLOW, (x, y), 10, 2)
            draw_bolt(surf, x - 4, y - 8, YELLOW, 0.75)
        elif kind == "gren":
            pygame.draw.polygon(surf, GREY, [(x, y - 4), (x + 4, y), (x, y + 4), (x - 4, y)])
        else:
            pygame.draw.circle(surf, GREEN, (x, y), 4, 2)
    x, y = scr(me)
    a = math.radians(b.get("hdg") or 0)
    tip = (x + 11 * math.sin(a), y - 11 * math.cos(a))
    lft = (x + 7 * math.sin(a - 2.5), y - 7 * math.cos(a - 2.5))
    rgt = (x + 7 * math.sin(a + 2.5), y - 7 * math.cos(a + 2.5))
    pygame.draw.polygon(surf, GREEN, [tip, lft, (x, y), rgt])
    surf.set_clip(old)
    pygame.draw.rect(surf, DIM, r, 1)
    put(surf, fs, ("ZONA", "CERCA (100 m)", "TODO EL RECORRIDO")[track["zoom"] % 3] + "  ·  toca para cambiar",
        (r.x + 6, r.y + 4), DIM, r.w - 120)
    nx = r.right - 12
    pygame.draw.line(surf, WHITE, (nx, r.y + 22), (nx, r.y + 9), 2)
    pygame.draw.polygon(surf, WHITE, [(nx, r.y + 4), (nx - 4, r.y + 11), (nx + 4, r.y + 11)])
    put(surf, fs, "N", (nx - 7, r.y + 6), WHITE, anchor="topright")
    put(surf, fs, f"cuadro = {fmt_m(step)}", (r.x + 6, r.bottom - 18), DIM)
    map_legend(surf, r.x + 8, r.bottom - 29, fs)
    nk = len(track["kills"])
    info = []
    if ship:
        info.append(f"nave a {fmt_m(round(hav((lat, lon), ship, R)))}")
    if nk:
        info.append(f"{nk} bajas")
    if info:
        put(surf, fs, "  ·  ".join(info), (r.right - 6, r.bottom - 18), ORANGE, r.w // 2, anchor="topright")

def map_legend(surf, x, y, fs):
    """Simbolos en pequeno: X baja, + botiquin, rayo celula, rombo nave, cuadro asentamiento."""
    def lab(t, x):
        put(surf, fs, t, (x, y - 7), DIM)
        return x + fs.size(t)[0] + 8
    pygame.draw.line(surf, RED, (x, y - 3), (x + 6, y + 3), 2); pygame.draw.line(surf, RED, (x, y + 3), (x + 6, y - 3), 2)
    x = lab("baja", x + 9)
    pygame.draw.line(surf, GREEN, (x, y), (x + 8, y), 3); pygame.draw.line(surf, GREEN, (x + 4, y - 4), (x + 4, y + 4), 3)
    x = lab("botiquín", x + 11)
    draw_bolt(surf, x, y - 6, YELLOW, 0.55)
    x = lab("célula", x + 9)
    pygame.draw.polygon(surf, ORANGE, [(x + 4, y - 5), (x + 8, y), (x + 4, y + 5), (x, y)])
    x = lab("nave", x + 11)
    pygame.draw.rect(surf, BLUE, (x, y - 4, 8, 8), 2)
    lab("base", x + 11)

MARK_BTN = pygame.Rect(W - 172, H - 38, 166, 34)

def view_map(surf, d, flags, now):
    draw_map(surf, pygame.Rect(4, TOP + 2, W - 8, H - TOP - 46), d, now)
    draw_button(surf, MARK_BTN, "      MARCAR RECARGA", None, F["small"], lit=flash.get(("mark",), 0) > now)
    draw_bolt(surf, MARK_BTN.x + 8, MARK_BTN.y + 7, YELLOW, 0.95)
    nm = sum(1 for k_, *_ in track["items"] if k_ == "med")
    nc = sum(1 for k_, *_ in track["items"] if k_ in ("cell", "recharge"))
    put(surf, F["small"], f"+ botiquines {nm}   ·   rayos {nc}", (8, H - 28), DIM, W - 190)

def tap_map(x=0, y=0):
    if MARK_BTN.collidepoint(x, y):
        if track_item("recharge"):
            tap_flash(("mark",))
            set_alert("PUNTO DE RECARGA MARCADO", "", YELLOW, 1.5, "ok")
        else:
            set_alert("SIN POSICIÓN", "solo en un planeta", secs=2)
        return
    track["zoom"] = (track["zoom"] + 1) % 3

VIEWS[150] = view_map
MENU[150] = "MAPA"
PARENT[150] = 0
TABS.append([(5, "SRV / A PIE"), (150, "MAPA")])


# ---------- RATON Y TECLADO (y HDMI en modo PANEL) ----------
# Clic izquierdo = tocar   ·   clic derecho o TAB = HDMI: PANEL <-> TABLERO   ·   ESC = atras   ·   M = menu   ·   A = ajustes
SMALL = {"null": False}
mouse = {"x": W // 2, "y": H // 2, "t": 0.0}
PANEL_SURF = [None]
MOUSE_SPEED = 0.6

def hdmi_panel():
    return cfg.get("hdmi", "panel" if SMALL["null"] else "tablero") == "panel"

def hdmi_toggle():
    cfg["hdmi"] = "tablero" if hdmi_panel() else "panel"
    save_cfg()

def handle_input(ev, ec):
    now = time.time()
    if ev.type == ec.EV_REL:
        if ev.code == ec.REL_X:
            mouse["x"] = max(0, min(W - 1, mouse["x"] + ev.value * MOUSE_SPEED)); mouse["t"] = now
        elif ev.code == ec.REL_Y:
            mouse["y"] = max(0, min(H - 1, mouse["y"] + ev.value * MOUSE_SPEED)); mouse["t"] = now
    elif ev.type == ec.EV_KEY and ev.value == 1:
        if ev.code == ec.BTN_LEFT:
            mouse["t"] = now
            on_tap(int(mouse["x"]), int(mouse["y"]))
        elif ev.code in (ec.BTN_RIGHT, ec.KEY_TAB):
            hdmi_toggle()
        elif ev.code in (ec.KEY_ESC, ec.KEY_BACKSPACE):
            on_tap(*BACK.center)
        elif ev.code in (ec.KEY_M, ec.KEY_HOME):
            ui["view"] = 0
        elif ev.code == ec.KEY_A:
            ui["view"] = 12

def mouse_loop():
    try:
        from evdev import InputDevice, list_devices, ecodes as ec
    except ImportError:
        return
    import select
    devs = {}
    while True:
        for p in list_devices():
            if p in devs:
                continue
            try:
                d = InputDevice(p)
                caps = d.capabilities()
            except Exception:
                continue
            if is_touch2(d):
                continue                                   # el tactil lo lleva touch_loop
            if ec.EV_REL in caps or ec.KEY_ESC in caps.get(ec.EV_KEY, []):
                devs[p] = d
                print("Raton/teclado:", d.name)
        if not devs:
            time.sleep(5); continue
        try:
            r, _, _ = select.select(list(devs.values()), [], [], 5)
        except (OSError, ValueError):
            devs = {}; continue
        for d in r:
            try:
                for ev in d.read():
                    handle_input(ev, ec)
            except OSError:
                devs = {k: v for k, v in devs.items() if v is not d}

def draw_pointer(surf):
    if time.time() - mouse["t"] > 10:
        return
    x, y = int(mouse["x"]), int(mouse["y"])
    pts = [(x, y), (x, y + 16), (x + 4, y + 12), (x + 8, y + 19), (x + 11, y + 17), (x + 7, y + 11), (x + 12, y + 11)]
    pygame.draw.polygon(surf, WHITE, pts)
    pygame.draw.polygon(surf, BLACK, pts, 1)

def render_big_panel(S):
    hi = panel_hi() if cfg.get("sharp") else None
    if hi is not None:
        S.fill(BLACK)
        S.blit(hi, ((BIG["w"] - hi.get_width()) // 2, (BIG["h"] - hi.get_height()) // 2))
        if cfg.get("perf"):
            perf_side(S)
        return True
    src = PANEL_SURF[0]
    if src is None:
        return False
    bw, bh = BIG["w"], BIG["h"]
    sc = min(bw / W, bh / H)
    size = (int(W * sc), int(H * sc))
    S.fill(BLACK)
    try:
        img = pygame.transform.smoothscale(src, size)
    except ValueError:
        img = pygame.transform.scale(src, size)
    S.blit(img, ((bw - size[0]) // 2, (bh - size[1]) // 2))
    return True


# ---------- v0.71 ----------
TYPE_ES = {"Station": "estación", "Planet": "planeta", "Star": "estrella", "PlanetaryRing": "anillo"}

def threat_col(t):
    return GREEN if t <= 2 else ORANGE if t <= 4 else RED

# EN VIVO en la nave: operacion en curso y Merc Coin
def view_live_v071(surf, d, flags, now):
    if draw_taxi(surf, d or {}, now):
        return
    view_live(surf, d, flags, now)
    d = d or {}
    if d.get("Flags2", 0) & 1 or flags & (1 << 26):
        return
    O = d.get("ops") or {}
    y = H - 20
    if O.get("merc") is not None:
        txt = f"MERC COIN {fnum(O['merc'], 0)}" + (f"  (+{O['lastgain']})" if O.get("lastgain") else "")
        put(surf, F["small"], txt, (8, y), MERC)
    c_ = (O.get("crew") or {})
    if c_.get("paid"):
        put(surf, F["small"], f"copiloto {c_.get('name', '')}: -{crx(c_['paid'])} cr", (W - 8, y), (70, 120, 230), 240, anchor="topright")
    if O.get("on"):
        mins = int((now - (O.get("t0") or now)) // 60)
        put(surf, F["small"], f"OPERACIÓN · {O.get('target') or O.get('mission') or ''} · {O.get('kills', 0)} derribos · "
                              f"{crx(O.get('cr', 0))} cr · {mins} min", (8, y - 18), RED, W - 16)

# SISTEMA en la pantalla grande: sin botones, mapa a todo lo ancho y ficha automatica
ORR_XS = [1.0]

def or_side_big(surf, d, orbits):
    d = d or {}
    want = [((d.get("dest") or {}).get("name")), d.get("body")]
    o = next((x for w_ in want if w_ for x in orbits if x.get("name") == w_), None)
    if o is None:
        cand = [x for x in orbits if x.get("name") and not x.get("mapped")]
        o = max(cand, key=lambda x: x.get("value") or 0, default=None)
    put(surf, F["small"], SPEEDS[orr["speed"]][1] + ("  ·  PAUSA" if orr["paused"] else ""), (W - 6, H - 16), DIM, anchor="topright")
    if not o:
        return
    system = (d.get("explo") or {}).get("system") or ""
    nm = o["name"]
    short = nm[len(system):].strip() if system and nm.startswith(system) else nm
    box = pygame.Rect(W - 168, TOP + 4, 162, 74)
    pygame.draw.rect(surf, BLACK, box)
    pygame.draw.rect(surf, DIM, box, 1, border_radius=4)
    put(surf, F["btn"], short or nm, (box.x + 6, box.y + 3), ORANGE, box.w - 12)
    put(surf, F["small"], o.get("cls", ""), (box.x + 6, box.y + 22), bcol(o), box.w - 12)
    put(surf, F["small"], f"{o.get('dist', 0):,} ls".replace(",", "."), (box.x + 6, box.y + 38), DIM)
    put(surf, F["small"], ("1º " if o.get("first") else "") + ("MAPEADO" if o.get("mapped") else ""), (box.right - 6, box.y + 38), GREEN, anchor="topright")
    put(surf, F["small"], f"~ {cr(o.get('value'))} cr", (box.x + 6, box.y + 54), ORANGE)

def view_orrery_big(surf, d, flags, now):
    global OR_AREA, draw_or_side
    keep = (OR_AREA, draw_or_side, orr.get("hits"), orr.get("scale"))
    OR_AREA = pygame.Rect(0, TOP, W, H - TOP)
    draw_or_side = or_side_big
    ORR_XS[0] = (W / 2 - 14) / max(1, (H - TOP) / 2 - 14)
    orr["scale"] = None
    try:
        view_orrery(surf, d, flags, now)
    finally:
        OR_AREA, draw_or_side, orr["hits"], orr["scale"] = keep
        ORR_XS[0] = 1.0

# clic del raton del PC sobre la pagina de EMITIR
def remote_tap(x, y, w, h, which):
    if (w, h) == (W, H) or which == "p":
        px, py = x * W / max(1, w), y * H / max(1, h)
    else:
        if not hdmi_panel():
            return
        sc = min(w / W, h / H)
        px, py = (x - (w - W * sc) / 2) / sc, (y - (h - H * sc) / 2) / sc
    if 0 <= px < W and 0 <= py < H:
        mouse.update(x=px, y=py, t=time.time())
        on_tap(int(px), int(py))

VIEWS[100] = view_live_v071


# ---------- v0.72: NITIDEZ ALTA (dibujar los cuadros de la pantalla grande a su tamano real) ----------
# Las pantallas siguen pensando en 480x320; ScaledSurf traduce posiciones, tamanos y letras al tamano real.
HI_IDS, HI_KEEP, _HIF, _HISURF = set(), [], {}, {}

class FontProxy:
    def __init__(self, real, f):
        self.real, self.f = real, f
    def size(self, text):
        w, h = self.real.size(text)
        return (int(w / self.f + 0.5), int(h / self.f + 0.5))
    def render(self, *a, **k):
        t = self.real.render(*a, **k)
        HI_IDS.add(id(t)); HI_KEEP.append(t)
        return t
    def get_linesize(self):
        return int(self.real.get_linesize() / self.f + 0.5)
    def get_height(self):
        return int(self.real.get_height() / self.f + 0.5)
    def __getattr__(self, n):
        return getattr(self.real, n)

def hi_fonts(f):
    mono = pygame.font.match_font("dejavusansmono") or pygame.font.match_font("monospace")
    out = {}
    for k, base in (("big", 30), ("btn", 24), ("small", 18), ("num", 48), ("clock", 110), ("mono", 11), ("tiny", 15)):
        size = max(6, int(round(base * f)))
        if (k, size) not in _HIF:
            _HIF[(k, size)] = pygame.font.Font(mono if k == "mono" else None, size)
        out[k] = FontProxy(_HIF[(k, size)], size / base)
    return out

class ScaledSurf:
    def __init__(self, real, sx, sy):
        self.real, self.sx, self.sy, self.clip = real, sx, sy, None
    def _r(self, r):
        r = pygame.Rect(r)
        return pygame.Rect(int(r.x * self.sx), int(r.y * self.sy), max(0, int(round(r.w * self.sx))), max(0, int(round(r.h * self.sy))))
    def get_size(self):
        return (W, H)
    def get_width(self):
        return W
    def get_height(self):
        return H
    def get_rect(self, **k):
        r = pygame.Rect(0, 0, W, H)
        for a, v in k.items():
            setattr(r, a, v)
        return r
    def fill(self, color, rect=None, special_flags=0):
        return self.real.fill(color, None if rect is None else self._r(rect), special_flags)
    def blit(self, src, dest, area=None, special_flags=0):
        x, y = dest[0], dest[1]
        pos = (int(x * self.sx), int(y * self.sy))
        if id(src) in HI_IDS:                      # texto ya dibujado a tamano real
            return self.real.blit(src, pos, area, special_flags)
        w, h = src.get_size()
        size = (max(1, int(w * self.sx)), max(1, int(h * self.sy)))
        try:
            sc = pygame.transform.smoothscale(src, size)
        except ValueError:
            sc = pygame.transform.scale(src, size)
        return self.real.blit(sc, pos, None if area is None else self._r(area), special_flags)
    def set_clip(self, r=None):
        self.clip = None if r is None else pygame.Rect(r)
        self.real.set_clip(None if r is None else self._r(r))
    def get_clip(self):
        return self.clip or pygame.Rect(0, 0, W, H)
    def set_at(self, pos, c):
        self.real.fill(c, self._r((pos[0], pos[1], 1, 1)))
    def get_at(self, pos):
        return self.real.get_at((int(pos[0] * self.sx), int(pos[1] * self.sy)))
    def __getattr__(self, n):
        return getattr(self.real, n)

def _hw(s_, w):
    return w if not w or w <= 0 else max(1, int(round(w * min(s_.sx, s_.sy))))

def _hp(s_, p):
    return (p[0] * s_.sx, p[1] * s_.sy)

def _wrap_draw():
    D = pygame.draw
    def mk(name, fn):
        def w(surf, *a, **k):
            if not isinstance(surf, ScaledSurf):
                return fn(surf, *a, **k)
            s_, a = surf, list(a)
            m = min(s_.sx, s_.sy)
            if name in ("rect", "ellipse", "arc"):
                a[1] = s_._r(a[1])
                wi = 4 if name == "arc" else 2
                if len(a) > wi:
                    a[wi] = _hw(s_, a[wi])
                if name == "rect" and len(a) > 3:
                    a[3] = int(a[3] * m)
            elif name in ("line", "aaline"):
                a[1], a[2] = _hp(s_, a[1]), _hp(s_, a[2])
                if name == "line" and len(a) > 3:
                    a[3] = _hw(s_, a[3])
            elif name in ("lines", "aalines"):
                a[2] = [_hp(s_, p_) for p_ in a[2]]
                if name == "lines" and len(a) > 3:
                    a[3] = _hw(s_, a[3])
            elif name == "polygon":
                a[1] = [_hp(s_, p_) for p_ in a[1]]
                if len(a) > 2:
                    a[2] = _hw(s_, a[2])
            elif name == "circle":
                a[1] = _hp(s_, a[1])
                a[2] = max(1, a[2] * m)
                if len(a) > 3:
                    a[3] = _hw(s_, a[3])
            if "width" in k:
                k["width"] = _hw(s_, k["width"])
            if "border_radius" in k:
                k["border_radius"] = int(k["border_radius"] * m)
            return fn(s_.real, *a, **k)
        return w
    for n in ("rect", "ellipse", "arc", "line", "aaline", "lines", "aalines", "polygon", "circle"):
        setattr(D, n, mk(n, getattr(D, n)))

_wrap_draw()

def big_cell_draw(cell, fn, d, flags, now):
    cell.fill(BLACK)
    try:
        if fn:
            fn(cell, d, flags, now)
    except Exception as e:
        put(cell, F["small"], f"error: {e}"[:60], (8, TOP + 8), RED)

def hi_cell(S, fn, d, flags, now, area, how):
    sx, sy = area.w / W, area.h / (H - TOP)
    if how != "fill":
        sx = sy = min(sx, sy)
    size = (int(W * sx) + 2, int(H * sy) + 2)
    real = _HISURF.get(size)
    if real is None:
        real = _HISURF[size] = pygame.Surface(size)
    real.fill(BLACK)
    keep = dict(F)
    HI_IDS.clear(); HI_KEEP.clear()
    F.update(hi_fonts(min(sx, sy)))
    try:
        fn(ScaledSurf(real, sx, sy), d, flags, now)
    except Exception as e:
        log_exc("nitidez alta", e)
        return False
    finally:
        F.clear(); F.update(keep)
        HI_IDS.clear(); HI_KEEP.clear()
    cw, ch = int(W * sx), int((H - TOP) * sy)
    top_ = int(TOP * sy)
    sub = real.subsurface((0, top_, min(cw, real.get_width()), min(ch, real.get_height() - top_)))
    if how == "fill":
        S.blit(sub, area.topleft)
    else:
        y = area.y if how == "top" else area.centery - ch // 2
        S.blit(sub, (area.centerx - cw // 2, y))
    return True

# 12 AJUSTES > PANTALLA: MODO, NITIDEZ y FPS
def view_pantalla(surf, d, flags, now):
    f = cfg.get("bigfps", "AUTO")
    items = [("MODO", BIGMODES.get(cfg.get("bigmode", "4"), "4 CUADROS"), False),
             ("NITIDEZ", "ALTA" if cfg.get("sharp") else "NORMAL", bool(cfg.get("sharp"))),
             ("FPS", "AUTO (3/10)" if f == "AUTO" else f"{f} por seg.", False),
             ("CONSUMO", "SÍ" if cfg.get("perf") else "NO", bool(cfg.get("perf"))),
             ("RELOJ", clock_style() + ("" if cfg.get("reloj") else " (auto)"), False)]
    for i, (t, sub, fill) in enumerate(items):
        draw_button(surf, grid(i, 3, 2, TOP, H - 40), t, sub, F["big"], filled=fill, lit=flash.get((160, i), 0) > now)
    perf_update()
    x = 8
    for j, (t, col) in enumerate(perf_parts()):
        x += put(surf, F["btn"], t, (x, H - 32), col) + 14
    put(surf, F["small"], "pantalla grande", (W - 8, H - 26), DIM, anchor="topright")

def tap_pantalla(x, y):
    for i in range(5):
        if not grid(i, 3, 2, TOP, H - 40).collidepoint(x, y):
            continue
        tap_flash((160, i))
        if i == 0:
            order = list(BIGMODES)
            cfg["bigmode"] = order[(order.index(cfg.get("bigmode", "4")) + 1) % len(order)]
        elif i == 1:
            cfg["sharp"] = not cfg.get("sharp", True)
        elif i == 2:
            cfg["bigfps"] = BIGFPS[(BIGFPS.index(cfg.get("bigfps", "AUTO")) + 1) % len(BIGFPS)]
        elif i == 3:
            cfg["perf"] = not cfg.get("perf", False)
        else:                                            # RELOJ: AEROPUERTO <-> LCD
            cfg["reloj"] = "LCD" if clock_style() == "AEROPUERTO" else "AEROPUERTO"
        save_cfg()
        return

VIEWS[160] = view_pantalla
MENU[160] = "PANTALLA"
PARENT[160] = 12


