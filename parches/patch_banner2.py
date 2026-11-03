import shutil, re
p = "/home/ortem/panel.py"
shutil.copy(p, p + ".bak31")
s = open(p, encoding="utf-8").read()
NEW = r'''def rhino_ready():
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
    if alt is not None and alt <= 100 and rh in ("A BORDO", "HANGAR"):
        return alt
    return None

def rhino_banner(surf):
    alt = rhino_ready()
    if alt is None:
        return
    now = time.time()
    if alt > 40:
        col, txt = (255, 80, 0), "BAJA PARA EL RHINO"
    elif alt >= 7:
        col, txt = (0, 170, 60), "RHINO PREPARADO"
    else:
        col = (255, 0, 0) if int(now * 4) % 2 == 0 else (60, 0, 0)
        txt = "DEMASIADO BAJO"
    w, h = surf.get_size()
    bh = max(58, h // 7)
    r = pygame.Rect(0, h - bh, w, bh)
    pygame.draw.rect(surf, col, r)
    pygame.draw.rect(surf, WHITE, r, 3)
    size = int(bh * 0.8)
    if size not in RB_FONTS:
        RB_FONTS[size] = (pygame.font.Font(None, size), pygame.font.Font(None, max(18, size // 2)))
    fb, fs = RB_FONTS[size]
    img = fb.render(txt, True, WHITE)
    surf.blit(img, img.get_rect(center=(r.centerx - w // 14, r.centery)))
    a = fs.render(f"{alt:.0f} m", True, WHITE)
    surf.blit(a, a.get_rect(midright=(r.right - 12, r.centery)))

'''
s, n = re.subn(r'def rhino_ready\(\):.*?(?=def render\(surf\):)', lambda m: NEW, s, count=1, flags=re.S)
if not n:
    print("NO ENCONTRADO (aplica antes patch_banner.py)"); raise SystemExit
s = re.sub(r'PANEL_VER = ".*"', 'PANEL_VER = "v0.31 · 29/10/2026 02:10"', s, count=1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
