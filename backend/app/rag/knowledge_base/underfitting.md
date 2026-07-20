# Underfitting

## What It Looks Like

Underfitting happens when a model fails to learn the training data well
enough in the first place. Both training and validation loss stay high,
and training accuracy itself is disappointing — not just validation
accuracy. Unlike overfitting, there's no meaningful gap between train and
validation performance, because the model hasn't captured enough signal
to do well on either.

## Common Causes

- Regularization that's too strong for the amount of data and model
  capacity available (dropout or weight decay set too high)
- A learning rate that's too low to make meaningful progress within the
  epoch budget
- A model with too little capacity for the task's actual complexity
- Too few training epochs for the model to converge
- Features or inputs that don't carry enough signal for the task

## How to Detect It

Look at training loss and accuracy specifically, not just validation.
If training accuracy itself is low and training loss has flattened at a
high value early in training, the model isn't fitting the training set,
which rules out overfitting as the explanation.

## How to Fix It

- Reduce dropout and/or weight decay if they're unusually high
- Increase the learning rate, or check that a learning rate schedule
  isn't decaying too aggressively too early
- Increase model capacity (more layers or channels) if the task
  genuinely needs it
- Train for more epochs if the loss curve is still trending downward
- Verify the loss function and labels are set up correctly — a subtle
  data or labeling bug often masquerades as underfitting

## Underfitting vs. a Genuinely Hard Task

Before adding capacity or changing hyperparameters, rule out that the
task itself is simply hard given the available data — sometimes a model
that looks like it's underfitting is actually performing near the
practical ceiling for the amount of signal in a small dataset.