"""Exact sample-loss masking used by the supplied ImageNet experiments."""
import torch

def masked_loss(loss, mask_prob=0.0, multi_mask=False):
    """Average masked, already-reduced per-sample diffusion losses.

    Each mask spans the local batch. No extra model forward pass or spatial
    latent masking is performed. Empty masks contribute zero, as in the source.
    """
    if loss.ndim != 1:
        raise ValueError('Expected one scalar diffusion loss per sample, shape [B]')
    if not 0 <= mask_prob < 1:
        raise ValueError('mask_prob must satisfy 0 <= mask_prob < 1')
    if mask_prob > 0.0:
        if multi_mask:
            n_masks = round(1.0 / (1.0 - mask_prob))
            masks = (torch.rand(n_masks, loss.shape[0], device=loss.device) >= mask_prob).float()
            return ((masks * loss).sum(dim=1) / masks.sum(dim=1).clamp(min=1)).mean()
        mask = (torch.rand_like(loss) >= mask_prob).float()
        return (loss * mask).sum() / mask.sum().clamp(min=1)
    return loss.mean()
