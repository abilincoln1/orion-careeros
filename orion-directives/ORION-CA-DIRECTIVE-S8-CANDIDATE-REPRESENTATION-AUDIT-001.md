Project ORION / CareerOS — Chief Architect Directive

Directive ID: ORION-CA-DIRECTIVE-S8-CANDIDATE-REPRESENTATION-AUDIT-001

To: Claude, Engineering Assistant
From: Chief Solutions Architect / ORION Architecture Review Board
Subject: Candidate Representation Audit — Skills, Experience, Projects and Career Direction
Status: Analysis and evidence collection only unless separately authorised.

1. Authority and Purpose

Directives S4 through S7 investigated Job Discovery relevance primarily through variations of job-title-based candidate representation.

Those experiments established useful negative evidence:

the latest-employment-title heuristic is insufficient;
enriching one narrow title with selected skills improved precision but collapsed volume;
the historical identity Applications Packager performed poorly against the live provider inventory.

These results do not establish that skills-, experience-, technology- or project-based discovery is ineffective.

The Chief Architect has identified a material representation gap:

The current discovery experiments may not adequately represent the candidate's current Systems Engineer experience, broader technical history, automation and AI capability, demonstrated project work, or current career direction.

This directive authorises an evidence-based audit of that gap.

No production capability is authorised by this directive.

2. Repository Protection Gate

Before any analysis, run:

git status
git status --short
git diff --cached --stat
git rev-parse HEAD
git describe --tags --exact-match HEAD

Record:

HEAD;
release tag;
staged files;
untracked files;
modified files.

The published release baseline remains:

HEAD: 56bccb2
Release: v0.5.0-ui-mvp

Do not assume the working tree matches any previously reported state.

Absolute restrictions

Do not:

git add -A
git commit -am
git reset --hard
git clean -fd

Do not alter:

existing commits;
existing release tags;
remote history.

No commit, tag or push is authorised.

3. Central Question

Determine, using the candidate's actual persisted CareerOS data and available project evidence:

What technically evidenced representation of this candidate should Job Discovery consume if the objective is to discover current and adjacent opportunities rather than merely repeat historical job titles?

This is an investigation.

Do not implement the answer yet.

4. Required Candidate Evidence Audit

Inspect the actual persisted candidate data.

Determine what CareerOS currently contains for:

A. Employment

Inspect all employment records.

Record:

role titles;
employers;
chronology where available;
responsibilities or descriptions where actually stored;
repeated role patterns;
most recent role.

Do not infer responsibilities that are not stored.

B. Skills

Extract and categorise all persisted skills.

Identify evidence for categories such as:

Systems Engineering;
Endpoint Management;
Application Management;
Infrastructure;
Cloud;
Automation;
AI;
Cybersecurity;
Networking;
Other technical domains actually evidenced.

Do not invent missing skills.

C. Technologies and Tools

Determine whether technologies are currently represented:

explicitly as structured data;
implicitly inside skills;
inside CV text;
or not persisted at all.

Examples relevant to this audit may include only where actually evidenced:

SCCM/MECM;
Intune;
Active Directory;
PowerShell;
Windows infrastructure;
Docker;
Python;
FastAPI;
PostgreSQL;
AWS;
automation platforms;
AI/LLM technologies.

The purpose is to establish what is actually available to CareerOS, not what could theoretically be added.

D. Current Systems Engineer Experience

Determine whether the candidate's current Systems Engineer experience is:

represented in Employment;
represented in extracted skills;
represented elsewhere;
available to Job Discovery;
actually consumed by Job Discovery.

If the candidate's current role is missing, incomplete, or not represented in the extracted data, state this explicitly.

Do not silently correct the data.

E. Automation and AI Experience

Inspect whether the candidate's demonstrated automation and AI experience is represented anywhere currently accessible to CareerOS.

Distinguish carefully between:

1. Persisted CareerOS evidence
2. Evidence available elsewhere in the repository
3. Evidence known from project work but not represented in CareerOS

Do not collapse these categories.

F. Project Evidence

Inspect whether CareerOS currently has structured or accessible evidence of the candidate's technical projects.

Determine specifically whether projects such as:

NDIP;
CareerOS;
AI/automation implementations;

are:

Persisted and queryable
Repository evidence only
Not represented

Do not add project records.

5. Current Discovery Consumption Audit

Trace exactly what Job Discovery currently reads from the candidate.

Produce a source-to-consumption map:

Candidate Evidence
        ↓
CareerOS Persistence
        ↓
Discovery Criteria
        ↓
Provider Fetch
        ↓
Local Filtering
        ↓
Persisted Job Listings
        ↓
UI

For every evidence category identified above, classify it as:

Evidence	Exists?	Persisted?	Read by Discovery?	Used in Query?	Used in Filtering?

This table is mandatory.

6. Representation Gap Analysis

Identify the difference between:

What the candidate demonstrably is

and

What Job Discovery currently represents the candidate as.

Do not describe this abstractly.

Use concrete evidence.

The analysis must answer:

Is Job Discovery effectively representing only one job title?
Are skills being ignored?
Is current Systems Engineer experience represented?
Is automation experience represented?
Is AI experience represented?
Is project evidence represented?
Are Career Preferences actually operational?
Which evidence already exists but is unused?
Which relevant evidence does not exist in CareerOS at all?
7. Market-Identity Analysis

Do not assume historical job titles represent the candidate's current market identity.

Based strictly on evidenced employment, skills and demonstrated technical work, identify up to five candidate capability domains.

These are not job searches and are not job titles selected for implementation.

Examples of the form expected:

Endpoint / Systems Engineering
Infrastructure and Platform Operations
Cloud Engineering
Technical Automation
Applied AI / AI-enabled Automation

The actual domains must be derived from evidence.

For each domain provide:

supporting evidence;
whether CareerOS currently stores it;
whether Job Discovery currently consumes it;
confidence level.

Do not invent market demand or claim that a domain is employable without evidence.

8. Architecture Boundary

This directive does not authorise:

multi-query discovery;
ranking;
scoring;
a second provider;
new Career DNA entities;
schema changes;
new APIs;
Career DNA writes;
project CRUD;
application tracking;
AI-generated search queries;
LLM analysis;
changes to matching;
changes to provider integration.

If the audit identifies that any of these might eventually be useful, record them only as unimplemented possibilities.

Do not build them.

9. Required Evidence Test

Before recommending any implementation, answer this question:

Is there already enough structured, persisted candidate evidence inside CareerOS to construct a materially better discovery representation, or is the real bottleneck missing candidate data?

Select exactly one:

Outcome A — Existing Evidence Is Sufficient

CareerOS already contains enough persisted evidence. The problem is primarily that Job Discovery does not consume it.

Outcome B — Existing Evidence Is Partially Sufficient

Some useful evidence exists, but material parts of the candidate's current profile are absent or inaccessible.

Outcome C — Candidate Representation Is Fundamentally Incomplete

CareerOS does not currently contain enough structured evidence to test a broader representation honestly.

The classification must be evidence-based.

10. No Implementation Experiment

This directive is analysis only.

Do not perform another query experiment.

Do not temporarily modify the discovery service.

Do not add query_override.

Do not alter Docker configuration.

Do not clear job data.

Do not rebuild the architecture.

The purpose is to establish whether the next experiment would even be testing a valid representation.

11. Required Report

Create:

docs/S8-CANDIDATE-REPRESENTATION-AUDIT.md

The report must contain:

Repository baseline.
Candidate employment evidence.
Candidate skills evidence.
Technology/tool evidence.
Current Systems Engineer representation.
Automation and AI evidence.
Project evidence.
Career Preference status.
Source-to-consumption map.
Representation gap analysis.
Candidate capability domains.
Outcome A, B or C.
Exact evidence supporting that outcome.
What Job Discovery currently represents.
What CareerOS demonstrably knows but does not use.
What relevant information is missing from CareerOS.
Smallest possible next validation question.
12. Critical Interpretation Rule

Do not conclude:

"Applications Packager failed, therefore the candidate has no useful discovery identity."

That conclusion is unsupported.

S7 tested one historical identity against one provider using one representation.

Likewise, do not conclude that skills-based discovery works or fails.

It has not yet been properly tested using a complete audit of what candidate evidence CareerOS actually possesses.

13. Stop Condition

After:

repository verification;
candidate evidence audit;
discovery consumption trace;
representation gap analysis;
outcome classification;
creation of the S8 report;

run:

git status
git diff
git diff --cached

Report the repository state.

Then stop.

No commit.
No tag.
No push.
No implementation.
No second experiment.

The final response must end:

STOP — S8 complete. Candidate representation audited, no implementation performed, no commit, no tag, no push. Awaiting Chief Architect review and next directive.