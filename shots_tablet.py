#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screenshots App Store / Google Play --- FORMAT TABLETTE 2064 x 2752.
(le format mobile a son propre script : shots_mobile.py)

    python shots_tablet.py config.json
    python shots_tablet.py config.json --lang fr_FR --out out

TOUS LES REGLAGES SONT DANS LE DICTIONNAIRE `LAYOUT` CI-DESSOUS.
Chacun peut etre surcharge depuis le config.json, du plus general au plus precis :

    LAYOUT (ce fichier)
      <- cfg["layout"]      : toutes les langues, tous les ecrans
      <- cfg["tablet"]      : ce format uniquement
      <- screen["layout"]   : un ecran precis
      <- screen["tablet"]   : un ecran precis, ce format uniquement

Exemple dans config.json :

    "tablet": { "title": { "size": 210, "y": 90 } },
    "screens": { "fr_FR": [
        { "img": "assets/fr_FR/01.jpg", "headline": "Dicte", "sub": "A la voix",
          "layout": { "title":  { "color": "#FFFFFF" },
                      "mockup": { "w": 980, "radius": 70 } } } ] }

--- PARAMETRES ------------------------------------------------------------
Blocs "title" et "subtitle" :
  x            "center", "left", "right" ou une position en px
  y            position du HAUT DES CAPITALES en px, ou "auto" (= colle sous le
               bloc precedent, a `gap` px : utile si le titre passe sur 2 lignes)
  gap          ecart avec le bloc precedent quand y vaut "auto"
  size         taille de la police
  font         "bold" | "medium" | "regular" | chemin direct vers un .ttf
  color        "#RRGGBB"
  align        "center" | "left" | "right"
  max_width    largeur maxi en px (null = largeur de l'image - 2 x margin)
  shrink       true : reduit la taille si le texte deborde
  wrap         true : passe a la ligne au lieu de reduire
  tracking     interlettrage en px (accepte les valeurs negatives)
  line_height  multiplicateur d'interligne pour le multi-ligne
  uppercase    true : passe le texte en majuscules
  shadow       null ou {"color": "#00000055", "blur": 12, "offset": [0, 4]}
  Un saut de ligne s'ecrit \\n dans le texte du config.json.

Bloc "mockup" :
  x            "center" ou position en px du bord gauche
  y            "bottom" (colle au bas), "auto" (sous le texte, a `gap` px),
               ou une position en px
  gap          ecart avec le texte quand y vaut "auto"
  w            largeur du cadre en px
  h            hauteur en px, ou "auto" (calculee sur le ratio de la capture)
  fit          "cover"   : remplit l'ecran, proportions gardees -> peut rogner
               "stretch" : remplit l'ecran exactement, deforme un peu, rien n'est
                           coupe et il n'y a aucune bande
               "contain" : capture entiere, proportions gardees, bandes sur les cotes
  buttons      true : dessine les boutons lateraux (volume, silencieux, veille)
  frame        chemin d'un PNG de device telecharge, dont l'ECRAN EST TRANSPARENT :
               la capture y est inseree automatiquement (radius/border/buttons
               sont alors ignores, le PNG fait tout)
  radius       rayon des coins : un nombre de px, un pourcentage ("5%"), ou
               "iphone" (14 % de la largeur), "ipad" (4,5 %), "android" (9 %),
               "ipad-old" (2 %), "square" (0)
  border       epaisseur de la bordure en px
  color        couleur de la bordure du mockup (alias : border_color)
  shadow       null ou {"color": "#00000055", "blur": 40, "offset": [0, 25]}
  crop_bottom  true : le mockup peut depasser sous le bas de l'image

Bloc "background" :
  colors       ["#depart", "#arrivee"] (une seule couleur = aplat)
  direction    "vertical" | "horizontal"
  image        chemin d'une image commune, decoupee en tranches egales entre
               les ecrans d'une meme langue (le fond se raccorde d'une capture
               a l'autre sur la fiche du store)

Captures : "img" pour les deux formats, ou "img_mobile" / "img_tablet" quand
tu as des captures differentes par format (un seul config.json suffit alors).

Polices : "font_bold", "font_medium", "font_regular" a la racine du config.json,
et une police par langue quand l'alphabet l'exige :

    "fonts": {
      "ru": { "bold": "fonts/NotoSans-Bold.ttf",   "regular": "fonts/NotoSans-Regular.ttf" },
      "zh": { "bold": "fonts/NotoSansSC-Bold.otf", "regular": "fonts/NotoSansSC-Regular.otf" }
    }

Le script previent quand un caractere du texte n'existe pas dans la police.
Dependance : Pillow.
"""
import argparse, json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEVICE = "tablet"

# =============================================================================
# REGLAGES PAR DEFAUT DU FORMAT TABLETTE
# =============================================================================
LAYOUT = {
    "width": 2064,
    "height": 2752,
    "margin": 120,                      # marge de securite laterale

    "background": {
        "colors": ["#FBD9F2", "#DCEBFF"],
        "direction": "vertical",
        "image": None,
    },

    "title": {
        "x": "center", "y": 150, "size": 300, "font": "bold",
        "color": "#111114", "align": "center", "max_width": None,
        "shrink": True, "wrap": False, "tracking": 0, "line_height": 1.05,
        "uppercase": False, "shadow": None, "gap": 30,
    },

    "subtitle": {
        "x": "center", "y": 520, "size": 150, "font": "regular",
        "color": "#111114", "align": "center", "max_width": None,
        "shrink": True, "wrap": False, "tracking": 0, "line_height": 1.15,
        "uppercase": False, "shadow": None, "gap": 30,
    },

    "mockup": {
        "x": "center", "y": "bottom", "w": 993, "h": 2074,
        "fit": "cover", "radius": "ipad", "border": 12, "border_color": "#101014",
        "shadow": None, "crop_bottom": False, "gap": 60,
    },
}

# Polices de secours si le config.json n'en fournit pas.
FONT_DIRS = ["C:/Windows/Fonts", "~/AppData/Local/Microsoft/Windows/Fonts",
             "/System/Library/Fonts", "/Library/Fonts", "~/Library/Fonts",
             "/usr/share/fonts", "."]
FALLBACK = {
    "bold": ["Poppins-Bold", "Inter-Bold", "segoeuib", "arialbd", "DejaVuSans-Bold"],
    "medium": ["Poppins-Medium", "Inter-Medium", "segoeui", "arial", "DejaVuSans"],
    "regular": ["Poppins-Regular", "Inter-Regular", "segoeui", "arial", "DejaVuSans"],
}


# =============================================================================
# OUTILS
# =============================================================================
def deep_merge(base, over):
    """Fusion recursive : `over` gagne, `base` n'est pas modifie."""
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def hexa(c):
    """'#RRGGBB' ou '#RRGGBBAA' -> tuple RGBA."""
    c = str(c).lstrip("#")
    if len(c) == 6:
        c += "ff"
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4, 6))


def system_font(kind):
    """Cherche une police du systeme (Windows / macOS / Linux)."""
    for name in FALLBACK.get(kind, FALLBACK["regular"]) + ["*"]:
        for folder in FONT_DIRS:
            folder = Path(folder).expanduser()
            if folder.is_dir():
                for ext in ("ttf", "otf"):
                    hit = next(folder.rglob(f"{name}.{ext}"), None)
                    if hit:
                        return str(hit)
    sys.exit("Aucune police trouvee : renseigne font_bold / font_regular dans le config.")


def load_font(spec, size, fonts):
    """`spec` = 'bold' / 'medium' / 'regular' (du config) ou un chemin direct."""
    path = fonts.get(spec, spec)
    return ImageFont.truetype(str(path), max(1, int(round(size))))


def cover(im, w, h):
    """Remplit (w, h) puis recadre au centre."""
    k = max(w / im.width, h / im.height)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h)).convert("RGBA")


def contain(im, w, h, fill=(255, 255, 255, 255)):
    """Capture entiere dans (w, h), centree, sans recadrage."""
    k = min(w / im.width, h / im.height)
    small = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), fill)
    out.paste(small, ((w - small.width) // 2, (h - small.height) // 2))
    return out


def rounded(size, radius):
    """Masque aux coins arrondis, lisse par surechantillonnage x4."""
    w, h = size
    big = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(big).rounded_rectangle((0, 0, w * 4 - 1, h * 4 - 1),
                                          max(0, round(radius)) * 4, fill=255)
    return big.resize((w, h), Image.LANCZOS)


def fit_shot(im, w, h, mode):
    """Insere la capture dans l'ecran selon `fit` :

    "cover"   : remplit l'ecran en gardant les proportions -> peut rogner
    "stretch" : remplit l'ecran EXACTEMENT, quitte a deformer un peu
                -> tout le contenu de la capture est visible, sans bande
    "contain" : capture entiere, proportions gardees -> bandes sur les cotes
    """
    if mode == "stretch":
        return im.resize((max(1, w), max(1, h)), Image.LANCZOS).convert("RGBA")
    if mode == "contain":
        return contain(im, w, h)
    return cover(im, w, h)


def screen_mask(frame):
    """Masque de l'ecran dans un PNG de device : la zone transparente INTERIEURE.

    On marque d'abord tout le transparent qui touche un bord (= l'exterieur du
    device), ce qui ne laisse que le trou de l'ecran.
    """
    a = frame.getchannel("A").point(lambda v: 255 if v < 16 else 0)
    w, h = a.size
    px = a.load()
    for x in range(w):
        for y in (0, h - 1):
            if px[x, y] == 255:
                ImageDraw.floodfill(a, (x, y), 0)
    for y in range(h):
        for x in (0, w - 1):
            if px[x, y] == 255:
                ImageDraw.floodfill(a, (x, y), 0)
    return a


_FRAMES = {}


def device_png(path, shot, fit):
    """Insere la capture dans un PNG de device (ecran = zone transparente)."""
    path = str(path)
    if path not in _FRAMES:
        fr = Image.open(path).convert("RGBA")
        mask = screen_mask(fr)
        if not mask.getbbox():
            sys.exit(f"{path} : aucun ecran transparent detecte. Utilise un PNG de "
                     f"device dont l'ecran est transparent (fond damier dans l'apercu).")
        _FRAMES[path] = (fr, mask)
    frame, mask = _FRAMES[path]
    x0, y0, x1, y1 = mask.getbbox()
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    inner = fit_shot(shot, x1 - x0, y1 - y0, fit)
    layer.paste(inner, (x0, y0))
    layer.putalpha(mask)                 # la capture n'existe que dans l'ecran
    layer.alpha_composite(frame)         # le device par-dessus
    return layer


def side_buttons(frame, fw, fh, bump, color, radius):
    """Boutons lateraux : volume + silencieux a gauche, veille a droite."""
    d = ImageDraw.Draw(frame)
    r = max(1, bump // 2)
    for y0, y1, left in ((0.140, 0.175, True),     # silencieux
                         (0.205, 0.285, True),     # volume +
                         (0.300, 0.380, True),     # volume -
                         (0.250, 0.360, False)):   # veille
        top, bot = round(fh * y0), round(fh * y1)
        box = (0, top, bump * 2, bot) if left else (fw - bump * 2, top, fw, bot)
        d.rounded_rectangle(box, radius=r, fill=color)


RADIUS_PRESETS = {                 # en proportion de la largeur du cadre
    "iphone": 0.14,                # ~55,6 pt pour 393 pt de large
    "ios": 0.14,
    "auto": 0.14,
    "android": 0.09,
    "ipad": 0.045,                 # les coins d'une tablette sont bien moins ronds
    "tablet": 0.045,
    "ipad-old": 0.02,              # iPad a bordures droites (Air 2, mini 4...)
    "square": 0.0,
}


def corner_radius(value, width):
    """Rayon des coins : un nombre de px, un mot-cle ("iphone", "ipad",
    "android", "square") ou un pourcentage de la largeur du cadre ("14%")."""
    if isinstance(value, str):
        key = value.lower().strip()
        if key in RADIUS_PRESETS:
            return width * RADIUS_PRESETS[key]
        if key.endswith("%"):
            return width * float(key[:-1]) / 100
        sys.exit(f'radius "{value}" inconnu. Valeurs possibles : '
                 f'{", ".join(RADIUS_PRESETS)}, un pourcentage ("5%") ou un nombre.')
    return float(value)


def background(cfg, w, h):
    """Degrade vertical ou horizontal, ou aplat si une seule couleur."""
    colors = cfg.get("colors") or ["#FFFFFF"]
    a, b = hexa(colors[0]), hexa(colors[-1])
    n = h if cfg.get("direction", "vertical") == "vertical" else w
    strip = Image.new("RGBA", (1, n) if n == h else (n, 1))
    px = strip.load()
    for i in range(n):
        t = i / max(1, n - 1)
        col = tuple(round(x + (z - x) * t) for x, z in zip(a, b))
        px[(0, i) if n == h else (i, 0)] = col
    return strip.resize((w, h), Image.BILINEAR)


def slice_bg(path, n, w, h):
    """Decoupe une image de fond en n tranches de w x h qui se raccordent.

    L'image est mise a l'echelle UNE SEULE FOIS sur la largeur totale (n x w)
    avant d'etre coupee : c'est ce qui garantit la continuite du fond d'une
    capture a la suivante.
    """
    band = cover(Image.open(path).convert("RGB"), n * w, h)
    return [band.crop((i * w, 0, (i + 1) * w, h)) for i in range(n)]


def shadow_layer(size, shape, pos, cfg):
    """Calque d'ombre portee a la taille de l'image."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    dx, dy = cfg.get("offset", [0, 0])
    layer.paste(shape, (pos[0] + int(dx), pos[1] + int(dy)), shape)
    return layer.filter(ImageFilter.GaussianBlur(float(cfg.get("blur", 20))))


try:                                   # Pillow compile avec Raqm ? (arabe/hebreu)
    from PIL import features as _pil_features
    HAS_RAQM = bool(_pil_features.check("raqm"))
except Exception:
    HAS_RAQM = False

_RTL = re.compile("[\u0590-\u08FF\uFB1D-\uFDFF\uFE70-\uFEFF]")
_RTL_WARNED = set()


def shape_rtl(text):
    """Arabe / hebreu : lie les lettres et remet le texte dans l'ordre visuel.

    Quand Pillow est compile avec Raqm, il le fait tout seul et on ne touche a
    rien. Sinon (cas des roues Windows recentes), on le fait en amont avec
    arabic-reshaper + python-bidi :  pip install arabic-reshaper python-bidi
    """
    if HAS_RAQM or not text or not _RTL.search(text):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        if "rtl" not in _RTL_WARNED:
            _RTL_WARNED.add("rtl")
            print("   ! texte arabe/hebreu et Pillow sans Raqm : les lettres vont rester "
                  "detachees.  ->  pip install arabic-reshaper python-bidi")
        return text


_FONT_CACHE = {}


def resolve_fonts(cfg, root, lang=None):
    """Polices a utiliser pour une langue donnee.

    Par defaut : "font_bold" / "font_medium" / "font_regular" a la racine du
    config. Une langue peut imposer les siennes, ce qui est indispensable pour
    le russe, le chinois, le japonais, le coreen ou l'arabe :

        "fonts": {
          "ru": { "bold": "fonts/NotoSans-Bold.ttf",
                  "regular": "fonts/NotoSans-Regular.ttf" }
        }
    """
    if lang in _FONT_CACHE:
        return _FONT_CACHE[lang]
    per_lang = (cfg.get("fonts") or {}).get(lang) or {}
    out = {}
    for kind in ("bold", "medium", "regular"):
        spec = per_lang.get(kind) or cfg.get(f"font_{kind}")
        path = str(root / spec) if spec else None
        if not path or not Path(path).exists():
            if spec:
                print(f"   ! [{lang}] police {kind} introuvable ({spec}), "
                      f"remplacee par une police systeme.")
            path = system_font(kind)
        out[kind] = path
    _FONT_CACHE[lang] = out
    return out


def check_glyphs(text, font, lang, where):
    """Previent si la police ne contient pas les caracteres du texte.

    Un caractere absent est dessine avec le glyphe ".notdef" (une case barree) :
    on compare donc le rendu de chaque caractere a celui d'un code volontairement
    inexistant.
    """
    if not text:
        return
    n = max(8, int(font.size * 2))

    def rendu(ch):
        im = Image.new("L", (n, n), 0)
        ImageDraw.Draw(im).text((n // 4, n // 4), ch, font=font, fill=255)
        return im.tobytes()

    ref = rendu("\ue000")
    manquants = [c for c in dict.fromkeys(text) if c.strip() and rendu(c) == ref]
    if manquants:
        print(f"   ! [{lang}] {where} : la police ne contient pas "
              f"{' '.join(manquants)}  ->  ajoute une police pour cette langue : "
              f'"fonts": {{ "{lang}": {{ "bold": "...", "regular": "..." }} }}')


# =============================================================================
# TEXTE
# =============================================================================
def line_width(font, text, tracking):
    return font.getlength(text) + tracking * max(0, len(text) - 1)


def wrap_lines(text, font, tracking, max_w):
    """Retour a la ligne glouton."""
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}".strip()
            if line and line_width(font, trial, tracking) > max_w:
                out.append(line)
                line = word
            else:
                line = trial
        out.append(line)
    return out


def draw_line(d, x, y, text, font, fill, tracking, align):
    """Dessine une ligne ; `x` est deja le point d'ancrage horizontal."""
    w = line_width(font, text, tracking)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if not tracking:
        d.text((x, y), text, font=font, fill=fill, anchor="la")
        return
    for ch in text:                      # interlettrage : caractere par caractere
        d.text((x, y), ch, font=font, fill=fill, anchor="la")
        x += font.getlength(ch) + tracking


def draw_text(img, text, cfg, fonts, W, margin, prev_bottom=0, lang="", where=""):
    """Dessine un bloc de texte. Retourne le y du bas du bloc.

    `y` peut valoir "auto" : le bloc se place alors juste sous le precedent,
    a `gap` pixels (pratique quand le titre passe sur plusieurs lignes).
    """
    if not text:
        return prev_bottom
    if cfg.get("uppercase"):
        text = text.upper()
    text = shape_rtl(text)                 # arabe/hebreu : liaison des lettres

    max_w = cfg.get("max_width") or (W - 2 * margin)
    tracking = cfg.get("tracking", 0)
    size = cfg["size"]
    font = load_font(cfg["font"], size, fonts)

    if cfg.get("wrap"):
        lines = wrap_lines(text, font, tracking, max_w)
    else:
        lines = text.split("\n")
        while cfg.get("shrink") and size > 10 and \
                max(line_width(font, l, tracking) for l in lines) > max_w:
            size -= 2
            font = load_font(cfg["font"], size, fonts)

    check_glyphs(text, font, lang, where)   # alphabet couvert par la police ?

    d = ImageDraw.Draw(img)
    # y demande = haut des CAPITALES : on mesure le vide au-dessus sur un "H"
    cap = d.textbbox((0, 0), "H", font=font, anchor="la")[1]
    ascent, descent = font.getmetrics()
    lh = round((ascent + descent) * cfg.get("line_height", 1.1))
    x = W // 2 if cfg["x"] == "center" else (margin if cfg["x"] == "left" else
                                             (W - margin if cfg["x"] == "right" else cfg["x"]))
    align = cfg.get("align", "center")
    fill = hexa(cfg["color"])
    y_top = prev_bottom + cfg.get("gap", 24) if cfg["y"] == "auto" else cfg["y"]
    y0 = y_top - cap

    sh = cfg.get("shadow")
    if sh:                                # ombre : meme texte, floute, decale
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        dx, dy = sh.get("offset", [0, 4])
        for i, line in enumerate(lines):
            draw_line(ld, x + dx, y0 + i * lh + dy, line, font,
                      hexa(sh.get("color", "#00000055")), tracking, align)
        img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(float(sh.get("blur", 10)))))

    for i, line in enumerate(lines):
        draw_line(d, x, y0 + i * lh, line, font, fill, tracking, align)
    return y0 + (len(lines) - 1) * lh + ascent + descent


# =============================================================================
# MOCKUP
# =============================================================================
BUMP_RATIO = 0.008          # depassement des boutons lateraux, en % de la largeur


def draw_mockup(img, shot_path, cfg, W, H, text_bottom, name=""):
    shot = Image.open(shot_path).convert("RGB")
    fw = float(cfg["w"])
    border = max(0, round(cfg.get("border", 0)))
    buttons = bool(cfg.get("buttons"))

    def total_height(width):
        """Hauteur du cadre pour que la capture tienne SANS ETRE ROGNEE.

        On part de la largeur de l'ecran, c'est-a-dire la largeur demandee
        moins le depassement des boutons et moins la bordure.
        """
        bump = round(width * BUMP_RATIO) if buttons else 0
        screen_w = width - 2 * bump - 2 * border
        return screen_w * shot.height / shot.width + 2 * border

    auto = str(cfg["h"]) == "auto"
    fh = total_height(fw) if auto else float(cfg["h"])

    if cfg["y"] == "bottom":
        top = H - fh
    elif cfg["y"] == "auto":                  # juste sous le texte
        top = text_bottom + float(cfg.get("gap", 40))
    else:
        top = float(cfg["y"])

    if not cfg.get("crop_bottom"):        # on garde le mockup entier dans l'image
        limit = H - max(text_bottom, 0)   # hauteur disponible sous le texte
        if fh > limit:
            print(f"   ! {name} : mockup reduit ({round(fh)} -> {round(limit)} px de haut) "
                  f"pour ne pas chevaucher le texte.")
            fw, fh = fw * limit / fh, limit
        top = min(top, H - fh) if cfg["y"] == "bottom" else top
        if cfg["y"] == "bottom":
            top = H - fh

    fw = round(fw)
    if auto:                             # ratio exact apres l'arrondi de la largeur
        fh = total_height(fw)
        if cfg["y"] == "bottom":
            top = H - fh
    fh, top = round(fh), round(top)
    left = (W - fw) // 2 if cfg["x"] == "center" else round(cfg["x"])
    radius = round(corner_radius(cfg.get("radius", 0), fw))
    color = hexa(cfg.get("color") or cfg.get("border_color") or "#101014")

    if cfg.get("frame"):                 # --- PNG de device telecharge ---------
        frame = device_png(cfg["frame"], shot, cfg.get("fit", "cover"))
        frame = frame.resize((fw, round(fw * frame.height / frame.width)), Image.LANCZOS)
        fh = frame.height
        if cfg["y"] == "bottom":
            top = H - fh
    else:                                # --- cadre dessine -------------------
        bump = round(fw * BUMP_RATIO) if buttons else 0
        bw = fw - 2 * bump               # largeur du corps, boutons compris
        frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        if bump:
            side_buttons(frame, fw, fh, bump, color, radius)
        body = Image.new("RGBA", (bw, fh), color)
        body.putalpha(rounded((bw, fh), radius))
        frame.alpha_composite(body, (bump, 0))
        iw, ih = max(1, bw - 2 * border), max(1, fh - 2 * border)
        inner = fit_shot(shot, iw, ih, cfg.get("fit", "cover"))
        inner.putalpha(rounded((iw, ih), max(0, radius - border)))
        frame.alpha_composite(inner, (bump + border, border))

    if cfg.get("shadow"):
        img.alpha_composite(shadow_layer(img.size, frame, (left, top), cfg["shadow"]))
    img.paste(frame, (left, top), frame)


# =============================================================================
# ASSEMBLAGE
# =============================================================================
def make(screen, shot, layout, fonts, bg_slice=None, lang=""):
    W, H, margin = layout["width"], layout["height"], layout["margin"]
    img = bg_slice.copy() if bg_slice is not None else background(layout["background"], W, H)
    img = img.convert("RGBA")

    y = draw_text(img, screen.get("headline", ""), layout["title"], fonts, W, margin,
                  lang=lang, where="titre")
    y = draw_text(img, screen.get("sub", ""), layout["subtitle"], fonts, W, margin, y,
                  lang=lang, where="sous-titre")

    draw_mockup(img, shot, layout["mockup"], W, H, y, name=shot.name)
    return img.convert("RGB")             # les stores refusent la transparence


def main():
    p = argparse.ArgumentParser(description=f"Screenshots {DEVICE}.")
    p.add_argument("config", help="Fichier JSON de configuration.")
    p.add_argument("--lang", "-l", action="append", help="Limiter a une ou des langues.")
    p.add_argument("--out", "-o", help="Dossier de sortie.")
    a = p.parse_args()

    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    root = Path(a.config).parent
    out_dir = root / (a.out or cfg.get("out", "out"))

    # Reglages : LAYOUT <- cfg["layout"] <- cfg["tablet"]
    base = deep_merge(deep_merge(LAYOUT, cfg.get("layout", {})), cfg.get(DEVICE, {}))
    # Compatibilite : "background_image" et "bg" a la racine du config
    if cfg.get("background_image"):
        base["background"]["image"] = cfg["background_image"]
    if cfg.get("bg"):
        base["background"]["colors"] = cfg["bg"]
    if cfg.get("color"):
        base["title"]["color"] = base["subtitle"]["color"] = cfg["color"]

    W, H = base["width"], base["height"]
    for lang, screens in cfg["screens"].items():
        if a.lang and lang not in a.lang:
            continue
        fonts = resolve_fonts(cfg, root, lang)      # police propre a la langue
        bg_img = base["background"].get("image")
        parts = slice_bg(root / bg_img, len(screens), W, H) if bg_img else None

        n = 0
        for i, s in enumerate(screens):
            # "img_tablet": null -> cette capture n'existe pas sur ce format
            if f"img_{DEVICE}" in s and not s[f"img_{DEVICE}"]:
                print(f"IGNORE {s['img']} : pas de version {DEVICE}")
                continue
            # une capture par format si besoin : "img_tablet", sinon "img"
            rel = s.get(f"img_{DEVICE}") or s["img"]
            shot = root / rel
            if not shot.exists():
                here = sorted(q.name for q in shot.parent.iterdir()
                              if q.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")) \
                    if shot.parent.is_dir() else []
                print(f"IGNORE {rel} : introuvable. Dans {shot.parent} : "
                      + (", ".join(here) if here else "aucune image"))
                continue

            # Reglages de l'ecran : ... <- screen["layout"] <- screen["tablet"]
            layout = deep_merge(deep_merge(base, s.get("layout", {})), s.get(DEVICE, {}))
            if s.get("bg") and not parts:
                layout["background"]["colors"] = s["bg"]
            if layout["mockup"].get("frame"):        # chemin relatif au config.json
                layout["mockup"]["frame"] = root / layout["mockup"]["frame"]

            img = make(s, shot, layout, fonts, parts[i] if parts else None, lang)
            n += 1
            f = out_dir / DEVICE / lang / f"{n:02d}.png"
            f.parent.mkdir(parents=True, exist_ok=True)
            img.save(f)
            print("OK", f, img.size)


if __name__ == "__main__":
    main()