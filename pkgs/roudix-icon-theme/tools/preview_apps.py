import sys, os, io, cairosvg
from PIL import Image
out=sys.argv[1]; cell=84; cols=14
BG={'Roudix':(20,16,13),'Roudix-Light':(251,245,238)}
for v,bg in BG.items():
    d=f'{out}/{v}/scalable/apps'
    files=sorted(f for f in os.listdir(d) if not os.path.islink(f'{d}/{f}') and not f.startswith('roudix-'))
    rows=(len(files)+cols-1)//cols
    im=Image.new('RGB',(cols*cell+12,rows*cell+12),bg)
    for i,f in enumerate(files):
        t=Image.open(io.BytesIO(cairosvg.svg2png(url=f'{d}/{f}',output_width=72,output_height=72))).convert('RGBA')
        im.paste(t,(12+(i%cols)*cell,12+(i//cols)*cell),t)
    im.save(f'{out}/preview-brands-{v.lower()}.png'); print(v,len(files))
