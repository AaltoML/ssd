# Sparsely Supervised Diffusion (SSD)

Code for **Sparsely Supervised Diffusion**, published at **NeurIPS 2026**.

[Paper](https://openreview.net/pdf?id=4HalTYbzQG) ·
[arXiv](https://arxiv.org/abs/2602.02699) ·
[Project website](https://wenshuaizhao.github.io/ssd/)

- `unet/`: pixel-space flow matching for CelebA-50K, CIFAR-10 and LSUN Bedroom.
- `dit/`: ImageNet DiT training on cached VAE features, sampling and ADM evaluation.
- `flow_matching/`: vendored Flow Matching library used by the U-Net experiments.

Only source, configurations and a CelebA subset filename manifest are included.
Datasets, checkpoints, features, generated images and logs are not distributed.

## Install

Use Python 3.10–3.12 (3.11 recommended) and a CUDA-enabled PyTorch/torchvision pair suitable for
your GPU. Create an environment, then run from the repository root:

```bash
pip install -r requirements.txt
pip install -e .
# Add these packages for ImageNet:
pip install -r dit/requirements.txt
```

Weights & Biases is optional; the documented commands disable it. Training needs
CUDA GPUs. Install dependencies before running on a compute node without internet;
FID's Inception weights and DiT's VAE also need to be downloaded/cached beforehand.

## U-Net experiments

Provide the original-size CIFAR-10 training set (downloaded by torchvision), and
flat RGB folders containing **50,000 CelebA images at 64×64** and **303,125 LSUN
Bedroom images at 32×32**. See [data preparation](unet/README.md#data-preparation)
for the exact CelebA subset manifest and preprocessing limits.

```bash
python scripts/run_unet.py --dataset celeba_50k_64x64 \
  --data-path /path/to/celeba50k --output-dir outputs/celeba-ssd --mask-prob 0.8
python scripts/run_unet.py --dataset cifar10 \
  --data-path /path/to/cifar10 --output-dir outputs/cifar-ssd --mask-prob 0.8
python scripts/run_unet.py --dataset lsun_32x32 --gpus 2 \
  --data-path /path/to/lsun-bedroom --output-dir outputs/lsun-ssd --mask-prob 0.8
```

Set `--mask-prob 0` for baselines; use distinct output directories for every mask
ratio and seed. The main sweeps use η ∈ {0, 0.2, 0.5, 0.8}; repeat with seeds
0–3 for four runs. Change `--gpus` while preserving the default global batch size.
Use `--dry-run` to inspect a command without launching training.

| Dataset | Resolution | Epochs | Global batch | FID interval |
|---|---:|---:|---:|---:|
| CelebA-50K | 64×64 | 2,000 | 128 | 100 epochs |
| CIFAR-10 | 32×32 | 3,000 | 256 | 100 epochs |
| LSUN Bedroom | 32×32 | 2,000 | 1,024 | 200 epochs |

The launcher enables EMA, skewed timesteps and the original EDM time grid with
`heun2` and `{"nfe": 50}`. The inherited setting names the grid size; see the
[U-Net notes](unet/README.md) for actual solver calls and FID counts.

Evaluate a locally trained checkpoint with the same settings:

```bash
python scripts/run_unet.py --dataset celeba_50k_64x64 \
  --data-path /path/to/celeba50k --output-dir outputs/celeba-eval \
  --resume outputs/celeba-ssd/checkpoint.pth --eval-only --save-fid-samples
```

Checkpoints and JSON-lines metrics are saved in the output directory. Evaluation
uses EMA weights. `--resume` also resumes training when `--eval-only` is omitted.

## ImageNet

See [the DiT instructions](dit/README.md) for feature extraction, matched-budget
training, CFG=1.5 sampling, and ADM FID against ImageNet validation images.

**Implementation distinction:** U-Net SSD masks individual regression-loss
entries independently across spatial positions and channels. The supplied DiT
experiment first reduces diffusion MSE/VB to one scalar per image, then masks
those **per-sample losses**. With `--multi-mask`, DiT averages
`round(1 / (1 - η))` independently masked batch losses (50 at η=0.98), using one
model forward pass. We preserve this experimental implementation; it is not
spatial masking of latent pixels. The optional U-Net `--multi-mask` instead uses
`2 * round(1 / (1 - η))` element-wise masks.

## Citation

If you use SSD in your research, please cite our NeurIPS 2026 paper:

```bibtex
@inproceedings{zhao2026sparsely,
  title     = {Sparsely Supervised Diffusion},
  author    = {Zhao, Wenshuai and Li, Zhiyuan and Zhao, Yi and Vali, Mohammad Hassan and Trapp, Martin and Pajarinen, Joni and Kannala, Juho and Solin, Arno},
  booktitle = {Advances in Neural Information Processing Systems},
  year      = {2026}
}
```

The reference is also available in [citation.bib](citation.bib).
