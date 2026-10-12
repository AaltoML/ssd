"""CPU smoke checks for the retained objectives and the continuous U-Net path."""
import sys
import unittest
from argparse import Namespace
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'unet'))
sys.path.insert(0, str(ROOT / 'dit'))
# U-Net's models/ is a package; import it before introducing DiT models.py.
sys.path.remove(str(ROOT / 'dit'))
from models.unet import UNetModel
from models.ema import EMA
from training.train_loop import sample_loss_mask, train_one_epoch
from training.grad_scaler import NativeScalerWithGradNormCount
from training.edm_time_discretization import get_time_discretization
sys.path.insert(0, str(ROOT / 'dit'))
from loss_masking import masked_loss
from diffusion import create_diffusion
from flow_matching.solver.ode_solver import ODESolver
from torch.utils.data import DataLoader, TensorDataset

torch.set_num_threads(2)

class MaskingTests(unittest.TestCase):
    def test_element_and_patch_masks(self):
        torch.manual_seed(0)
        shape=torch.Size([2,3,16,16])
        element=sample_loss_mask(shape,.5,torch.device('cpu'))
        self.assertTrue(set(element.unique().tolist()) <= {0.,1.})
        self.assertFalse(torch.equal(element[:,0],element[:,1]))
        patch=sample_loss_mask(shape,.5,torch.device('cpu'),True,8)
        self.assertTrue(torch.equal(patch[:,0],patch[:,1]))
        for r in [0,8]:
            for c in [0,8]:
                block=patch[:,:,r:r+8,c:c+8]
                self.assertTrue(torch.all(block==block[:,:,0:1,0:1]))
        with self.assertRaises(AssertionError):
            sample_loss_mask(torch.Size([1,3,15,16]),.5,torch.device('cpu'),True,8)

    def test_dit_multi_mask_normalization_and_gradients(self):
        torch.manual_seed(0)
        loss=torch.full((4096,),2.,requires_grad=True)
        result=masked_loss(loss,.98,True)
        self.assertAlmostEqual(result.item(),2.,places=5)
        result.backward()
        self.assertTrue(torch.all(loss.grad>=0))
        self.assertAlmostEqual(loss.grad.sum().item(),1.,places=5)
        self.assertTrue(torch.allclose(masked_loss(loss,0),loss.mean()))
        with self.assertRaises(ValueError): masked_loss(loss.reshape(64,64),.98,True)
        with self.assertRaises(ValueError): masked_loss(loss,1.,True)

    def test_dit_diffusion_returns_per_image_losses(self):
        class ToyModel(torch.nn.Module):
            def __init__(self):
                super().__init__(); self.scale=torch.nn.Parameter(torch.tensor(.1))
            def forward(self,x,t,**kwargs):
                return torch.cat([x*self.scale,torch.zeros_like(x)],dim=1)
        model=ToyModel()
        diffusion=create_diffusion('')
        losses=diffusion.training_losses(model,torch.randn(4,4,8,8),torch.tensor([1,10,100,500]))
        self.assertEqual(losses['loss'].shape,(4,))
        result=masked_loss(losses['loss'],.8,True)
        result.backward()
        self.assertTrue(torch.isfinite(model.scale.grad))

    def test_unet_masked_training_step_and_ema(self):
        torch.manual_seed(0)
        model=EMA(UNetModel(in_channels=3,model_channels=32,out_channels=3,
            num_res_blocks=1,attention_resolutions=[],channel_mult=[1],
            num_heads=1,num_classes=None))
        before=next(model.model.parameters()).detach().clone()
        loader=DataLoader(TensorDataset(torch.rand(2,3,8,8),torch.zeros(2,dtype=torch.long)),batch_size=2)
        optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4,betas=(.9,.95))
        scheduler=torch.optim.lr_scheduler.ConstantLR(optimizer,factor=1.,total_iters=1)
        args=Namespace(accum_iter=1,discrete_flow_matching=False,class_drop_prob=1.,
            skewed_timesteps=True,mask_prob=.8,multi_mask=True,patch_mask=False,patch_size=8,test_run=False)
        stats=train_one_epoch(model,loader,optimizer,scheduler,torch.device('cpu'),0,
            NativeScalerWithGradNormCount(),args)
        self.assertGreater(stats['loss'],0.)
        self.assertFalse(torch.equal(before,next(model.model.parameters()).detach()))
        self.assertEqual(model.num_updates.item(),1)

    def test_original_heun_grid_and_call_count(self):
        time=get_time_discretization(50)
        self.assertEqual(len(time),51)
        self.assertTrue(torch.all(time[1:]>time[:-1]))
        calls=[]
        def velocity(x,t,**kwargs):
            calls.append(t);return torch.ones_like(x)
        solver=ODESolver(velocity)
        result=solver.sample(torch.zeros(2),None,method='heun2',time_grid=time)
        self.assertEqual(len(calls),100)
        self.assertTrue(torch.allclose(result,torch.ones_like(result)*(time[-1]-time[0]),atol=1e-6))

if __name__=='__main__': unittest.main()
