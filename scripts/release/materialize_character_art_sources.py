"""Copy packaged character PNGs to the renderer's documented source layout, without overwrites."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input-root',type=Path,required=True)
    ap.add_argument('--cids',type=int,nargs='+')
    args=ap.parse_args();root=args.input_root.resolve()
    art=root/'output/character_skills/pages/art'
    if not art.is_dir():raise FileNotFoundError('Unpack the character image package first: '+str(art))
    cids=args.cids or sorted(int(p.name) for p in art.iterdir() if p.is_dir() and p.name.isdigit())
    files=[]
    for cid in cids:
        padded=str(cid).zfill(5)
        for name,folder,stem in [('card','Card_OrgSize','card'),('whole','Trimmed_Whole','whole'),('icon','Card_Icon','icon')]:
            source=art/str(cid)/(name+'.png')
            if not source.is_file():continue # Preserve the original missing-art status.
            dest=root/f'output/full_unpack/objects/{folder}/cha_2d_{stem}_{padded}/cha_2d_{stem}_{padded}.png'
            expected=sha(source)
            if dest.exists():
                if not dest.is_file() or sha(dest)!=expected:raise ValueError('Existing different source image: '+str(dest))
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with source.open('rb') as inp,dest.open('xb') as out:shutil.copyfileobj(inp,out)
            if sha(dest)!=expected:raise ValueError('Image copy differs: '+str(dest))
            files.append({'source':source.relative_to(root).as_posix(),'target':dest.relative_to(root).as_posix(),'sha256':expected,'bytes':source.stat().st_size})
    print(json.dumps({'files':files,'bytes':sum(f['bytes'] for f in files)},ensure_ascii=False))

if __name__=='__main__':main()
