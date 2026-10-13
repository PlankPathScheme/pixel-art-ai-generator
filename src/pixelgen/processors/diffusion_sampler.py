"""Diffusion sampler processor.

Wraps diffusers.StableDiffusionPipeline in img2img mode when a reference is
present, txt2img otherwise. Model weights are lazily loaded and cached on the
instance so batch runs pay the load cost once.

Gotcha: diffusers >= 0.30 renamed `safety_checker=None` handling. We pass
`requires_safety_checker=False` in from_pretrained to avoid the deprecation
warning spam and the extra CLIP load on CPU.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from src.pixelgen.processors.base import Processor
from src.pixelgen.jobs import Job

log = logging.getLogger("pixelgen.processor.diffusion")


class DiffusionSampler(Processor):
    _pipe = None  # class-level cache — one model per process

    def _load(self):
        if DiffusionSampler._pipe is not None:
            return DiffusionSampler._pipe
        from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

        weights = Path(self.cfg.model or "models/weights/pixel-diffusion-v2.safetensors")
        if not weights.exists():
            raise FileNotFoundError(f"model weights missing: {weights}")
        device = "cuda" if (self.device in ("auto", "cuda") and torch.cuda.is_available()) else "cpu"
        log.info("loading diffusion model from %s on %s", weights, device)
        pipe = StableDiffusionPipeline.from_single_file(
            str(weights),
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            requires_safety_checker=False,
        )
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe = pipe.to(device)
        if device == "cuda":
            pipe.enable_attention_slicing()
        DiffusionSampler._pipe = pipe
        return pipe

    def apply(self, job: Job) -> None:
        pipe = self._load()
        seed = job.seed if job.seed >= 0 else torch.randint(0, 2**31 - 1, (1,)).item()
        gen = torch.Generator(device="cpu").manual_seed(int(seed))
        prompt = job.artifacts["prompt_augmented"]
        negative = job.artifacts.get("negative_prompt") or None
        ref = job.artifacts.get("reference_rgb")

        if ref is not None:
            init = Image.fromarray(ref).resize((512, 512), Image.NEAREST)
            out = pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=init,
                strength=self.cfg.strength,
                num_inference_steps=self.cfg.steps,
                guidance_scale=self.cfg.guidance,
                generator=gen,
                num_images_per_prompt=job.batch,
            ).images
        else:
            out = pipe(
                prompt=prompt,
                negative_prompt=negative,
                num_inference_steps=self.cfg.steps,
                guidance_scale=self.cfg.guidance,
                generator=gen,
                num_images_per_prompt=job.batch,
            ).images

        job.artifacts["image"] = np.asarray(out[0].convert("RGB"), dtype=np.uint8)
        job.artifacts["image_batch"] = [np.asarray(im.convert("RGB"), dtype=np.uint8) for im in out]
        job.artifacts["seed"] = int(seed)