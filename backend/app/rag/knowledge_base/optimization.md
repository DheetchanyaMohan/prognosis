# Optimization

## Choosing an Optimizer

**SGD with momentum** is simple, well-understood, and often generalizes
slightly better than adaptive methods given enough tuning, but it's more
sensitive to learning rate choice and typically needs a learning rate
schedule to work well.

**Adam** (and AdamW, which decouples weight decay from the gradient
update rather than folding it into the loss) adapts the effective
learning rate per-parameter, converges quickly, and is much more forgiving
of a slightly-off learning rate — a reasonable default when a lot of
tuning time isn't available.

## Batch Size

Larger batch sizes give a smoother, lower-variance gradient estimate per
step and better hardware utilization, but very large batches can make it
harder to escape sharp minima and sometimes generalize slightly worse
without a corresponding learning rate increase. Very small batch sizes
increase gradient noise, which can act as a mild regularizer but also
makes training less stable, especially combined with a high learning
rate.

## Gradient Clipping

Gradient clipping caps the norm of the gradient before the optimizer step
is applied, preventing any single batch with an unusually large gradient
from causing a destructive update. It's especially useful when training
with a high learning rate or a small batch size, both of which increase
the chance of an occasional large gradient spike.

## Diagnosing Instability

Loss spikes — sudden sharp increases that may or may not recover — are
most often caused by some combination of: learning rate too high, batch
size too small, and no gradient clipping. When several of these are true
simultaneously, instability becomes much more likely than any one factor
alone would suggest.

## Diagnosing Slow Convergence

If loss is decreasing smoothly but very slowly, check the learning rate
first, then whether a learning rate schedule is decaying too early or too
aggressively. Optimizer choice matters much less than learning rate for
this particular symptom.