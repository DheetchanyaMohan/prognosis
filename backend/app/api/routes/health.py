def _check_chroma() -> HealthComponentStatus:
    try:
        client = get_chroma_client()
        client.heartbeat()

        from app.rag.retriever import (
            CHROMA_PERSIST_DIR,
            KNOWLEDGE_COLLECTION_NAME,
            RUN_SUMMARY_COLLECTION_NAME,
        )

        counts = {}
        for name in (KNOWLEDGE_COLLECTION_NAME, RUN_SUMMARY_COLLECTION_NAME):
            try:
                counts[name] = client.get_collection(name).count()
            except Exception:  # noqa: BLE001 - collection not existing yet reports as 0
                counts[name] = 0

        # TEMPORARY DIAGNOSTIC — remove once the Railway zero-retrieval
        # issue is root-caused and fixed. Reveals exactly what path and
        # collection state the *actual running container* sees, since
        # `railway run` executes locally against pulled env vars, not
        # inside the real container, and can't answer this question.
        detail = f"persist_dir={CHROMA_PERSIST_DIR} counts={counts}"
    except Exception as exc:  # noqa: BLE001
        return HealthComponentStatus(status="error", detail=str(exc))
    return HealthComponentStatus(status="ok", detail=detail)