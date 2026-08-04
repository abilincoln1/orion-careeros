# CareerOS

CareerOS is a **product** built on the **ORION Platform** -- it is not
itself the platform. See `/platform` for the shared kernel it consumes
and `/docs/ARCHITECTURE.md` for how the two relate.

CareerOS is a Personal AI Career Operating System: a Career Intelligence
Platform that continuously understands a professional, analyses the
employment market, recommends the highest-value opportunities, prepares
evidence-based applications, and learns from outcomes. See the repository
root `README.md` for setup/run/test instructions and `docs/` for full
documentation.

## Structure

- `backend/` -- FastAPI application. Consumes `orion_kernel` (from
  `/platform/kernel`) for configuration, logging, authentication
  primitives, database wiring, and health endpoints; owns its own models,
  schemas, and API routes.
- `frontend/` -- React + TypeScript + Vite application consuming the
  backend's REST API.
