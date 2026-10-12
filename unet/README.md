# Pixel-space U-Net reproduction

Run the commands in the root README from the repository root. The launcher uses
`scripts/run_unet.py`, `configs/unet.json`, and `unet/train.py`.

## Data preparation

The original experiments read already resized RGB images from flat folders;
training applies random horizontal flipping and scales pixels to [-1,1]. It does
not crop or resize images at runtime. CIFAR-10 uses torchvision's 50K training
images at their native 32×32 resolution.

`configs/celeba50k_filenames.txt` lists the **exact 50,000 filenames** found in the
original preprocessed CelebA-50K folder. If you have that preprocessed folder, use
it directly. To reconstruct membership from the aligned CelebA image release:

```bash
python scripts/prepare_images.py --input /path/to/img_align_celeba \
  --output /path/to/celeba50k --size 64 \
  --manifest configs/celeba50k_filenames.txt --geometry resize
```

The preparation utility converts to RGB, resizes with Lanczos, and writes PNGs
plus membership/preprocessing metadata. `--geometry center-crop` is available
when needed. **The original CelebA/LSUN preprocessing script was not present in
the supplied source**, so newly resized images cannot be claimed to reproduce
its interpolation/cropping exactly. The filename manifest reproduces CelebA
membership, not the original JPEG pixel values.

For LSUN, use the original 303,125-image Bedroom subset at 32×32 when available.
Otherwise export RGB images from your licensed LSUN Bedroom release, provide
your own subset manifest, and prepare the flat folder:

```bash
python scripts/prepare_images.py --input /path/to/exported-bedroom \
  --output /path/to/lsun32 --size 32 --manifest /path/to/lsun-subset.txt
```

The original LSUN subset membership was not available in the supplied data
folders. Selecting a different subset is a reproduction setting, not a guarantee
of exact paper FID. Dataset files should remain outside the repository.

## Masking and model settings

`training/train_loop.py` leaves the noisy input and regression target unchanged.
It applies i.i.d. Bernoulli(1−η) masks to the unreduced squared error [B,C,H,W],
normalizes by retained entries, and resamples every step. `--multi-mask` averages
`2*round(1/(1−η))` independent masked losses from a single forward pass.
`--patch-mask` uses 8×8 masks shared across channels; `--patch_size` controls size.
The main η=0.8 experiments use a single mask.

Architecture configurations are in `models/model_configs.py`, retaining the
original channel multipliers, dropout and attention settings. Training uses
AdamW, lr=1e-4, betas=(0.9,0.95), the inherited default weight decay (0.01), mixed
precision and EMA with nominal decay 0.999 and its original warmup rule. These
models are unconditional (`class_drop_prob=1`, `cfg_scale=0`).

## Sampling and evaluation details

The source's `{"nfe":50}` creates **51 time points / 50 intervals**. With standard
torchdiffeq `heun2`, this takes 100 velocity evaluations; the source logs the
actual calls. We keep the original schedule instead of changing it to 50 calls.

FID uses torchmetrics/torch-fidelity Inception features against batches from the
training loader, with its original horizontal-flip augmentation and shuffled
sampler. The inherited loop requests 50K generated images but runs for at most
one loader pass with `drop_last=True`: CelebA/CIFAR settings above produce
49,920 images on one GPU. LSUN's larger loader reaches the 50K target. The real
reference consists of the corresponding processed batches, not an independent
validation split. Changing GPU count changes sampler partitioning and can change
sample counts slightly. Metrics now record the actual global real/fake counts.

`log.txt` records training loss and evaluation FID; `args.json` records the run
settings. Periodic checkpoints and the final `checkpoint.pth` retain optimizer,
scheduler, scaler and EMA state. The cleaned entrypoint also supports evaluation
when a resumed checkpoint is already beyond the requested training epoch count.
