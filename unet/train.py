# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the CC-by-NC license found in the
# LICENSE file in the root directory of this source tree.
# Copyright (c) Meta Platforms, Inc. and affiliates.

import datetime
import json
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torchvision.datasets as datasets
from torch.utils.data import Dataset
from PIL import Image
from models.model_configs import instantiate_model
from train_arg_parser import get_args_parser

from training import distributed_mode
from training.data_transform import get_train_transform
from training.eval_loop import eval_model
from training.grad_scaler import NativeScalerWithGradNormCount as NativeScaler
from training.load_and_save import load_model, save_model
from training.train_loop import train_one_epoch

# Import wandb for experiment tracking
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    print("Warning: wandb not available, skipping logging")

logger = logging.getLogger(__name__)

# Automatically detect the best available device
def get_best_device():
    """Automatically detect the best available device in order of preference:
    CUDA (NVIDIA) -> ROCm (AMD) -> MPS (Apple Silicon) -> CPU"""
    try:
        import torch

        if torch.cuda.is_available():
            device_name = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"Using CUDA device: {gpu_name}")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device_name = "mps"
            logger.info("Using Apple Metal Performance Shaders (MPS)")
        elif hasattr(torch.version, 'hip') and torch.version.hip is not None:
            # Check for ROCm/HIP (AMD GPUs)
            device_name = "cuda"  # ROCm uses cuda API
            logger.info("Using ROCm (AMD GPU) with CUDA API")
        else:
            device_name = "cpu"
            logger.info("No GPU acceleration available, using CPU")

    except Exception as e:
        logger.warning(f"Error detecting device: {e}. Falling back to CPU.")
        device_name = "cpu"

    return device_name

class CelebADataset(Dataset):
    """Custom dataset for CelebA that handles flat directory structure."""

    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform

        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        self.image_files = []

        for filename in os.listdir(root_dir):
            if os.path.splitext(filename)[1].lower() in image_extensions:
                self.image_files.append(os.path.join(root_dir, filename))
        self.image_files.sort()

        if len(self.image_files) == 0:
            raise ValueError(f"No image files found in {root_dir}")

        logger.info(f"Found {len(self.image_files)} images in {root_dir}")

    def __len__(self):
        return len(self.image_files)

    def __getitem__(self, idx):
        img_path = self.image_files[idx]
        image = Image.open(img_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        # Return image and dummy label (0) since CelebA is unconditional
        return image, 0

def main(args):
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    distributed_mode.init_distributed_mode(args)

    # Initialize wandb for experiment tracking (only on main process)
    if distributed_mode.is_main_process() and WANDB_AVAILABLE and not args.disable_wandb:
        run_name = args.wandb_name or f"flow_matching_{args.dataset}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Prepare tags
        if args.wandb_tags:
            # Use custom tags if provided
            tags = [tag.strip() for tag in args.wandb_tags.split(',')]
        else:
            # Use default tags
            tags = [args.dataset, "distributed"] if args.distributed else [args.dataset]

        wandb.init(
            project=args.wandb_project,
            name=run_name,
            config=vars(args),
            dir=args.output_dir,
            tags=tags
        )

    logger.info("job dir: {}".format(os.path.dirname(os.path.realpath(__file__))))
    logger.info("{}".format(args).replace(", ", ",\n"))
    if distributed_mode.is_main_process():
        args_filepath = Path(args.output_dir) / "args.json"
        logger.info(f"Saving args to {args_filepath}")
        with open(args_filepath, "w") as f:
            json.dump(vars(args), f)


    # Use automatic device detection if args.device is 'auto', otherwise use specified device
    if args.device == "auto":
        device_str = get_best_device()
    else:
        device_str = args.device
        logger.info(f"Using specified device: {device_str}")

    device = torch.device(device_str)



    # fix the seed for reproducibility
    seed = args.seed + distributed_mode.get_rank()
    torch.manual_seed(seed)
    np.random.seed(seed)

    cudnn.benchmark = True

    logger.info(f"Initializing Dataset: {args.dataset}")
    transform_train = get_train_transform()

    if args.dataset == "cifar10":
        dataset_train = datasets.CIFAR10(
            root=args.data_path,
            train=True,
            download=True,
            transform=transform_train,
        )
    elif args.dataset == "celeba_10k_64x64" or args.dataset == "celeba_50k_64x64":
        # CelebA dataset support - handles flat directory structure
        dataset_train = CelebADataset(args.data_path, transform=transform_train)
        logger.info(f"Loading CelebA dataset from: {args.data_path}")
    elif args.dataset == "lsun_32x32":
        dataset_train = CelebADataset(args.data_path, transform=transform_train)
        logger.info(f"Loading LSUN dataset from: {args.data_path}")
    elif args.dataset == "hands_11k_64x64":
        dataset_train = CelebADataset(args.data_path, transform=transform_train)
        logger.info(f"Loading 11k-Hands dataset from: {args.data_path}")
    else:
        raise NotImplementedError(f"Unsupported dataset {args.dataset}")

    if dataset_train is not None:
        logger.info(dataset_train)

    # Initialize DataLoader (if not already created by webdataset)
    if dataset_train is not None:
        logger.info("Intializing DataLoader")
        num_tasks = distributed_mode.get_world_size()
        global_rank = distributed_mode.get_rank()
        sampler_train = torch.utils.data.DistributedSampler(
            dataset_train, num_replicas=num_tasks, rank=global_rank, shuffle=True
        )
        data_loader_train = torch.utils.data.DataLoader(
            dataset_train,
            sampler=sampler_train,
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            pin_memory=args.pin_mem,
            drop_last=True,
        )
        logger.info(str(sampler_train))

    if len(data_loader_train) == 0:
        raise ValueError("Dataset is smaller than the per-device batch size")

    # define the model
    logger.info("Initializing Model")
    model = instantiate_model(
        architechture=args.dataset,
        is_discrete=args.discrete_flow_matching,
        use_ema=args.use_ema,
    )

    model.to(device)

    model_without_ddp = model
    logger.info(str(model_without_ddp))

    eff_batch_size = (
        args.batch_size * args.accum_iter * distributed_mode.get_world_size()
    )

    logger.info(f"Learning rate: {args.lr:.2e}")

    logger.info(f"Accumulate grad iterations: {args.accum_iter}")
    logger.info(f"Effective batch size: {eff_batch_size}")

    if args.distributed:
        model = torch.nn.parallel.DistributedDataParallel(
            model, device_ids=[args.gpu], find_unused_parameters=True
        )
        model_without_ddp = model.module

    optimizer = torch.optim.AdamW(
        model_without_ddp.parameters(), lr=args.lr, betas=args.optimizer_betas
    )
    if args.decay_lr:
        lr_schedule = torch.optim.lr_scheduler.LinearLR(
            optimizer,
            total_iters=args.epochs,
            start_factor=1.0,
            end_factor=1e-8 / args.lr,
        )
    else:
        lr_schedule = torch.optim.lr_scheduler.ConstantLR(
            optimizer, total_iters=args.epochs, factor=1.0
        )

    logger.info(f"Optimizer: {optimizer}")
    logger.info(f"Learning-Rate Schedule: {lr_schedule}")

    loss_scaler = NativeScaler()

    load_model(
        args=args,
        model_without_ddp=model_without_ddp,
        optimizer=optimizer,
        loss_scaler=loss_scaler,
        lr_schedule=lr_schedule,
    )

    logger.info(f"Start from {args.start_epoch} to {args.epochs} epochs")
    start_time = time.time()
    epoch_range = [args.start_epoch] if args.eval_only else range(args.start_epoch, args.epochs)
    for epoch in epoch_range:
        if args.distributed and hasattr(data_loader_train, 'sampler') and data_loader_train.sampler is not None:
            data_loader_train.sampler.set_epoch(epoch)
        if not args.eval_only:
            train_stats = train_one_epoch(
                model=model,
                data_loader=data_loader_train,
                optimizer=optimizer,
                lr_schedule=lr_schedule,
                device=device,
                epoch=epoch,
                loss_scaler=loss_scaler,
                args=args,
            )
            log_stats = {
                **{f"train_{k}": v for k, v in train_stats.items()},
                "epoch": epoch,
            }

            # Log training metrics to wandb
            if distributed_mode.is_main_process() and WANDB_AVAILABLE and not args.disable_wandb:
                wandb.log({
                    "epoch": epoch,
                    **{f"train/{k}": v for k, v in train_stats.items()},
                })
        else:
            log_stats = {
                "epoch": epoch,
            }

        if args.output_dir and (
            (args.eval_frequency > 0 and (epoch + 1) % args.eval_frequency == 0)
            or args.eval_only
            or args.test_run
        ):
            if not args.eval_only:
                if (epoch+1)%(2*args.eval_frequency)==0:
                    save_model(
                        args=args,
                        model=model,
                        model_without_ddp=model_without_ddp,
                        optimizer=optimizer,
                        lr_schedule=lr_schedule,
                        loss_scaler=loss_scaler,
                        epoch=epoch,
                    )
            if args.distributed:
                data_loader_train.sampler.set_epoch(0)
            if distributed_mode.is_main_process():
                fid_samples = args.fid_samples - (num_tasks - 1) * (
                    args.fid_samples // num_tasks
                )
            else:
                fid_samples = args.fid_samples // num_tasks
            eval_stats = eval_model(
                model,
                data_loader_train,
                device,
                epoch=epoch,
                fid_samples=fid_samples,
                args=args,
            )
            log_stats.update({f"eval_{k}": v for k, v in eval_stats.items()})

            # Log evaluation metrics to wandb
            if distributed_mode.is_main_process() and WANDB_AVAILABLE and not args.disable_wandb:
                wandb.log({
                    "epoch": epoch,
                    **{f"eval/{k}": v for k, v in eval_stats.items()},
                })

        if args.output_dir and distributed_mode.is_main_process():
            with open(
                os.path.join(args.output_dir, "log.txt"), mode="a", encoding="utf-8"
            ) as f:
                f.write(json.dumps(log_stats) + "\n")

        if args.test_run or args.eval_only:
            break

    if not args.eval_only:
        model.train(True)  # Restore raw weights if the last operation evaluated EMA.
        save_model(args, epoch, model, model_without_ddp, optimizer, lr_schedule, loss_scaler)
    total_time = time.time() - start_time
    total_time_str = str(datetime.timedelta(seconds=int(total_time)))
    logger.info(f"Training time {total_time_str}")


if __name__ == "__main__":
    args = get_args_parser()
    args = args.parse_args()
    if not 0 <= args.mask_prob < 1:
        raise ValueError("mask_prob must satisfy 0 <= mask_prob < 1")
    if args.accum_iter < 1 or args.batch_size < 1:
        raise ValueError("batch_size and accum_iter must be positive")
    if distributed_mode.is_main_process():
        print('running and see:', args.output_dir)
    if args.output_dir:
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    main(args)
