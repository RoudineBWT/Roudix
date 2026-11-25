import sys, os, io, cairosvg
from PIL import Image, ImageDraw
out=sys.argv[1]; cell=84
BG={'Roudix':(20,16,13),'Roudix-Light':(251,245,238)}
def sheet(v, items, cols, fn):
    rows=(len(items)+cols-1)//cols
    im=Image.new('RGB',(cols*cell+12,rows*cell+12),BG[v])
    for i,p in enumerate(items):
        png=cairosvg.svg2png(url=p,output_width=72,output_height=72)
        t=Image.open(io.BytesIO(png)).convert('RGBA')
        im.paste(t,(6+(i%cols)*cell+6,6+(i//cols)*cell+6),t)
    im.save(fn); print(fn, im.size)
for v in BG:
    b=f'{out}/{v}/scalable'
    real=lambda d,pref=None:[f'{b}/{d}/{f}' for f in sorted(os.listdir(f'{b}/{d}')) if f.endswith('.svg') and not os.path.islink(f'{b}/{d}/{f}')]
    items=real('places')+real('mimetypes')+real('devices')+real('categories')
    sheet(v,items,13,f'{out}/preview-system-{v.lower()}.png')
    gen=[p for p in real('apps') if 'roudix-generic' in p]
    sheet(v,gen,13,f'{out}/preview-generic-{v.lower()}.png')
