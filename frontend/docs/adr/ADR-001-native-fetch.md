# ADR-001: Use Native `fetch` Instead of Axios

**Status:** Accepted
**Date:** 2026-07-21

## Context

The backend currently exposes only four read-only REST endpoints with no
authentication, interceptors, or request transformation requirements
(Frontend Integration Guide §2, §3).

## Options Considered

- Axios
- Native `fetch`

## Decision

Use the browser's native `fetch` API with a thin wrapper (`src/lib/api/client.ts`).

## Rationale

Reduces dependencies, leverages modern browser capabilities, and keeps the
networking layer simple while meeting all current requirements.

## Consequences

If authentication, interceptors, or more advanced request handling are
introduced later, the wrapper can be extended or swapped without changing
feature code — every feature calls `apiGet<T>()`, never `fetch` directly.
