# ImageNet with DiT

Install `dit/requirements.txt` from the repository root. This code preserves the
supplied DiT objective: **sample-loss masking**, including averaging multiple
independent masks per batch. It does not mask spatial latent pixels.

## 1. Extract VAE features

ImageNet training images must use torchvision ImageFolder layout
`train/<class>/*.JPEG`. Extraction uses ADM center crop to 256×256, a random
horizontal flip, the ft-MSE VAE posterior sample, and latent scaling 0.18215.

```bash
cd dit
# Use the same GPU count for feature extraction within a reproduction.
torchrun --standalone --nproc_per_node=8 extract_features.py \
  --data-path /path/to/imagenet/train --features-path /path/to/features \
  --global-batch-size 1024 --image-size 256 --vae mse
```

The resulting `imagenet256_features` and `imagenet256_labels` folders must contain
matching `.npy` filenames. The original extractor uses a DistributedSampler that
may pad the final dataset partition; this behavior is retained. Features are
cached once and shared by baseline and SSD. Neither features nor VAE weights are
included in this repository.

## 2. Train

```bash
accelerate launch --multi_gpu --num_processes 8 --mixed_precision fp16 train.py \
  --feature-path /path/to/features --results-dir ../outputs/dit-ssd \
  --model DiT-XL/2 --image-size 256 --global-batch-size 4096 \
  --max-steps 180000 --mask-prob 0.98 --multi-mask --disable-wandb
```

For the baseline, use `--mask-prob 0` and a separate results directory. Use
`--ckpt /path/to/0180000.pt` to resume. `--max-steps` includes resumed steps.
For one GPU use `accelerate launch --num_processes 1 --mixed_precision fp16 ...`
without `--multi_gpu`, provided the global batch fits in memory.

DiT-XL/2 uses 675M parameters, latent patch size 2, AdamW lr=1e-4,
betas=(0.9,0.999), weight decay 0, EMA decay 0.9999, learned variance and a
1,000-step linear noise schedule. Multiple masks span local per-sample MSE+VB
losses. Each is normalized separately; empty masks contribute zero, as in the
original experiment. At η=0.98 there are 50 masks. VAE features are not re-encoded
during training. Checkpoints retain model/EMA weights, optimizer, step and args.

The trainer now stops at an explicit total-step budget, supports unwrapped
single-GPU checkpoints, and makes logging optional. It also applies the supplied
seed (`--global-seed`, default 0); the original trainer did not explicitly seed
initialization, so exact random-number-stream matching is not guaranteed.

## 3. Sample and evaluate at CFG=1.5

```bash
torchrun --standalone --nproc_per_node=8 sample_ddp.py \
  --ckpt /path/to/0180000.pt --model DiT-XL/2 --image-size 256 --vae mse \
  --cfg-scale 1.5 --num-sampling-steps 250 --num-fid-samples 50000 \
  --sample-dir ../outputs/dit-samples --global-seed 0
cd ..
python scripts/build_imagenet_reference.py --data-path /path/to/imagenet/val \
  --output /path/to/reference_imagenet_val.npz
```

Sampling loads EMA weights and prints the **exact output NPZ path**, which
includes checkpoint, VAE, CFG and seed. Use that path explicitly below; do not
select the first NPZ in a directory. Each sampling run must use a distinct output
location when checkpoint step names are shared across experiments.

For the paper's reference protocol, the builder resizes all 50K validation images
directly to 256×256 with Lanczos (no center crop). Do not substitute a differently
preprocessed reference NPZ. The reference array is approximately 10 GB; the
builder uses a temporary memory-mapped array to limit peak RAM.

Install `dit/requirements-eval.txt` in a separate Python 3.10/3.11 environment
with TensorFlow, then run the supplied ADM evaluator:

```bash
python dit/evaluator.py /path/to/reference_imagenet_val.npz /exact/sample-output.npz
```

It downloads the Inception graph on first use. Corrected paper full-ImageNet FID
at 180K steps and CFG=1.5 is **4.98 baseline / 4.83 SSD (η=0.98)**. For the
100K-image subset use the same chosen features for both models, batch 2,048 and
100K/200K steps; the reported η=0.98 FIDs are 6.84/15.58 (baseline 8.93/25.99).
The original 100K subset membership is not included, so a newly chosen subset
cannot guarantee those exact values.
