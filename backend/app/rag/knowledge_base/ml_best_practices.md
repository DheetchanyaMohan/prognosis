# ML Experimentation Best Practices

## Change One Thing at a Time

When diagnosing a training pathology, changing multiple hyperparameters
between runs makes it impossible to attribute the outcome to any one
change. A single-variable comparison between two otherwise-identical runs
is far more informative than a run that changes five things at once, even
though it takes more runs to fully explore a hyperparameter space this
way.

## Establish a Healthy Baseline First

Before diagnosing a problem, it's worth confirming what "healthy" looks
like for the same architecture and dataset — a baseline run with
reasonable, unremarkable hyperparameters. Diagnosing an unusual run is
much easier with a known-good reference to compare against than in
isolation.

## Choosing a Batch Size

Batch size interacts with learning rate: as a rough rule of thumb,
scaling batch size up without also scaling the learning rate tends to
slow convergence, while a very small batch size increases gradient noise
and can require a lower learning rate for stability. When in doubt, keep
batch size fixed across a comparison and vary only the hyperparameter
actually being studied.

## Early Stopping and Fixed Epoch Budgets

A fixed epoch budget across a set of comparable runs makes learning
curves directly comparable, which is valuable when the goal is diagnosis
rather than squeezing out maximum performance from any single run. Early
stopping is more appropriate once a specific configuration has already
been identified as promising and the goal shifts to final performance.

## Reproducibility

Fixing a random seed and documenting every hyperparameter in a versioned
config file (rather than relying on memory or informal notes) is what
makes a run's results trustworthy and its failure modes diagnosable later.
An experiment that can't be reproduced from its recorded configuration is
much less useful even if its numbers looked good.

## Reading Learning Curves

The shape of a learning curve over time is usually more informative than
its value at any single epoch. A curve that's still decreasing at the end
of training suggests more epochs would help; a curve that plateaued early
suggests the epoch budget isn't the bottleneck.