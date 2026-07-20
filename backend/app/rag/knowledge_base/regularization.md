# Regularization

## What Regularization Does

Regularization techniques constrain a model during training so it's less
able to memorize training-set-specific noise, at some cost to how
tightly it can fit the training data. The goal is a model that performs
closer to equally well on data it hasn't seen, at the cost of it fitting
the training set slightly less perfectly.

## Dropout

Dropout randomly zeroes a fraction of activations during training
(typically applied before fully-connected layers), forcing the network to
not rely too heavily on any single unit. A dropout probability between
0.2 and 0.5 is common; very small models on very small datasets sometimes
benefit from higher values, while larger models with abundant data often
need less. Dropout is disabled at evaluation time.

## Weight Decay (L2 Regularization)

Weight decay adds a penalty proportional to the squared magnitude of the
model's weights to the loss, discouraging any single weight from growing
very large. It's usually implemented directly in the optimizer (most
optimizers accept a `weight_decay` parameter) rather than as a separate
loss term. Typical values are small, often in the 1e-5 to 1e-2 range
depending on model and dataset size.

## Data Augmentation as Regularization

Augmentation effectively regularizes by artificially growing the training
set's diversity, which makes it harder for the model to memorize specific
examples. See the data augmentation document for details on specific
techniques.

## Early Stopping

Stopping training once validation performance stops improving — rather
than training for a fixed number of epochs regardless — is itself a form
of regularization, since it prevents the model from continuing to fit the
training set past the point of diminishing (or negative) returns on
validation performance.

## Balancing Regularization Strength

Too little regularization on a small dataset tends to produce overfitting;
too much on a dataset that already has plenty of data tends to produce
underfitting. When diagnosing a run, the direction of the train/validation
gap (present and growing vs. absent) is usually the best signal for which
direction to adjust regularization in.