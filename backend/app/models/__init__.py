"""ORM model registry.

Importing this package registers every model on Base.metadata, which is
required both for Alembic autogenerate and for Base.metadata.create_all()
to see every table.
"""

from app.models.experiment import Experiment
from app.models.metric import Metric
from app.models.run import Run

__all__ = ["Experiment", "Run", "Metric"]
