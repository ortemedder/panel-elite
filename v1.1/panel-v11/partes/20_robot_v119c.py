# Panel Elite v1.1 · parte 20: arreglos del ROBOT (v1.1.9c)
#   El rótulo de las fotos (estación, nave, logo) lo pinta el panel dentro de la foto, con letra buena y tildes:
#   en la pantalla del robot salía ilegible. El robot v1.1.9c ya no pinta el suyo si la foto viene rotulada.
SC_ROT = {}                                    # foto -> (título, dato) del último envío

def _rot_txt(font, t, maxw):
    if font.size(t)[0] <= maxw:
        return t
    while t and font.size(t + "…")[0] > maxw:
        t = t[:-1]
    return t.rstrip() + "…"

def sc_foto_rotulada(f):
    import io
    base = sc_foto_jpg(f)
    tit, dat = SC_ROT.get(f, ("", ""))
    if not base or not (tit or dat):
        return base
    k = ("rot", f, tit, dat)
    if k in SC_FOTO["cache"]:
        return SC_FOTO["cache"][k]
    img = pygame.image.load(io.BytesIO(base), "foto.jpg")
    w, h = img.get_size()
    fh = 46 if dat else 28
    pygame.draw.rect(img, (0, 0, 0), (0, h - fh, w, fh))
    pygame.draw.line(img, (255, 140, 0), (0, h - fh), (w, h - fh), 2)
    ft, fd = pygame.font.Font(None, 24), pygame.font.Font(None, 20)
    img.blit(ft.render(_rot_txt(ft, tit, w - 12), True, (255, 140, 0)), (6, h - fh + 5))
    if dat:
        img.blit(fd.render(_rot_txt(fd, dat, w - 12), True, (255, 255, 255)), (6, h - fh + 25))
    b = io.BytesIO()
    pygame.image.save(img, b, "foto.jpg")
    data = b.getvalue()
    if len(SC_FOTO["cache"]) > 20:
        SC_FOTO["cache"].clear()
    SC_FOTO["cache"][k] = data
    return data

def sc_foto(f, titulo, dato, seg=6):
    sc_foto_srv()
    if sc_foto_file(f):
        SC_ROT[f] = (titulo or "", dato or "")
        sc_send({"t": "foto", "f": f, "port": SC_FOTO_PORT, "titulo": titulo or "", "dato": dato or "", "seg": seg, "rot": True})
