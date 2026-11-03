p = "/home/ortem/panel.py"
s = open(p, encoding="utf-8").read()
old = "    draw_emblem(surf, W // 2, 110, 70, now)\n"
if old not in s:
    print("NO ENCONTRADO"); raise SystemExit
s = s.replace(old, '''    img = cmdr_img()
    if img:
        r = img.get_rect(center=(W // 2, 105))
        surf.blit(img, r)
        pygame.draw.rect(surf, ORANGE, r.inflate(6, 6), 2, border_radius=4)
    else:
        draw_emblem(surf, W // 2, 110, 70, now)
''', 1)
open(p, "w", encoding="utf-8").write(s)
print("OK")
