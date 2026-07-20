# Overfitting

## What It Looks Like

Overfitting happens when a model starts memorizing patterns specific to
the training set rather than learning patterns that generalize. The
clearest signal is a growing gap between training loss and validation
loss: training loss keeps falling while validation loss flattens out or
starts rising again. Training accuracy climbing toward 100% while
validation accuracy stalls well below it is the same signal from the
accuracy side.

## Common Causes

- Too little training data relative to how expressive the model is
- Training for too many epochs without any regularization
- Missing or too-weak regularization (dropout, weight decay)
- No data augmentation on a small dataset
- A model with far more capacity than the task actually needs

## How to Detect It

Track train and validation loss on the same plot across epochs. A
consistently widening gap, especially one that starts small and grows
steadily rather than fluctuating randomly, is the signature to look for.
A single epoch where validation loss ticks up isn't overfitting by
itself — look at the trend over several epochs.

## How to Fix It

- Add or increase dropout in the network
- Add weight decay (L2 regularization) to the optimizer
- Add data augmentation, especially for small image datasets
- Reduce model capacity if the dataset is very small
- Use early stopping based on validation loss rather than training for a
  fixed number of epochs regardless of validation performance
- Increase the size of the training set if more data is available

## When It's Not Overfitting

A gap between train and validation metrics that stays roughly constant
across training, rather than widening, is often just an artifact of
train-time augmentation making the training task effectively harder than
the clean validation task — that's expected and not a sign to intervene.