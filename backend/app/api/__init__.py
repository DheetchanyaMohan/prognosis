"""FastAPI layer.

Routes are thin: they resolve dependencies (DB session, settings) and
delegate to app.tools — the same abstraction boundary LangGraph nodes
use. No route parses a CSV, opens a raw SQLAlchemy session outside the
dependency system, or duplicates logic that already lives in app.tools,
app.config, or app.data_generation.
"""