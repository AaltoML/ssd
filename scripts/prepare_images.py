"""Prepare flat RGB image folders, with explicit subset membership and geometry."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--size', type=int, required=True)
    parser.add_argument('--manifest', type=Path, help='One input-relative filename per line, in order')
    parser.add_argument('--limit', type=int, help='First N sorted files; ignored when manifest is supplied')
    parser.add_argument('--geometry', choices=['resize','center-crop'], default='resize')
    args = parser.parse_args()
    if args.size < 1: parser.error('size must be positive')
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output must be empty to avoid mixing dataset subsets')
    if args.manifest:
        files = [args.input/x.strip() for x in args.manifest.read_text().splitlines() if x.strip()]
    else:
        files = sorted(p for p in args.input.rglob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS)
        if args.limit: files=files[:args.limit]
    if not files: parser.error('no input images')
    missing = [str(p) for p in files if not p.is_file()]
    if missing: parser.error(f'{len(missing)} missing files; first: {missing[0]}')
    if len({p.stem for p in files})!=len(files): parser.error('duplicate filename stems; flattening would overwrite samples')
    args.output.mkdir(parents=True,exist_ok=True)
    for index,path in enumerate(files):
        with Image.open(path) as image:
            image = image.convert('RGB')
            if args.geometry=='center-crop':
                image=ImageOps.fit(image,(args.size,args.size),method=Image.Resampling.LANCZOS)
            elif image.size!=(args.size,args.size):
                image=image.resize((args.size,args.size),Image.Resampling.LANCZOS)
            image.save(args.output/(path.stem+'.png'))
        if index%10000==0: print(f'{index}/{len(files)}',flush=True)
    names='\n'.join(str(p.relative_to(args.input)) for p in files)+'\n'
    (args.output/'preparation.json').write_text(json.dumps({'images':len(files),'size':args.size,
        'geometry':args.geometry,'membership_sha256':hashlib.sha256(names.encode()).hexdigest()},indent=2)+'\n')
    (args.output/'filenames.txt').write_text(names)
    print(f'Prepared {len(files)} images in {args.output}')

if __name__=='__main__': main()
