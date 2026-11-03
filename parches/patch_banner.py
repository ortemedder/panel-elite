import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak30")
s = open(p, encoding="utf-8").read()
if "def rhino_banner" in s:
    print("ya estaba"); raise SystemExit
ok = True
def rep(old, new):
    global s, ok
    if old not in s:
        print("NO ENCONTRADO:", old.strip()[:70]); ok = False; return
    s = s.replace(old, new, 1)
SNIP = r'''# ---------- aviso RHINO PREPARADO (7-40 m) en las dos pantallas ----------
RB_FONTS = {}

def rhino_ready():
    with lock:
        d, rx = state["data"], state["rx"]
    if not d or time.time() - rx > 5:
        return None
    flags, f2 = d.get("Flags", 0), d.get("Flags2", 0)
    if flags & ((1 << 26) | 1 | 2) or f2 & 1:            # en SRV, atracado, aterrizado o a pie
        return None
    if not flags & (1 << 21) or flags & (1 << 29):       # sin altitud real sobre el terreno
        return None
    L = d.get("live") or {}
    alt, rh = L.get("alt"), (L.get("ship") or {}).get("rhino")
    if alt is not None and 7 <= alt <= 40 and rh in ("A BORDO", "HANGAR"):
        return alt
    return None

def rhino_banner(surf):
    alt = rhino_ready()
    if alt is None:
        return
    w, h = surf.get_size()
    bh = max(58, h // 7)
    r = pygame.Rect(0, h - bh, w, bh)
    on = int(time.time() * 2) % 2 == 0
    pygame.draw.rect(surf, RED if on else (130, 0, 0), r)
    pygame.draw.rect(surf, WHITE, r, 3)
    size = int(bh * 0.8)
    if size not in RB_FONTS:
        RB_FONTS[size] = (pygame.font.Font(None, size), pygame.font.Font(None, max(18, size // 2)))
    fb, fs = RB_FONTS[size]
    img = fb.render("RHINO PREPARADO", True, WHITE)
    surf.blit(img, img.get_rect(center=(r.centerx - w // 14, r.centery)))
    a = fs.render(f"{alt:.0f} m", True, WHITE)
    surf.blit(a, a.get_rect(midright=(r.right - 12, r.centery)))

'''
rep("def render(surf):", SNIP + "def render(surf):")
rep("            decorate(surf)\n", "            decorate(surf)\n            rhino_banner(surf)\n")
rep("        render_big()\n", '        render_big()\n        rhino_banner(BIG["surf"])\n')
rep('''            if real and alt <= 30:
                lab, acol = "RHINO OK", GREEN
            elif real and alt <= 60:
                lab, acol = "BAJA A 30 m", ORANGE''', '''            if real and 7 <= alt <= 40:
                lab, acol = "RHINO OK", GREEN
            elif real and alt < 7:
                lab, acol = "SUBE A 7 m", ORANGE
            elif real and alt <= 80:
                lab, acol = "BAJA A 40 m", ORANGE''')
s, n = re.subn(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.30 · 29/10/2026 02:00"', s, count=1)
if ok:
    open(p, "w", encoding="utf-8").write(s); print("OK")
else:
    print("No he cambiado nada")
