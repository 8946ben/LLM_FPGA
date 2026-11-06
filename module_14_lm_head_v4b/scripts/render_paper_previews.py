"""Render a contact sheet for original-paper visual identity QA."""
from pathlib import Path
import concurrent.futures,json,subprocess
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
PAP=ROOT/'doc/paper/lm_head_quantization'
OUT=ROOT/'module_14_lm_head_v4b/reports/research_design/pdf_previews'
OUT.mkdir(parents=True,exist_ok=True)
papers=json.loads((PAP/'manifest.json').read_text(encoding='utf-8'))['papers']
def render(p):
    dest=OUT/p['id']
    subprocess.run(['pdftoppm','-f','1','-l','1','-scale-to','650','-jpeg','-singlefile',str(PAP/p['file']),str(dest)],check=True,capture_output=True)
    return dest.with_suffix('.jpg')
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    paths=list(pool.map(render,papers))
sheet=Image.new('RGB',(2000,2800),'#dde6dd')
draw=ImageDraw.Draw(sheet)
for i,path in enumerate(paths):
    x=(i%4)*500;y=(i//4)*700
    draw.text((x+15,y+10),papers[i]['id']+' '+papers[i]['name'],fill='black')
    preview=Image.open(path).convert('RGB');preview.thumbnail((480,650))
    sheet.paste(preview,(x+(500-preview.width)//2,y+40))
sheet.save(OUT/'paper_contact_sheet.jpg',quality=90)
print(OUT/'paper_contact_sheet.jpg')
