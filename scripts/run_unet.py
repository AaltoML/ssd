"""Portable paper training/evaluation launcher; all paths are supplied by the user."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PRESETS = json.loads((ROOT / 'configs/unet.json').read_text())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=PRESETS, required=True)
    parser.add_argument('--data-path', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--mask-prob', type=float, default=0.8)
    parser.add_argument('--gpus', type=int, default=1)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--global-batch-size', type=int)
    parser.add_argument('--epochs', type=int)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--resume')
    parser.add_argument('--eval-only', action='store_true')
    parser.add_argument('--multi-mask', action='store_true')
    parser.add_argument('--patch-mask', action='store_true')
    parser.add_argument('--save-fid-samples', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args, extra = parser.parse_known_args()
    cfg = PRESETS[args.dataset]
    batch = args.global_batch_size or cfg['global_batch_size']
    if args.gpus < 1 or batch % args.gpus:
        parser.error('global batch size must be divisible by the positive GPU count')
    if not 0 <= args.mask_prob < 1:
        parser.error('mask probability must satisfy 0 <= p < 1')
    command = [sys.executable, '-m', 'torch.distributed.run', '--standalone',
        f'--nproc_per_node={args.gpus}', str(ROOT/'unet/train.py'),
        '--dataset', args.dataset, '--data_path', str(Path(args.data_path).resolve()),
        '--output_dir', str(Path(args.output_dir).resolve()), '--batch_size', str(batch//args.gpus),
        '--epochs', str(args.epochs or cfg['epochs']), '--eval_frequency', str(cfg['eval_frequency']),
        '--seed', str(args.seed), '--num_workers', str(args.workers), '--lr', '0.0001',
        '--optimizer_betas', '0.9', '0.95', '--class_drop_prob', '1.0', '--cfg_scale', '0.0',
        '--compute_fid', '--fid_samples', '50000', '--ode_method', 'heun2',
        '--ode_options', '{"nfe": 50}', '--mask_prob', str(args.mask_prob),
        '--use_ema', '--edm_schedule', '--skewed_timesteps', '--disable_wandb']
    for flag in ['eval_only', 'multi_mask', 'patch_mask', 'save_fid_samples']:
        if getattr(args, flag): command.append('--'+flag)
    if args.resume: command.extend(['--resume',str(Path(args.resume).resolve())])
    command += extra
    print(shlex.join(command),flush=True)
    if not args.dry_run:
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
        subprocess.run(command, cwd=ROOT, env=env, check=True)

if __name__ == '__main__': main()
