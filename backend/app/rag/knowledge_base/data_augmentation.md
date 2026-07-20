# Data Augmentation

## Why It Helps

Data augmentation applies random, label-preserving transformations to
training examples, effectively growing the diversity of the training set
without collecting new data. This makes it harder for a model to memorize
specific training examples, which is why augmentation is one of the most
effective and cheapest tools against overfitting on small datasets.

## Common Image Augmentation Techniques

- **Random crop**: pads the image and crops a random region, so the
  model doesn't rely on objects always appearing in the same position.
- **Random horizontal flip**: mirrors the image left-right; appropriate
  for most natural image tasks but not for tasks where left-right
  orientation is meaningful (e.g. text).
- **Color jitter**: randomly perturbs brightness, contrast, and
  saturation, reducing sensitivity to lighting conditions.
- **Random rotation**: rotates the image by a small random angle.
- **Cutout / random erasing**: masks out a random rectangular region,
  forcing the model not to rely too heavily on any single localized
  feature.

## How Much Is Too Much

Augmentation that's too aggressive relative to the dataset's size and the
task's difficulty can make the training task harder than the actual
target task, which shows up as underfitting-like symptoms — training loss
that stays higher than expected because the model is essentially solving
a harder problem than evaluation will ask of it. Augmentation strength
should scale down as available data grows; a very large dataset often
needs little to no augmentation.

## Augmentation and the Train/Validation Gap

Because augmentation is normally applied to training data only,
comparing raw train and validation loss can slightly overstate the true
generalization gap — the training task is genuinely a bit harder due to
the added variation. This is expected and not itself a sign of a problem.

## When Augmentation Won't Help

If a model is underfitting because it fundamentally lacks the capacity
for the task, adding more augmentation will usually make things worse,
not better — augmentation is a regularizer, and underfitting calls for
less regularization, not more.