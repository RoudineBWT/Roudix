"""Convertit une icône colorée (Tela / Papirus) dans le style Roudix : recoloration duotone (brun -> orange -> crème)
du SVG d'origine, puis insertion dans la tuile Roudix. Tout reste vectoriel."""
import re, colorsys

NAMED = {"white":"#ffffff","black":"#000000","red":"#ff0000","green":"#008000","blue":"#0000ff","yellow":"#ffff00",
         "gray":"#808080","grey":"#808080","orange":"#ffa500","purple":"#800080","silver":"#c0c0c0","lime":"#00ff00",
         "navy":"#000080","teal":"#008080","maroon":"#800000","olive":"#808000","aqua":"#00ffff","fuchsia":"#ff00ff","pink":"#ffc0cb"}

# rampe de luminance -> couleurs Roudix
RAMPS = {
 "dark":  [(0.00,"#2e1d12"),(0.22,"#7a3a16"),(0.45,"#e0661a"),(0.66,"#ff8c42"),(0.85,"#ffc878"),(1.00,"#fff1dc")],
 "light": [(0.00,"#4a2a16"),(0.22,"#94491a"),(0.45,"#d9601a"),(0.66,"#ff8c42"),(0.85,"#ffc878"),(1.00,"#fff6e8")],
}
def _hex2rgb(h):
    h=h.lstrip("#")
    if len(h)==3: h="".join(c*2 for c in h)
    return tuple(int(h[i:i+2],16) for i in (0,2,4))
def _lerp(a,b,t): return tuple(round(a[i]+(b[i]-a[i])*t) for i in range(3))
def ramp_color(L, variant):
    stops=RAMPS[variant]
    L=max(0.0,min(1.0,L))
    for (p0,c0),(p1,c1) in zip(stops,stops[1:]):
        if L<=p1:
            t=0 if p1==p0 else (L-p0)/(p1-p0)
            r,g,b=_lerp(_hex2rgb(c0),_hex2rgb(c1),t)
            return f"#{r:02x}{g:02x}{b:02x}"
    return stops[-1][1]
def _luma(rgb):
    r,g,b=rgb
    y=(0.299*r+0.587*g+0.114*b)/255.0
    # un peu de saturation compte comme "plus sombre/plus chaud" : évite que les couleurs vives tombent toutes au même ton
    return y

PROP = r"(?P<prop>fill|stroke|stop-color|flood-color|lighting-color|color)"
VAL  = r"(?P<val>#[0-9a-fA-F]{8}|#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgba?\([^)]*\)|[a-zA-Z]+)"
RE_ATTR  = re.compile(PROP + r'(?P<sep>\s*=\s*")' + VAL + r'(?P<end>")')
RE_STYLE = re.compile(PROP + r'(?P<sep>\s*:\s*)' + VAL)

def recolor(svg, variant="dark"):
    def conv(val):
        v=val.strip()
        low=v.lower()
        if low in ("none","currentcolor","inherit","transparent") or low.startswith("url("): return None
        if low in NAMED: v=NAMED[low]
        if v.startswith("#"):
            rgb=_hex2rgb(v[:7] if len(v)>=7 else v)
        elif low.startswith("rgb"):
            nums=[float(x.strip().rstrip("%")) for x in re.findall(r"[\d.]+%?",v)[:3]]
            rgb=tuple(round(n) for n in nums)
        else:
            return None
        return ramp_color(_luma(rgb), variant)
    def rep_attr(m):
        c=conv(m.group("val"))
        return m.group(0) if c is None else f'{m.group("prop")}{m.group("sep")}{c}{m.group("end")}'
    def rep_style(m):
        c=conv(m.group("val"))
        return m.group(0) if c is None else f'{m.group("prop")}{m.group("sep")}{c}'
    svg=RE_ATTR.sub(rep_attr,svg)
    svg=RE_STYLE.sub(rep_style,svg)
    return svg

def split_svg(svg):
    """-> (viewBox tuple, contenu interne, defs globaux) ; gère les SVG sans viewBox (width/height)."""
    svg=re.sub(r"<\?xml[^>]*\?>","",svg)
    svg=re.sub(r"<!--.*?-->","",svg,flags=re.S)
    svg=re.sub(r"<!DOCTYPE[^>]*>","",svg)
    m=re.search(r"<svg\b([^>]*)>",svg,flags=re.S)
    attrs=m.group(1)
    inner=svg[m.end():svg.rindex("</svg>")]
    vb=re.search(r'viewBox\s*=\s*"([^"]+)"',attrs)
    if vb:
        x,y,w,h=[float(t) for t in re.split(r"[\s,]+",vb.group(1).strip())]
    else:
        w=float(re.sub(r"[^\d.]","",re.search(r'\bwidth\s*=\s*"([^"]+)"',attrs).group(1)) or 48)
        h=float(re.sub(r"[^\d.]","",re.search(r'\bheight\s*=\s*"([^"]+)"',attrs).group(1)) or 48)
        x=y=0.0
    return (x,y,w,h), inner

def prefix_ids(inner, pre):
    ids=set(re.findall(r'\bid="([^"]+)"',inner))
    for i in ids:
        inner=inner.replace(f'id="{i}"',f'id="{pre}{i}"')
        inner=inner.replace(f'url(#{i})',f'url(#{pre}{i})').replace(f"url('#{i}')",f"url('#{pre}{i}')")
        inner=inner.replace(f'href="#{i}"',f'href="#{pre}{i}"')
    return inner

def inline_style_ids(inner,pre):
    return inner

def clean(svg):
    """Retire métadonnées Inkscape/Sodipodi & co (inutiles, et leurs préfixes ne seraient plus déclarés)."""
    svg=re.sub(r"<metadata\b.*?</metadata>","",svg,flags=re.S)
    svg=re.sub(r"<sodipodi:[^>]*?/>","",svg,flags=re.S)
    svg=re.sub(r"<sodipodi:([\w-]+)\b[^>]*>.*?</sodipodi:\1>","",svg,flags=re.S)
    svg=re.sub(r'\s(?:inkscape|sodipodi|xmlns:[\w-]+|sketch|serif|i|x):[\w.-]+\s*=\s*"[^"]*"',"",svg)
    svg=re.sub(r'\sxmlns(:[\w-]+)?\s*=\s*"[^"]*"',"",svg)
    svg=re.sub(r"<(?:inkscape|rdf|cc|dc):[^>]*?/>","",svg,flags=re.S)
    svg=re.sub(r"<((?:inkscape|rdf|cc|dc):[\w-]+)\b[^>]*>.*?</\1>","",svg,flags=re.S)
    svg=re.sub(r"\s+"," ",svg)
    return svg.strip()

def import_inner(path, variant, uid):
    """Lit un SVG Tela/Papirus -> (viewBox, contenu recoloré Roudix) ou None si inutilisable."""
    raw=open(path,encoding="utf-8").read()
    if len(raw)>70000: return None
    vb,inner=split_svg(raw)
    inner=clean(inner)
    inner=prefix_ids(recolor(inner,variant),f"i{uid}_")
    return vb,inner
