"""Build the ImageNet validation NPZ using the original resize-only protocol."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-path',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-count',type=int,default=50000)
    args=parser.parse_args()
    files=sorted(p for p in args.data_path.rglob('*') if p.is_file() and p.suffix.lower() in {'.jpg','.jpeg','.png'})
    if len(files)!=args.expected_count:
        parser.error(f'Expected {args.expected_count} validation images, found {len(files)}')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    # A memory-mapped intermediate avoids holding two 10 GB arrays in RAM.
    temporary=args.output.with_suffix('.images.npy')
    images=np.lib.format.open_memmap(temporary,mode='w+',dtype=np.uint8,shape=(len(files),256,256,3))
    try:
        for i,path in enumerate(files):
            with Image.open(path) as image:
                images[i]=np.asarray(image.convert('RGB').resize((256,256),Image.Resampling.LANCZOS))
            if i%10000==0: print(f'{i}/{len(files)}',flush=True)
        images.flush()
        np.savez(args.output,arr_0=images)
    finally:
        del images
        temporary.unlink(missing_ok=True)
    print(args.output)

if __name__=='__main__': main()
