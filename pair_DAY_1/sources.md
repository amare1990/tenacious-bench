# Sources

## Canonical sources

1. Hu et al., 2021 — *LoRA: Low-Rank Adaptation of Large Language Models*  
   https://arxiv.org/abs/2106.09685

2. Li et al., 2018 — *Measuring the Intrinsic Dimension of Objective Landscapes*  
   https://arxiv.org/abs/1804.08838

## Tool / demonstration

- LoRA rank-sweep demonstration included in `explainer.md`, comparing the expected behavior of r=4, r=8, and r=16 on a small preference fine-tuning setup.
- Gradient-spectrum demonstration included in `explainer.md`, showing how singular values of accumulated gradients can reveal low-rank adaptation structure.

## Public artifacts

- Blog: https://medium.com/@amaremek/stop-copying-lora-defaults-how-to-actually-choose-rank-for-fine-tuning-f6311f9f0ef7
- X thread: https://x.com/amaremek/status/2051407182923452753