# Shared Connectors (Reserved -- Not Yet Implemented)

Placeholder for the future connector framework described in the original
CareerOS specification's Job Intelligence Framework (Indeed, JobServe,
CWJobs, Reed, TotalJobs, NHS Jobs, Civil Service Jobs, company career
pages, and eventually recruiter mailboxes). Each connector was specified
to independently implement fetch / validate / normalise / deduplicate /
health-status, with connector failure never able to stop the platform.

This directory is intentionally empty. Job Intelligence is explicitly
**not authorised** as of Sprint 1 Closure (see the Chief Architect
directive recorded in docs/adr and docs/SPRINT-2-IMPLEMENTATION-PLAN.md).
When it is authorised, the connector framework's shared base
(retry/backoff, normalisation contracts, health-status reporting) belongs
here; individual connectors belong under the relevant product or a future
`products/job-intelligence` if it becomes a standalone product.
