# Learning Rate Scheduling

## Why the Learning Rate Matters So Much

The learning rate controls how large each optimization step is. Too high
and training can oscillate or diverge outright; too low and training
makes barely any progress within a reasonable epoch budget. Of all the
hyperparameters in a training run, the learning rate is usually the one
most likely to single-handedly determine whether a run succeeds or fails.

## Signs the Learning Rate Is Too High

Loss that oscillates wildly between epochs, spikes sharply and doesn't
recover, or diverges toward very large or NaN values are all classic
signs of too high a learning rate. This is different from the loss just
being noisy — a too-high learning rate typically produces spikes that are
large relative to the overall scale of the loss.

## Signs the Learning Rate Is Too Low

Loss decreases, but extremely slowly, and appears to plateau early at a
value well above what similar setups typically achieve. Unlike a genuine
plateau from convergence, this kind of "plateau" is really just very slow
progress that would keep improving given a much larger epoch budget or a
larger learning rate.

## Common Scheduling Strategies

- **Constant**: no schedule; simplest option, but requires the initial
  learning rate to be well-tuned for the entire run.
- **Step decay**: multiply the learning rate by a fixed factor at set
  epoch milestones. Simple and effective, but the milestones need tuning.
- **Cosine annealing**: smoothly decays the learning rate following a
  cosine curve down to a small value by the end of training. Requires no
  milestone tuning and is a reasonable default for many setups.
- **Warmup**: gradually increasing the learning rate for the first few
  epochs before applying the main schedule, often used with larger models
  or larger batch sizes to avoid early instability.

## Practical Guidance

When a run is unstable, checking the learning rate first is usually more
productive than reaching for regularization changes — instability is much
more often a learning-rate or optimization problem than an overfitting
problem.