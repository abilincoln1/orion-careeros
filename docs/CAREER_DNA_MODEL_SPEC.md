# Career Knowledge Model Specification

**Sprint:** 2 -- Career DNA Service
**Status:** Draft, submitted for architecture review (see
`docs/SPRINT-2-ARCHITECTURE-REVIEW.md`) before Phase 2 implementation.
**Author:** Claude, Chief Software Engineer, Project ORION
**Date:** 2026-08-04

This is the canonical specification of CareerOS's Career Knowledge Model:
an evidence-backed, structured, queryable representation of a person's
professional identity. It is not a CV and not a profile page -- it is the
data every future CareerOS feature (matching, recommendations, document
generation, analytics) must read from and write to. Nothing may bypass
it.

## 0. Modeling principles (apply to every entity below)

1. **Evidence is first-class, not a text field.** Anywhere a claim can be
   backed by proof (a skill, an achievement, a competency), it is backed
   by a real `Evidence` record, not a free-text description alone. See
   §6 Evidence.
2. **Facts are attributable.** Every record that represents a claim about
   a person carries who/what asserted it (self-reported, inferred,
   verified) -- see the `attribution_source` field pattern used
   throughout.
3. **History is preserved, not overwritten.** Career facts (an
   employment, a certification) are not edited into a different fact when
   they change meaning -- they get a new record and the old one's
   `valid_to`/`status` is set. Mutable *current-state* fields (like a
   profile headline) are the exception -- see §9 Versioning strategy for
   the precise rule.
4. **Shared vocabulary is normalized; personal facts are not
   duplicated.** `Employer`, `Skill`, `Technology`, `Industry`,
   `JobFamily`, and `Occupation` are shared, deduplicated taxonomy tables
   -- a thousand people who worked at the same company reference one
   `Employer` row, not a thousand copies of its name. A person's
   *possession* of a skill, technology, or competency is a separate
   association record (a join entity) carrying person-specific attributes
   (proficiency, dates, evidence) -- the taxonomy entity itself carries
   none of that.
5. **Ownership is explicit.** Every table below states who "owns" a row:
   either a specific `Person` (the row is meaningless without them, and is
   deleted/anonymized if they are), or the Platform/taxonomy (the row is
   shared reference data, not deleted when any one person's data is).
6. **No unnecessary abstraction.** Where two of the directive's named
   concepts turned out, on inspection, to be the same thing wearing two
   names (see §3 Technology and §5 Qualification), they are implemented
   as one table with a discriminator, not two tables joined 1:1. This is
   a normalization decision, explained inline and revisited in the
   Architecture Review, not a silent omission -- every named concept from
   the directive is still documented below as a first-class concept, even
   where it isn't a separate physical table.

## Entity index

| # | Entity | Physical table? | Group |
|---|---|---|---|
| 1 | Person | Yes | Identity |
| 2 | CareerProfile | Yes | Identity |
| 3 | Employer | Yes | Employment |
| 4 | Employment | Yes | Employment |
| 5 | Role | Yes | Employment |
| 6 | Skill | Yes | Skills |
| 7 | PersonSkill (association) | Yes | Skills |
| 8 | Competency | Yes | Skills |
| 9 | PersonCompetency (association) | Yes | Skills |
| 10 | Technology | Yes (unifies Framework/Tool/Programming Language) | Skills |
| 11 | Framework | No -- `Technology` where `category='framework'` | Skills |
| 12 | Tool | No -- `Technology` where `category='tool'` | Skills |
| 13 | Programming Language | No -- `Technology` where `category='language'` | Skills |
| 14 | PersonTechnology (association) | Yes | Skills |
| 15 | Education | Yes | Credentials |
| 16 | Certification | Yes | Credentials |
| 17 | Qualification | No -- conceptual supertype of Education + Certification | Credentials |
| 18 | Project | Yes | Work product |
| 19 | Achievement | Yes | Work product |
| 20 | Publication | Yes | Work product |
| 21 | PortfolioItem | Yes | Work product |
| 22 | Evidence | Yes | Evidence |
| 23 | EvidenceLink (association) | Yes | Evidence |
| 24 | Reference | Yes | Evidence |
| 25 | CareerGoal | Yes | Preferences & goals |
| 26 | LocationPreference | Yes | Preferences & goals |
| 27 | WorkPreference | Yes | Preferences & goals |
| 28 | SalaryPreference | Yes | Preferences & goals |
| 29 | Industry | Yes | Taxonomy |
| 30 | JobFamily | Yes | Taxonomy |
| 31 | Occupation | Yes | Taxonomy |

All 27 concepts named in the directive are covered (rows 1-10, 15-31 are
1:1 with the directive's list; rows 11-13 and 17 are the directive's
remaining four concepts, documented here and resolved to existing
physical tables per Principle 6).

---

## 1. Identity

### 1.1 Person
**Purpose:** the root of an individual's Career DNA graph. Every other
entity in this model ultimately traces back to exactly one `Person`.

**Relationship to `User` (Sprint 1):** `User` (existing, `app/models/user.py`)
is the *authentication* identity -- email, password hash, login. `Person`
is the *professional* identity. They are separate concerns for a reason:
a future multi-tenant phase (explicitly out of scope, but the model
shouldn't have to be redesigned to allow for it) could have a `User` who
manages more than one `Person` (e.g., a career coach), or a `Person`
record created before its owner ever registers a login. For Sprint 2,
the relationship is 1:1 and created automatically when a `User`
registers.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `user_id` | UUID, FK -> `users.id`, unique, not null | Enforces 1:1 today; the FK being on `Person` (not `User`) is what leaves room for the future 1:many without a migration that changes direction. |
| `first_name` | string(100), not null | |
| `last_name` | string(100), not null | |
| `preferred_name` | string(100), nullable | |
| `headline` | string(255), nullable | e.g. "Senior Backend Engineer, Fintech" |
| `created_at` | timestamptz, not null | |
| `updated_at` | timestamptz, not null | |

**Validation:** `first_name`/`last_name` non-empty after trim. `headline`
max 255 chars (a headline, not a summary -- summaries live on
`CareerProfile`).

**Relationships:** 1:1 `User`. 1:1 `CareerProfile`. 1:many to almost
every other Person-owned entity in this document (`Employment`, `Skill`
possession, `Education`, etc. -- listed under each entity's own
"Ownership" line rather than repeated here).

**Cardinality:** exactly one `Person` per `User` (Sprint 2 constraint;
see above for why the FK direction leaves room to relax this later).

**Ownership:** the person themself. Deleting a `User` cascades to
deleting their `Person` and everything Person-owned (see §9 for the
precise cascade policy).

**Lifecycle:** created at registration (via `User` creation, Sprint 1);
updated as the person edits their identity fields; not soft-deleted
separately from account deletion.

**Versioning:** `Person`'s own fields (name, headline) are current-state,
overwritten in place, `updated_at` bumped. They are not historically
significant the way an `Employment` record is -- nobody needs to know
what someone's headline said last year.

### 1.2 CareerProfile
**Purpose:** the queryable *summary* of a Person's Career DNA -- the
aggregate view every consuming feature (search, matching, recommendations
-- all future, all out of scope this sprint) reads first. It exists so
those features don't have to recompute "years of experience" or "primary
industry" from raw `Employment` rows on every read; it's a maintained
projection, not a duplicate source of truth.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, unique, not null | |
| `summary` | text, nullable | Free-text professional summary -- the *only* place in this model where free text is acceptable as primary content, precisely because it's explicitly a narrative summary, not a claim needing evidence. |
| `career_stage` | enum(`entry`,`mid`,`senior`,`lead`,`executive`), nullable | Self-reported or derived; either is valid, tracked via `career_stage_source`. |
| `career_stage_source` | enum(`self_reported`,`derived`), not null, default `self_reported` | |
| `total_experience_months` | integer, nullable | Derived/cached from `Employment` rows; recomputed, not hand-edited (Phase 2 service responsibility, not a client-writable field). |
| `primary_industry_id` | UUID, FK -> `industry.id`, nullable | |
| `visibility` | enum(`private`,`platform`), not null, default `private` | Out-of-scope features (sharing, matching) will read this; Sprint 2 only defines and enforces the default. |
| `last_reviewed_at` | timestamptz, nullable | When the person last confirmed the profile is accurate -- a staleness signal for future recommendation quality, not used by anything yet. |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `summary` max 4000 chars. `total_experience_months` >= 0,
server-computed only (rejected if present in a client CRUD payload).

**Relationships:** 1:1 `Person`. many:1 `Industry` (optional).

**Cardinality:** exactly one `CareerProfile` per `Person`, created
automatically alongside it.

**Ownership:** the person.

**Lifecycle:** created with `Person`; fields updated as career facts
change or are recomputed; never deleted independently.

**Versioning:** this is the one entity where the directive's "career
history must be versionable" is met head-on, because this is the
aggregate whose *history over time* (not just current state) has real
future value (e.g., "show me how this person's experience grew"). See
§9 for the `CareerProfileSnapshot` mechanism.

---

## 2. Employment

### 2.1 Employer
**Purpose:** a normalized, shared record of an organization someone was
employed by. Shared across every `Person` who lists that employer --
not copied per person.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `name` | string(255), not null | |
| `normalized_name` | string(255), not null, indexed | Lowercased, punctuation-stripped, used for dedup matching on create (e.g. "Acme Inc." and "ACME, Inc" resolve to the same row). |
| `industry_id` | UUID, FK -> `industry.id`, nullable | |
| `website` | string(500), nullable | |
| `size_range` | enum(`1-10`,`11-50`,`51-200`,`201-1000`,`1001-5000`,`5001+`), nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `name` non-empty. `website` must be a valid URL if
present. `normalized_name` has a **DB-level unique index** (independent
review finding: a service-layer "look up, then insert if not found" is a
race condition -- two concurrent requests for the same new employer can
both pass the lookup and both insert). Create-time dedup is an **upsert**
(`INSERT ... ON CONFLICT (normalized_name) DO UPDATE/NOTHING RETURNING`),
not a separate lookup-then-insert, so the database itself is the
tie-breaker under concurrency, not application code.

**Relationships:** 1:many `Employment`. many:1 `Industry` (optional).

**Cardinality:** many `Person`s, via `Employment`, reference one
`Employer`.

**Ownership:** the platform (shared taxonomy), not any one `Person`. Not
deleted when a `Person` is deleted, even if they were its only
referencer yet -- future people may reference it.

**Lifecycle:** created on first reference (typically via `Employment`
creation), then reused. No deactivation concept needed in Sprint 2 (a
defunct company is still a valid historical employer).

**Versioning:** none needed -- `Employer` facts (name, industry) change
rarely and there's no product requirement yet to know "what this
employer used to be called."

### 2.2 Role
**Purpose:** a normalized job title/position taxonomy entry (e.g.
"Senior Backend Engineer"), reusable across many people's `Employment`
records and, longer-term, mappable to standardized `Occupation` codes for
future analytics.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `title` | string(255), not null, indexed | |
| `normalized_title` | string(255), not null, indexed | Same dedup pattern as `Employer.normalized_name`. |
| `seniority_level` | enum(`intern`,`junior`,`mid`,`senior`,`lead`,`principal`,`executive`), nullable | |
| `occupation_id` | UUID, FK -> `occupation.id`, nullable | Maps a free-form title to a standardized occupation, when known. |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `title` non-empty. `normalized_title` has a DB-level
unique index; created via upsert, same pattern and rationale as
`Employer.normalized_name`.

**Relationships:** 1:many `Employment`. many:1 `Occupation` (optional).

**Cardinality:** many `Employment` rows, across many people, may
reference one `Role`.

**Ownership:** the platform (shared taxonomy).

**Lifecycle:** created on first reference, reused thereafter.

**Versioning:** none -- a title's *meaning* doesn't change. **Resolved by
independent review:** a person's title changing at the same employer
(a promotion) is **always** a new `Employment` row, never an in-place
edit of `role_id`/`role_title_raw` on an existing one -- see the
corrected rule in §2.3. Editing `role_id`/`role_title_raw` in place is
reserved strictly for correcting a data-entry mistake, not for
recording a real career event, so it never overwrites real history.

### 2.3 Employment
**Purpose:** the historical record of one person working one role at
one employer for one period. This is the backbone of career history.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `employer_id` | UUID, FK -> `employer.id`, not null | |
| `role_id` | UUID, FK -> `role.id`, nullable | Nullable because a person may record an employment before the title has been normalized into `Role` -- `role_title_raw` covers that gap. |
| `role_title_raw` | string(255), not null | What the person actually typed/held, always stored verbatim even once `role_id` is resolved -- never lose the source fact to normalization. **Immutable in spirit** (see corrected rule below): only ever edited to fix a typo, never to record a title change. |
| `previous_employment_id` | UUID, FK -> `employment.id`, nullable | Set when this row represents a promotion/role change that continues an unbroken tenure at the same employer -- links to the `Employment` row it succeeded, so a full title-change history at one employer is traceable as a chain, not lost. Null for a person's first role at an employer. |
| `employment_type` | enum(`full_time`,`part_time`,`contract`,`freelance`,`internship`), not null | |
| `start_date` | date, not null | |
| `end_date` | date, nullable | Null means ongoing. |
| `is_current` | boolean, not null, default false | Denormalized for query convenience; a service-layer invariant keeps it consistent with `end_date IS NULL`, enforced on write, not by a DB trigger (kept simple per "avoid unnecessary abstraction"). |
| `description` | text, nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `end_date >= start_date` when both present.
`start_date` not in the future. At most one `Employment` per `Person`
may have `is_current = true` **and** `employment_type IN
('full_time','part_time')`, but multiple *concurrent* employments overall
are explicitly allowed (see Data Modelling Principles: "support
concurrent roles") -- e.g. a full-time role plus a concurrent freelance
contract. Enforced with a **partial unique index** on
`(person_id) WHERE is_current AND employment_type IN
('full_time','part_time')` -- a real DB constraint, not just a
service-layer check (independent review finding: DB-level enforcement
is cheap here and worth adding). `previous_employment_id`, when set,
must reference an `Employment` row with the same `person_id` and
`employer_id`, whose `end_date` is not after this row's `start_date`
(service-layer check -- a genuine chain-continuity rule, not
expressible as a simple DB constraint).

**Relationships:** many:1 `Person`, many:1 `Employer`, many:1 `Role`
(optional). 1:many `Achievement` (achievements earned during this
employment). 1:many `PersonSkill`/`PersonTechnology`/`PersonCompetency`
may reference an `Employment` as the context in which that skill was
demonstrated (see §3).

**Cardinality:** one `Person` has many `Employment` rows over time,
including overlapping ones (concurrent roles, explicitly required).

**Ownership:** the person. Deleted when the `Person` is (see §9
cascade policy).

**Lifecycle:** created when the person adds a job; `end_date`/`is_current`
updated when they leave; never hard-deleted on "leaving" -- that's a
normal field update, not a lifecycle transition. Can be deleted only if
the person removes it from their history entirely (a correction, not a
career event). **A promotion or title change at the same employer is
always a new `Employment` row** (`employer_id` unchanged, `start_date`
on/after the prior row's `end_date`, `previous_employment_id` pointing
back at it, and the prior row's `end_date`/`is_current` updated to close
it out) -- **never** an in-place edit of the prior row's `role_id`/
`role_title_raw`. This is a correction of the original draft, made
after independent review found the original wording ("a new row, or an
in-place edit") ambiguous enough that a promotion could silently
overwrite history, violating Principle 3.

**Versioning:** the record itself *is* the historical fact -- there's no
separate "old version" to keep, because ending an employment is a field
update (`end_date` from null to a date), not a fact being overwritten
with a different fact. If a person needs to correct which employer or
dates were recorded (a genuine data-entry correction, not a career
event), that's an in-place edit -- the one and only case where editing
`role_id`/`role_title_raw`/`employer_id` in place is correct, precisely
*because* it isn't recording a new career fact. The model does not
attempt to distinguish "correction" from "career event" via a stored
flag -- the rule above (new row vs. in-place edit) *is* that
distinction, enforced by which fields change and how, not by a separate
audit log (out of scope).

---

## 3. Skills & capabilities

### 3.1 Skill
**Purpose:** an atomic capability taxonomy entry -- the shared,
deduplicated vocabulary of things a person can be skilled at. Deliberately
broad: covers soft skills ("Stakeholder communication"), domain
knowledge ("Payments compliance"), and technical skills alike.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `name` | string(150), not null, indexed | |
| `normalized_name` | string(150), not null, indexed | Dedup, as with `Employer`/`Role`. |
| `skill_type` | enum(`soft`,`domain`,`technical`), not null | |
| `description` | string(500), nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `name` non-empty. `normalized_name` has a DB-level
unique index; created via upsert, same pattern as `Employer`.

**Relationships:** many:many `Person` via `PersonSkill`. many:many
`Competency` via a `CompetencySkill` association (a competency is
*composed of* skills -- see §3.3). Referenced by `Project`/`Achievement`
where relevant (see §5).

**Note on Skill vs. Competency (independent review):** these are
structurally near-identical (taxonomy + person-association + evidence),
differing only in that a `Competency` is explicitly *composed of*
multiple `Skill`s. This is intentional, not accidental duplication --
but future consumers (a matching/recommendation feature, out of scope
here) should treat `Skill` as the atomic, machine-matchable unit and
`Competency` as the human-readable, narrative grouping over skills, not
as two independent, equally-authoritative sources of the same fact.

**Cardinality:** shared across all people; one `Skill` row, many
`PersonSkill` rows.

**Ownership:** the platform (shared taxonomy).

**Lifecycle:** created on first reference, reused thereafter. Never
deleted while any `PersonSkill` references it (restrict, not cascade --
losing taxonomy data because one person removed a skill would corrupt
everyone else's history).

**Versioning:** none -- the taxonomy entry itself doesn't have a
"history," only a person's *possession* of it does (`PersonSkill`, next).

### 3.2 PersonSkill (association entity)
**Purpose:** the actual person-specific fact: "this person has this
skill," carrying everything that's true about *their* possession of it,
not the skill concept itself. This is where "evidence-backed" becomes
concrete for skills.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `skill_id` | UUID, FK -> `skill.id`, not null | |
| `proficiency` | enum(`beginner`,`intermediate`,`advanced`,`expert`), not null | |
| `years_experience` | numeric(4,1), nullable | |
| `last_used_date` | date, nullable | |
| `attribution_source` | enum(`self_reported`,`inferred`,`verified`), not null, default `self_reported`, **not directly client-settable for `verified`** | Principle 2. Corrected after independent review: the original draft let a client set `verified` directly, backed only by a service-layer "must have evidence" check with no DB enforcement -- a real gap in the model's core "evidence-backed, not adjectives" premise, since any future direct write path (bulk import, admin tool) could bypass it. Fixed by making `verified` a **derived value**, not client input: the CRUD API only ever accepts `self_reported` or `inferred` from a client; the service layer recomputes `attribution_source = 'verified'` automatically, on write, whenever >=1 `EvidenceLink` referencing this record exists, and demotes it back to `inferred` if the last such link is removed. There is no code path where a client can set `verified` without evidence existing, because there is no code path where a client sets it at all. |
| `employment_id` | UUID, FK -> `employment.id`, nullable | Optional context: which job this was primarily demonstrated in. |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** unique `(person_id, skill_id)` -- a person has one
proficiency record per skill, updated over time, not duplicated.
`years_experience >= 0`.

**Relationships:** many:1 `Person`, many:1 `Skill`, many:1 `Employment`
(optional). 1:many `EvidenceLink` (as the evidence *subject*).

**Cardinality:** one row per (person, skill) pair.

**Ownership:** the person.

**Lifecycle:** created when a person adds a skill; `proficiency`/
`years_experience`/`last_used_date` updated over time; deleted if the
person removes the skill from their profile.

**Versioning:** current-state, in-place updates -- proficiency
progression over time is a nice-to-have future feature (would need a
`PersonSkillHistory` table), explicitly not built in Sprint 2 (see
Architecture Review, "deferred, not forgotten").

### 3.3 Competency
**Purpose:** a higher-order, demonstrated capability -- broader than a
single skill, evidenced by a *combination* of skills and real proof
(e.g., "Distributed systems design," demonstrated via skills in
messaging, database sharding, and a linked architecture document as
evidence). This is what future matching/recommendation logic is expected
to reason over, more than raw skill lists.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `name` | string(150), not null, indexed | |
| `normalized_name` | string(150), not null, indexed | |
| `description` | string(500), nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `name` non-empty. `normalized_name` has a DB-level
unique index; created via upsert, same pattern as `Employer`.

**Relationships:** many:many `Skill` via `CompetencySkill` (a competency
is composed of >=1 skills). many:many `Person` via `PersonCompetency`.

**Cardinality:** shared taxonomy, like `Skill`.

**Ownership:** the platform.

**Lifecycle / Versioning:** same pattern as `Skill` (§3.1) -- taxonomy
entry is stable; a person's possession is tracked separately.

### 3.4 PersonCompetency (association entity)
**Purpose:** mirrors `PersonSkill` (§3.2) but for competencies --
person-specific proficiency, evidence, and context for a demonstrated
competency.

**Fields:** `id`, `person_id` (FK), `competency_id` (FK), `proficiency`
(same enum as `PersonSkill`), `attribution_source` (same enum, same
derived-not-client-settable-for-`verified` rule as `PersonSkill` §3.2),
`created_at`/`updated_at`.

**Validation:** unique `(person_id, competency_id)`.

**Relationships:** many:1 `Person`, many:1 `Competency`. 1:many
`EvidenceLink`.

**Cardinality:** one row per (person, competency) pair.

**Ownership:** the person.

**Lifecycle / Versioning:** same pattern as `PersonSkill`.

### 3.5 Technology (resolves Framework, Tool, Programming Language)
**Purpose:** a specific named technology a person has used --
programming languages, frameworks, tools, and platforms alike. The
directive names these as four concepts (Technology, Framework, Tool,
Programming Language); on inspection they are the same shape (a named,
shared, technical-skill-like taxonomy entry) differing only by a
category label, and are implemented as **one table with a `category`
discriminator** rather than four near-identical tables that would each
need their own person-association join table, dedup logic, and CRUD
surface for no behavioral difference. This decision is revisited
explicitly in the Architecture Review.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `name` | string(150), not null, indexed | e.g. "Python," "React," "Terraform," "PostgreSQL" |
| `normalized_name` | string(150), not null, indexed | |
| `category` | enum(`language`,`framework`,`tool`,`platform`,`database`,`other`), not null | This field *is* the Framework/Tool/Programming-Language distinction the directive asks for -- queryable (`WHERE category = 'language'`) exactly as if they were separate tables. |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `name` non-empty. `normalized_name` has a DB-level
unique index; created via upsert, same pattern as `Employer`.

**Relationships:** many:many `Person` via `PersonTechnology`. many:many
`Project` via `ProjectTechnology` (§5.1).

**Cardinality:** shared taxonomy, like `Skill`.

**Ownership:** the platform.

**Lifecycle / Versioning:** same pattern as `Skill`.

### 3.6 PersonTechnology (association entity)
**Purpose:** mirrors `PersonSkill` for technologies -- person-specific
proficiency and evidence for a specific technology.

**Fields:** `id`, `person_id` (FK), `technology_id` (FK), `proficiency`
(same enum as `PersonSkill`), `years_experience`, `last_used_date`,
`attribution_source` (same derived-not-client-settable-for-`verified`
rule as `PersonSkill` §3.2), `created_at`/`updated_at`.

**Validation:** unique `(person_id, technology_id)`.

**Relationships:** many:1 `Person`, many:1 `Technology`. 1:many
`EvidenceLink`.

**Cardinality:** one row per (person, technology) pair.

**Ownership:** the person.

**Lifecycle / Versioning:** same pattern as `PersonSkill`.

---

## 4. Credentials

### 4.1 Education
**Purpose:** a record of formal study -- an institution attended, a
field of study, a level, and dates. Represents the *attendance*, whether
or not it resulted in a completed credential (in progress or
discontinued study is still real career history).

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `institution_name` | string(255), not null | Free text, not normalized -- institutions are a far larger, messier taxonomy than employers, and Sprint 2 doesn't need cross-person institution analytics. Documented as a conscious scope limit, not an oversight. |
| `field_of_study` | string(255), nullable | |
| `degree_level` | enum(`high_school`,`associate`,`bachelor`,`master`,`doctorate`,`professional`,`other`), nullable | |
| `start_date` | date, nullable | |
| `end_date` | date, nullable | Null + `is_current=true` means in progress. |
| `is_current` | boolean, not null, default false | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `end_date >= start_date` when both present.

**Relationships:** many:1 `Person`. 1:1 optional -> the `Certification`
concept does **not** attach here; a *degree earned* is represented as
`degree_level` reaching a completion state on this same row, not a
separate `Certification` row (see §4.3 for the boundary rule).

**Cardinality:** one `Person` has many `Education` rows.

**Ownership:** the person.

**Lifecycle:** created when added; updated as study progresses/completes;
deleted if removed by the person.

**Versioning:** current-state, in-place, same as `Employment`.

### 4.2 Certification
**Purpose:** an externally issued credential -- a certification,
license, or professional designation issued by a third party (AWS,
PMI, a state licensing board, etc.), as distinct from a degree earned
through sustained study (`Education`).

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `name` | string(255), not null | |
| `issuing_organization` | string(255), not null | |
| `credential_id` | string(255), nullable | The issuer's own ID for this credential, if any. |
| `issue_date` | date, not null | |
| `expiry_date` | date, nullable | Null means does not expire. |
| `verification_url` | string(500), nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `expiry_date >= issue_date` when present.
`verification_url` must be a valid URL if present.

**Relationships:** many:1 `Person`. 1:many `EvidenceLink` (a
`verification_url` is a *field*; a formally attached, verified `Evidence`
record documenting a check performed against it is a separate, optional
fact -- see §6).

**Cardinality:** one `Person` has many `Certification` rows.

**Ownership:** the person.

**Lifecycle:** created when earned/added; `expiry_date` reached doesn't
delete the row -- an expired certification is still real history, just
no longer current (a computed status, not a stored one, to avoid a stale
boolean that silently drifts from `expiry_date`).

**Versioning:** current-state, in-place, same as `Employment`.

### 4.3 Qualification (conceptual, not a physical table)
**Purpose (as named in the directive):** a formal credential earned by
a person.

**Resolution:** on review, "Qualification" as a standalone concept is
fully covered by `Education` (degrees/diplomas, tracked via
`degree_level`) and `Certification` (externally issued credentials)
together -- there is no third kind of formal credential Sprint 2's scope
needs that isn't one of those two. Rather than add a third table that
would either duplicate `Education`/`Certification` or need to be a
supertype both of them inherit from (adding a join for every query that
touches either), "Qualification" is documented here as the *conceptual
umbrella term* for "`Education` results and `Certification`s, considered
together" -- e.g. a future "list all qualifications" view is a `UNION`
of the two, not a third table to keep in sync with both.

**Fields / Validation / Relationships / Cardinality / Ownership /
Lifecycle / Versioning:** not applicable -- see `Education` (§4.1) and
`Certification` (§4.2).

---

## 5. Work product

### 5.1 Project
**Purpose:** a body of work -- professional or personal -- that
demonstrates skills and technologies in practice. The bridge between
"claims to have a skill" and "evidence of using it."

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `employment_id` | UUID, FK -> `employment.id`, nullable | Set for a professional project done during a specific job; null for personal/independent projects. |
| `title` | string(255), not null | |
| `description` | text, nullable | |
| `role_in_project` | string(255), nullable | e.g. "Tech lead," "Sole contributor." |
| `start_date` | date, nullable | |
| `end_date` | date, nullable | |
| `outcome` | string(500), nullable | Quantifiable result, if any (also expressible as a linked `Achievement` -- see §5.2 for the boundary). |
| `url` | string(500), nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `title` non-empty. `end_date >= start_date` when both
present. `url` must be a valid URL if present.

**Relationships:** many:1 `Person`, many:1 `Employment` (optional).
many:many `Technology` via `ProjectTechnology`. many:many `Skill` via
`ProjectSkill`. 1:many `Achievement` (an achievement earned specifically
through this project). 1:many `EvidenceLink`.

**Cardinality:** one `Person` has many `Project` rows; a `Project` may
reference many `Technology`/`Skill` rows and vice versa.

**Ownership:** the person.

**Lifecycle:** created/updated/deleted by the person directly.

**Versioning:** current-state, in-place, same as `Employment`.

### 5.2 Achievement
**Purpose:** a specific, ideally quantified accomplishment ("Reduced p95
API latency by 40%"), the clearest expression of "evidence, not
adjectives" in this model. Distinguished from `Project.outcome` (a free
text field on the project itself) by being a first-class, evidence-linkable,
independently queryable record -- useful when an achievement doesn't
belong to one project (e.g., "Promoted twice in 18 months" belongs to an
`Employment`, not a `Project`).

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `employment_id` | UUID, FK -> `employment.id`, nullable | |
| `project_id` | UUID, FK -> `project.id`, nullable | |
| `title` | string(255), not null | |
| `description` | text, nullable | |
| `metric_value` | numeric(12,2), nullable | |
| `metric_unit` | string(50), nullable | e.g. "%," "USD," "requests/sec." |
| `achieved_date` | date, nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `title` non-empty. At least one of `employment_id` /
`project_id` may be null (a standalone achievement is valid -- e.g. a
personal milestone), but not required to be mutually exclusive: an
achievement can legitimately belong to a project that itself belongs to
an employment.

**Relationships:** many:1 `Person`, many:1 `Employment` (optional),
many:1 `Project` (optional). 1:many `EvidenceLink`.

**Cardinality:** one `Person` has many `Achievement` rows.

**Ownership:** the person.

**Lifecycle / Versioning:** current-state, in-place, same as
`Employment`.

### 5.3 Publication
**Purpose:** authored content -- an article, paper, patent, or talk --
attributable to the person. Distinguished from `Achievement` by being a
specific, citable, external artifact with its own metadata (venue,
co-authors, publication date), not a generic accomplishment.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `title` | string(255), not null | |
| `publication_type` | enum(`article`,`paper`,`patent`,`talk`,`book`,`other`), not null | |
| `publisher_or_venue` | string(255), nullable | |
| `published_date` | date, nullable | |
| `url` | string(500), nullable | |
| `co_authors` | string(500), nullable | Free-text list; not modeled as related `Person` rows in Sprint 2 -- co-authors are frequently not CareerOS users, and it isn't a "Reference" (§6.2) relationship either. Documented scope limit, not oversight. |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `title` non-empty. `url` must be a valid URL if present.

**Relationships:** many:1 `Person`. 1:many `EvidenceLink`.

**Cardinality:** one `Person` has many `Publication` rows.

**Ownership:** the person.

**Lifecycle / Versioning:** current-state, in-place, same as
`Employment`.

### 5.4 PortfolioItem
**Purpose:** a curated, presentation-layer pointer into the rest of the
model -- "here are the 5 things I most want shown first," referencing an
existing `Project`, `Publication`, or `Achievement` rather than
duplicating its content. This keeps "what to feature" (curation, which
changes often and is opinion, not fact) separate from the underlying
facts (which don't change just because curation preference does).

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `linked_entity_type` | enum(`project`,`publication`,`achievement`), not null | Polymorphic reference, deliberately narrow (three fixed kinds, not a fully generic "any entity") since a portfolio is specifically meant to feature *work product*, not arbitrary facts. |
| `linked_entity_id` | UUID, not null | Interpreted according to `linked_entity_type`; validated at the service layer (no DB-level polymorphic FK -- see Evidence, §6, for why this pattern is used sparingly and deliberately). |
| `display_order` | integer, not null, default 0 | |
| `is_featured` | boolean, not null, default false | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `linked_entity_id` must reference an existing row of the
type named in `linked_entity_type`, owned by the same `person_id`
(service-layer check on write).

**Relationships:** many:1 `Person`. Polymorphic reference to `Project` /
`Publication` / `Achievement`.

**Cardinality:** one `Person` has many `PortfolioItem` rows; a given
`Project`/`Publication`/`Achievement` may be featured in at most one
`PortfolioItem` (unique constraint on `(linked_entity_type,
linked_entity_id)`).

**Ownership:** the person.

**Lifecycle / Versioning:** current-state, in-place; reordering /
featuring is just a field update.

---

## 6. Evidence

### 6.1 Evidence
**Purpose:** the model's answer to "nothing should rely solely on free
text." A first-class record of *proof* -- a URL, a document reference, a
verifier's confirmation, a metric source -- that can be attached to any
claim elsewhere in the model (a skill, a competency, an achievement, a
certification, a project).

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | Evidence belongs to the person it's evidence *for*, even though it can be linked to multiple claims of theirs. |
| `evidence_type` | enum(`url`,`document`,`testimonial`,`metric`,`media`), not null | |
| `title` | string(255), not null | |
| `description` | text, nullable | |
| `source_url` | string(500), nullable | |
| `verified_by` | string(255), nullable | Name/identifier of who verified this, if verified. |
| `verified_at` | timestamptz, nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `title` non-empty. `source_url` must be a valid URL if
`evidence_type = 'url'`.

**Relationships:** many:1 `Person`. 1:many `EvidenceLink` (§6.3) -- this
is the *only* way `Evidence` attaches to other entities, deliberately: a
generic join table, rather than an `evidence_id` FK column added to
every evidence-bearing table (`PersonSkill`, `PersonCompetency`,
`PersonTechnology`, `Certification`, `Project`, `Achievement`,
`Publication`), because (a) one piece of evidence can legitimately back
more than one claim (a single performance review could evidence three
different skills at once), and (b) new evidence-bearing entity types can
be added later without an `ALTER TABLE` on `Evidence` itself.

**Cardinality:** one `Person` has many `Evidence` rows; one `Evidence`
row may back many claims (many:many with "claims," realized through
`EvidenceLink`).

**Ownership:** the person.

**Lifecycle:** created when a person attaches proof; deleted only if
explicitly removed (an `EvidenceLink` being removed does not delete the
underlying `Evidence` if other links still reference it).

**Versioning:** current-state, in-place; a `verified_at` timestamp being
set is itself the meaningful history (evidence moved from unverified to
verified), not something that needs a separate version row.

### 6.2 Reference
**Purpose:** a person who can vouch for the individual -- a professional
reference, with contact details and, optionally, a testimonial.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | The CareerOS user this reference is *for*. |
| `referee_name` | string(255), not null | |
| `referee_title` | string(255), nullable | |
| `referee_employer` | string(255), nullable | Free text, not a normalized `Employer` FK -- the referee's employer at the time of the relationship is a historical fact about the referee, not something CareerOS needs to query across people. |
| `relationship` | string(255), nullable | e.g. "Former manager at Acme." |
| `contact_email` | string(255), nullable | |
| `contact_phone` | string(50), nullable | |
| `can_contact` | boolean, not null, default false | Explicit consent flag -- must be true before any future feature may reach out to this person (enforced by consuming features, not this table, but the flag exists here as the source of truth). |
| `testimonial_text` | text, nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Correction from independent review:** the original draft gave
`Reference` its own direct `evidence_id` FK straight to `Evidence`,
alongside every other evidence-bearing entity going through
`EvidenceLink`. That was an inconsistent second pattern, and it silently
capped a `Reference` at exactly one piece of evidence for no stated
reason -- undercutting the very reason `EvidenceLink` exists (one
`Evidence` row, e.g. a single written recommendation, backing more than
one claim). Removed; a `Reference`'s testimonial, if captured as formal
`Evidence`, is linked the same way as everything else -- see
`EvidenceLink.subject_type` (§6.3), which now includes `reference`.

**Validation:** `referee_name` non-empty. `contact_email` valid email
format if present.

**Relationships:** many:1 `Person`. 1:many `EvidenceLink` (as the
evidence *subject*, same pattern as every other evidence-bearing
entity).

**Cardinality:** one `Person` has many `Reference` rows.

**Ownership:** the person.

**Lifecycle / Versioning:** current-state, in-place, same as
`Employment`.

### 6.3 EvidenceLink (association entity)
**Purpose:** the generic join that attaches one `Evidence` row to one
claim elsewhere in the model. This is the mechanism, not a concept named
directly in the directive, but required to make Evidence (§6.1)
actually work as "first-class" and attachable per the Data Modelling
Principles.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `evidence_id` | UUID, FK -> `evidence.id`, not null | |
| `subject_type` | enum(`person_skill`,`person_competency`,`person_technology`,`certification`,`education`,`project`,`achievement`,`publication`,`reference`), not null | Corrected after independent review: `education` was missing from the original enum with no stated rationale (an oversight, not a scope decision -- diplomas/transcripts are an obvious evidence case in the Credentials group), and `reference` was added as part of removing `Reference.evidence_id` (see §6.2). |
| `subject_id` | UUID, not null | Interpreted according to `subject_type`; validated at the service layer. |
| `created_at` | timestamptz, not null | |

**Validation:** `subject_id` must reference an existing row of the named
type, owned by the same `person_id` as the `Evidence` row (service-layer
check).

**Relationships:** many:1 `Evidence`. Polymorphic reference to one of
the nine subject types listed above.

**Cardinality:** many:many between `Evidence` and "claims," realized as
one row per (evidence, subject) pair. Unique `(evidence_id, subject_type,
subject_id)`.

**Ownership:** the person (via the `Evidence` row).

**Lifecycle:** created when evidence is attached to a claim; deleted when
detached (does not delete the `Evidence` row itself, per §6.1).
**Orphan-cleanup rule (independent review finding -- this was missing
entirely from the original draft):** because `subject_id` is not a real
foreign key, deleting a subject row (a `PersonSkill`, `Project`,
`Achievement`, etc. -- all of which are deletable per their own
lifecycle rules) does nothing to referencing `EvidenceLink` rows at the
database level, and would silently orphan them. **The service layer
must delete all `EvidenceLink` rows referencing a subject in the same
transaction as deleting that subject.** The same rule applies to
`PortfolioItem.linked_entity_id` (§5.4) for the same reason -- both are
documented once here rather than repeated, since it's one rule applied
to two polymorphic-reference fields in this model.

**Versioning:** none -- it's a link, not a fact with its own history.

---

## 7. Preferences & goals

### 7.1 CareerGoal
**Purpose:** an aspirational target -- what the person wants next,
explicitly modeled (not inferred) so future recommendation features have
a real, person-stated target to reason against.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `goal_type` | enum(`role`,`industry`,`skill_development`,`salary`,`other`), not null | |
| `description` | string(500), not null | |
| `target_date` | date, nullable | |
| `priority` | enum(`low`,`medium`,`high`), not null, default `medium` | |
| `status` | enum(`active`,`achieved`,`abandoned`), not null, default `active` | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `description` non-empty.

**Relationships:** many:1 `Person`.

**Cardinality:** one `Person` has many `CareerGoal` rows.

**Ownership:** the person.

**Lifecycle:** created when set; `status` transitions
`active` -> `achieved`/`abandoned` over time; not deleted on completion
(an achieved goal is meaningful history for future "how this person's
goals evolved" analytics).

**Versioning:** the `status` field *is* the lifecycle/versioning
mechanism here -- no separate history table needed for something this
simple.

### 7.2 LocationPreference
**Purpose:** where and how the person is willing to work, geographically.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, not null | |
| `location_text` | string(255), not null | e.g. "London, UK" or "Remote (UK-based)." Free text deliberately -- geocoding is a future concern, not Sprint 2's. |
| `preference_type` | enum(`remote`,`hybrid`,`onsite`), not null | |
| `willing_to_relocate` | boolean, not null, default false | |
| `max_commute_minutes` | integer, nullable | |
| `priority_rank` | integer, not null, default 0 | Lower = more preferred, when a person lists more than one acceptable location. |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `location_text` non-empty. `max_commute_minutes >= 0`
if present.

**Relationships:** many:1 `Person`.

**Cardinality:** one `Person` has many `LocationPreference` rows (they
may accept several locations, ranked).

**Ownership:** the person.

**Lifecycle / Versioning:** current-state, in-place.

### 7.3 WorkPreference
**Purpose:** how the person wants to work -- employment type, arrangement,
and soft preferences that don't fit `LocationPreference` or
`SalaryPreference`.

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, unique, not null | One row per person (unlike `LocationPreference`, these aren't ranked alternatives -- they're a single current preference set). |
| `preferred_employment_types` | array(enum, same as `Employment.employment_type`), not null, default `[]` | |
| `company_size_preference` | enum(`startup`,`scaleup`,`midsize`,`enterprise`,`no_preference`), not null, default `no_preference` | |
| `culture_values` | array(string), not null, default `[]` | Free-form tags (e.g. "async-first," "flat structure"); intentionally unconstrained, since this is stated preference, not a claim needing evidence. |
| `available_from` | date, nullable | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** none beyond type checks -- this is preference data, low
validation stakes by design.

**Relationships:** 1:1 `Person`.

**Cardinality:** exactly one `WorkPreference` per `Person` (created
lazily on first write, not automatically like `CareerProfile`, since
many people won't set this immediately).

**Ownership:** the person.

**Lifecycle / Versioning:** current-state, in-place.

### 7.4 SalaryPreference
**Purpose:** compensation expectations. Kept separate from
`WorkPreference` because it has meaningfully different sensitivity
(financial data) and a different natural lifecycle (people update salary
expectations more often, and independently of other work preferences).

**Fields:**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID, PK | |
| `person_id` | UUID, FK -> `person.id`, unique, not null | |
| `currency` | string(3), not null | ISO 4217 code. |
| `min_amount` | numeric(12,2), not null | |
| `max_amount` | numeric(12,2), nullable | |
| `period` | enum(`annual`,`monthly`,`hourly`,`daily_rate`), not null | |
| `is_negotiable` | boolean, not null, default true | |
| `effective_date` | date, not null | |
| `created_at` / `updated_at` | timestamptz | |

**Validation:** `max_amount >= min_amount` when present. `currency`
matches ISO 4217 3-letter format. `min_amount > 0`.

**Relationships:** 1:1 `Person`.

**Cardinality:** exactly one *current* `SalaryPreference` per `Person`.

**Ownership:** the person.

**Lifecycle:** updated in place as expectations change.

**Versioning:** `effective_date` is retained specifically so that, if a
future sprint decides salary expectation history matters (e.g. for
market-rate trend analysis), the field is already there -- but Sprint 2
does not build a history table for it; updates overwrite in place. This
mirrors the same "field exists, full history table deferred" pattern
used elsewhere and is called out explicitly, not left implicit.

---

## 8. Taxonomy (shared reference data)

**Forward note on multi-tenant SaaS (independent review):** every
taxonomy table in this section assumes one global, platform-wide
namespace (`name`/`normalized_name` unique across all of CareerOS, not
per-tenant). Multi-tenancy is explicitly out of scope for this sprint,
and this assumption does **not** require a redesign to relax later: a
future tenant-private taxonomy extension is additive (a companion table
scoping certain rows to a tenant, with global rows remaining shared) --
not a change to the tables below. Noted here so it's a known,
already-considered forward compatibility question if it comes up, not a
surprise.

### 8.1 Industry
**Fields:** `id`, `name` (unique), `parent_industry_id` (FK ->
`industry.id`, nullable, self-referential for a hierarchy e.g.
"Financial Services" > "Fintech"), `created_at`/`updated_at`.
**Purpose:** standardized industry taxonomy. **Relationships:** self-
referential hierarchy; referenced by `Employer`, `CareerProfile`.
**Ownership:** platform. **Lifecycle:** seeded + grown by admin/service
processes (no public CRUD in Sprint 2 -- see Architecture Review, API
surface). **Versioning:** none.

### 8.2 JobFamily
**Fields:** `id`, `name` (unique), `parent_job_family_id` (FK ->
`job_family.id`, nullable, self-referential), `description`,
`created_at`/`updated_at`.
**Purpose:** standardized grouping of related occupations (e.g.
"Software Engineering" within "Engineering"). **Relationships:** self-
referential hierarchy; 1:many `Occupation`. **Ownership:** platform.
**Lifecycle:** seeded + grown by admin/service processes. **Versioning:**
none.

### 8.3 Occupation
**Fields:** `id`, `name`, `standard_code` (string, nullable -- e.g. an
O*NET/SOC code, for future external data alignment), `job_family_id`
(FK, nullable), `description`, `created_at`/`updated_at`.
**Purpose:** standardized occupation taxonomy that `Role` entries can
map to, enabling future cross-person analytics without relying on raw
job titles. **Relationships:** many:1 `JobFamily`; 1:many `Role`.
**Ownership:** platform. **Lifecycle:** seeded + grown by admin/service
processes. **Versioning:** none.

---

## 9. Cross-cutting: ownership, lifecycle, and versioning strategy

**Ownership (ties together every "Ownership" line above):** two kinds of
rows exist in this model:
- **Person-owned** (`Person`, `CareerProfile`, `Employment`, `Education`,
  `Certification`, `Project`, `Achievement`, `Publication`,
  `PortfolioItem`, `Evidence`, `Reference`, `CareerGoal`,
  `LocationPreference`, `WorkPreference`, `SalaryPreference`,
  `PersonSkill`, `PersonCompetency`, `PersonTechnology`, `EvidenceLink`):
  `ON DELETE CASCADE` from `Person`. Deleting a person's account deletes
  all of these -- there is no soft-delete/anonymization requirement in
  this sprint's scope (out of scope per the directive: no privacy/GDPR
  workflow requested), but cascading hard deletes are the correct default
  until one is.
- **Platform-owned / shared taxonomy** (`Employer`, `Role`, `Skill`,
  `Competency`, `Technology`, `Industry`, `JobFamily`, `Occupation`):
  `ON DELETE RESTRICT` from anything that references them. A `Person`
  being deleted never deletes shared taxonomy data; a taxonomy row can
  only be deleted (an admin operation, out of scope for Sprint 2's public
  API) once nothing references it.

**Lifecycle (ties together every "Lifecycle" line above):** every
Person-owned entity follows one of two patterns, stated once here rather
than repeated as boilerplate on each entity:
- **Fact entities** (`Employment`, `Education`, `Certification`,
  `Project`, `Achievement`, `Publication`, `Reference`, `CareerGoal`):
  created when the person adds the fact, updated in place as details
  change, deleted only if the person removes it entirely (a correction,
  not a career event -- ending a job is a field update, not a delete).
- **Singleton state entities** (`CareerProfile`, `WorkPreference`,
  `SalaryPreference`): exactly one row per person, updated in place,
  never deleted while the person exists.

**Versioning strategy (the directive's "career history must be
versionable" requirement, answered once, precisely):** two different
things could be meant by "versionable," and this model deliberately
picks the one with real product value now, while leaving room for the
other later without a redesign:
1. **"A career fact, once true, stays visible even after it's no longer
   current."** -- Met directly: `Employment`, `Education`, `Certification`
   etc. are never deleted when they end, only updated (`end_date` set,
   `is_current` flipped). This is the versioning that matters for "show
   this person's full career history," and it's built now.
2. **"Every edit to every field is retained as a full version history
   (audit log / event sourcing)."** -- Not built in Sprint 2. This would
   be real, unnecessary complexity today (a generic versioning/event
   table, or per-table history tables, for entities with no current
   consumer of that history) -- explicitly the kind of premature
   abstraction the directive itself warns against ("do not optimise
   prematurely," "avoid unnecessary abstraction"). The one place this
   sprint *does* build toward it is `CareerProfile`, via a
   `CareerProfileSnapshot` table (point-in-time copies of the aggregate,
   taken on an explicit "snapshot" service call -- not automatic on every
   edit), because that's the one entity the directive and product intent
   both call out as needing a "how has this person's profile grown over
   time" view. Everything else's "versioning consideration" is: the
   fact-entity pattern above already provides history; full audit
   versioning is deferred and tracked as technical debt (see
   `docs/TechnicalDebt.md` TD-013), not silently skipped.
