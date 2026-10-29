# Integration contracts

See [IDENTITY.md](IDENTITY.md) for the identity contract.

Status: schema, resolver, tool names and event wire types are specified in
`manager/internal/integration` with tests. Production instance loading now
resolves the shipped builtin manifests. Selection gates startup, MCP tools,
portal adapters, catalog entries, prompt sections and readiness. Instance
`integration_grants` is an explicit operator-supplied snapshot during this
builtin transition; stored grants and service tokens remain subsequent work.
Consent storage, durable deletion jobs, event transport and the scoped API
remain contracts, not claims about today's deployment. See [INSTALL.md](INSTALL.md) for minimal-instance validation.

The first public release does not require a service API. Any early API is experimental `v1alpha`, or
absent. The stable `/api/v1` promise below starts only when explicitly released;
writing this document does not announce that release or change the proof of
concept's general support policy.

## 1. Integration manifest, schema 1, and resolver

`Load(io.Reader)` loads JSON; `LoadYAML(io.Reader)` loads YAML using the
already-present `go.yaml.in/yaml/v3` dependency. Shipped examples use
`deploy/integrations/<name>/manifest.json`. No dependency was added. Both
formats have the same fields. Exactly one document is accepted; duplicate
keys, unknown fields, wrong field case, null contract fields and incorrect
value types fail. YAML anchors, aliases, merge keys and custom tags fail.
Omit an optional field instead of setting it to null. Settings schemas may
contain arbitrary keys and null values internally.

```json
{
  "schema": 1,
  "name": "report",
  "version": "1.2.0",
  "runs": "service",
  "requires_core": ">=1.4 <2",
  "requires_opencode": ">=2.2.0 <2.3",
  "requires": ["feedback"],
  "enabled_by_default": false,
  "mcp": "/mcp",
  "tools": ["summary"],
  "events": ["chat.finished", "account.deleting", "consent.changed"],
  "event_consumer": "report",
  "scopes": ["transcripts:read", "llm.background"],
  "portal": [{"path": "/report", "roles": ["admin"]}],
  "consent": {"required": true, "version": 1, "text": "consent.de.md", "text_en": "consent.en.md"},
  "holds_personal_data": true,
  "deletion_contract": "v1",
  "health": "optional",
  "limits": {"timeout_s": 30, "concurrency": 4, "llm_eur_month": 20},
  "owner": {"name": "Operations", "contact": "ops@example.org"}
}
```

That example requires an installed, selected `feedback` integration and
admin grants before it resolves. A service's image or instance-provided URL
is a deployment concern; the loader does not connect to it. An image, when
present, must end in `@sha256:` and 64 lowercase hex digits, for example
`registry.example.org/report@sha256:` followed by its actual digest, never a
placeholder or a tag alone.

| Field | Schema-1 rule |
|---|---|
| `schema`, `name`, `version`, `runs` | Required. Schema is integer 1. Name is at most 40 ASCII characters, starts with a lowercase letter, contains lowercase letters/digits with single internal hyphens; `base` is reserved for consent. Runs is `none`, `builtin`, or `service`. |
| `version` | Three or four unsigned decimal components, no leading zeroes except `0`: `1.2.0` or the repository's CalVer `2026.10.27.1`. No prerelease/build suffix. This is comparison syntax, not a promise that the product adopts SemVer. |
| `requires_core`, `requires_opencode` | Optional AND of whitespace-separated comparisons `=`, `>`, `>=`, `<`, `<=`; bare version means equality. Bounds have one to four components, missing trailing components mean zero. `>=1.4 <2` works; wildcards, OR, caret, tilde, commas and split operators do not. No requirement means no check; a declared requirement needs a valid supplied version. Declare the OpenCode range whenever tools, catalog reload or runtime behavior are relied on; the old plan's `2.0.30` example is not the supported M1 runtime. |
| `requires`, `conflicts` | Lists of integration names, no duplicates or self-reference. No implicit dependency installation/activation. A one-sided conflict is sufficient to fail. An absent conflicting integration is harmless. |
| `enabled_by_default` | Boolean, default false. An instance's explicit true/false overrides it. This selects an instance integration; it grants no per-person consent, catalog access or scope. |
| `image` | Optional digest-pinned image, only with `runs: service`. Builtins run in the manager; `none` has no process. |
| `skills`, `prompt` | Integration-relative paths. No absolute path, dot/parent segments, backslashes, percent escapes or colon. A trailing slash on a skills directory is accepted. Files are not read by this package; the renderer must also enforce containment through symlinks and existence. Skills for a service stay local and available while the service is down. |
| `mcp` | Service-relative canonical path such as `/mcp` only with `runs: service`, or `{"url":"https://tools.example.org/mcp","auth_secret":"TICKET_TOKEN"}`. HTTP permits an internal service network; remote transport security is deployment policy. No URL userinfo, query or fragment. Secret references match `[A-Z][A-Z0-9_]*`; never embed a secret. Builtin registries need no MCP URL. |
| `tools` | Local exported names, validated under §2. Required as a complete inventory before activation by a future registrar. Non-builtin tools require `mcp`. Discovery must match the declared inventory; never silently drop a duplicate. |
| `events`, `event_consumer` | Known §5 event names, unique per manifest. A consumer defaults to the integration name; an explicit name has the integration-name grammar and requires subscriptions. `runs: none` cannot consume events. Different consumers may subscribe to the same event type. |
| `scopes` | Unique known scopes from §7, requested only. No implicit grants. Unknown scopes fail closed. |
| `portal` | Unique canonical absolute paths, nonempty unique role names using the name grammar. No root `/`, trailing slash, dot segments, escaping, query, fragment, whitespace or route wildcards. `runs: none` has no pages. Paths reserve exact entry routes, not arbitrary subtrees. Role checks remain server-side. |
| `settings`, `person_settings` | JSON schema objects, opaque to this contract loader. They describe settings, not secret-bearing instance values. Settings-schema dialect and value validation belong to the renderer; this loader does not claim full JSON Schema validation. |
| `consent` | Optional §3 declaration. `required` defaults false. Required consent needs positive integer `version` and local `text`; `text_en` is optional. Any supplied consent text needs a positive version. |
| `holds_personal_data`, `deletion_contract` | Data declaration defaults false. Non-builtin data holders must declare `deletion_contract: "v1"`; any other nonempty value fails. Builtins use the always-registered cleanup obligation in §4. A declaration is not proof that the cleanup has been implemented. |
| `health` | Omitted means optional; otherwise `optional` or `critical`. Optional failure degrades that integration, not core health. |
| `limits` | Nonnegative `timeout_s`/`concurrency` integers and finite `llm_eur_month` number. Omitted/zero selects the instance's bounded default, never unlimited execution or a free budget. Actual defaults are selected during runtime wiring. |
| `owner` | Optional; if present, nonblank `name` and `contact`. Contact is an operator address, not a credential. |

New fields that close gaps in the plan are `enabled_by_default`, `tools`,
`event_consumer`, `consent.version` and `deletion_contract`. They make selection,
collisions, consent updates and remote deletion capability explicit.

`Resolve(manifests, Options)` validates every supplied manifest and rejects
duplicate integration names, including disabled ones. Unknown instance switch
names fail, even if set to false. It then validates the selected set:

1. Check core and OpenCode versions, enabled dependencies, one-sided conflicts.
2. Check requested scopes against the separate admin grant snapshot.
3. Reject rendered tool-name, exact portal-path and consumer-ID collisions.
4. Reject dependency cycles; return deterministic dependency-first order,
   sorting independent names and dependency traversals lexically.

A disabled integration's valid but unmet version/dependency/grant requirements
are inert. Collision checks also concern only the selected set. Dependency
cycles in an entirely disabled set cannot execute and are not activation
errors. Grant rows for removed/disabled integrations may persist and are
ignored by this resolver. Every selected integration's grant list must contain
known, unique scopes. Surplus known grants do not add requested capabilities.

For example, `pdf` is on by default; `{pdf: false}` overrides that. Selecting
`workspace-style` while disabling `pdf` fails because it requires `pdf`. An empty
manifest list, or explicit false for all defaults, resolves to an empty set.
Core/catalog must still work in that state. Revocation is immediate at the
policy point; prompt/catalog refresh may wait for the current chat. Switching
off never purges data or removes deletion obligations.

Errors return no partial result. First startup must fail; a reload must keep
the last applied set. The caller owns that atomic publication and retention;
this pure resolver never changes runtime state or chooses an older release.
Failed scope escalation keeps an *already applied* release, not a downgrade.

Versioning: schema 1 evolves additively; existing meanings do not change.
A breaking shape/meaning requires schema 2 and the §6 overlap period once
stable. Strict authoring validation intentionally rejects fields unknown to
this core: a manifest using new fields must declare the minimum core version
that understands them. Backward compatibility means newer loaders accept old
schema-1 manifests, not that older policy validators ignore new authority.

The minimal instance permits file work and denies shell execution. Optional web
tools and other integrations require explicit configuration. Extracting a builtin
into a separate reference service remains future work.

## 2. Tool naming

One MCP server per integration; client-visible name is exactly
`<integration>_<tool>`. Local tools match `[a-z][a-z0-9]*(_[a-z0-9]+)*` and the
complete name is at most 64 ASCII characters. Hyphens in integration names stay
literal. Integration names cannot contain underscores, making the boundary
unambiguous. Two integrations can each export `fetch`; two identical local
names in one manifest fail. No normalization or silent deduplication.

```text
{{tool pdf.md_to_pdf}}       -> pdf_md_to_pdf
{{tool nextcloud.fetch}}     -> nextcloud_fetch
{{tool workspace-rooms.rooms_free}} -> workspace-rooms_rooms_free
```

`ToolName` validates and joins names. Template parsing and checking that a
reference is exported by an enabled integration belong to the next renderer
step. Skills/prompts use references, never literal client tool names. A skill's
`requires_tools` frontmatter controls availability. Readiness waits only for
selected MCP servers; an empty selection cannot wait for the old builtin server.
Every invocation still passes consent, account, catalog, budget, identity and
untrusted-content policy, including central MCPs transported by LiteLLM.

Builtin tools currently share the instance-selected server name. `LegacyTool`
keeps existing local handler names, except Nextcloud's explicit prefix. Minimal
has no configured builtin tools and no readiness wait. Separate-server naming
is a contract; moving existing chats and skills requires coordinated migration.

Versioning: changing an exported name or template reference is a breaking
integration contract. During migration the renderer and its skills must move
together; any temporary alias must be explicitly declared and collision-tested.
Schema/API versioning follows §6, not an accidental server rename.

Separate-server naming is specified here. Empty-selection readiness is implemented;
migrating the existing shared builtin server remains future work.

## 3. Consent per integration

Store one decision per `(uid, scope)`, where scope is `base` or an integration
name. A row records the accepted text version and acceptance/revocation time.
Base consent is mandatory; a required integration consent independently gates
that integration for the person. Enabling an instance integration or granting
its scopes never accepts a person's consent.

```text
(uid=person-1, scope=base,       version=3, accepted=true)
(uid=person-1, scope=evaluation, version=1, accepted=true)
evaluation manifest changes consent.version to 2 -> evaluation inactive
person accepts version 2 -> evaluation eligible again, subject to policy
person revokes evaluation -> its tools and background access denied immediately
```

Changing either language's consent text bumps the integration consent version.
Acceptance of an older version cannot satisfy a newer one. `text` is the
fallback; `text_en` supplies the English variant of the same decision.
`transcripts:read` always requires a current integration consent row, even if a
misconfigured manifest omitted `consent.required`. It also requires valid base
consent and an active account. Filter every scoped read and audit it.
Background work rechecks both consent scopes and account state at execution,
before each paid call, and transactionally at commit. A queued event or token
cannot preserve withdrawn authorization. Emit `consent.changed` in the same
transaction as each acceptance/revocation; a manifest text revision invalidates
old acceptances even before notifications arrive.

Revocation disables access; it does not silently delete stored results. Export
and account deletion remain available through the core account procedures.

Versioning: consent versions are positive integers per scope, independent of
manifest versions and the base version. Never reuse a version for changed
text. Storage/API breaking changes follow §6; the current global consent table
is not migrated by this package.

Open work: provide notice texts and migrate global consent during runtime wiring.
This contract does not convert existing consent into per-integration acceptances.

## 4. Durable deletion job

A durable operation has a stable operation ID and states `revoking`,
`purging_core`, `waiting_obligations`, `blocked`, `complete`. Start is
idempotent for an already-deleting account. Persist progress so a crash or
restart resumes the same operation; cleanup and acknowledgements are
idempotent. A timeout never turns failure into success.

1. Revoke login, new work and person-context tokens immediately. Persist the
   deleting state and generation fence before asynchronous work. Cancel or
   fence in-flight work; its later writes must fail.
2. Purge core containers, workspace and core personal-data tables independently
   of optional integration availability. Keep minimal operation/tombstone
   metadata required to prevent stale writes and track obligations.
3. Create one obligation per integration that ever held data, from a persisted
   data-holder registry. Register before the first personal-data write; it must
   serialize with deletion so a late writer cannot escape the snapshot.
4. Acknowledge an obligation using the authenticated integration identity plus
   deletion operation ID. Builtin cleanup callbacks are always registered,
   including when disabled, and acknowledge synchronously after success.
5. Retry failed obligations. After the configured deadline, mark `blocked` and
   list outstanding integrations. Complete only after core purge and every
   obligation's acknowledgement or recorded operator resolution.

```json
{"operation_id":"delete-17","integration":"nextcloud","status":"acknowledged"}
```

The authenticated integration must equal `integration`; a different operation
or integration cannot be acknowledged. A repeated successful ack has the same
result. Deletion acknowledgement is a narrowly scoped exception to the normal
post-revocation write ban and remains possible after the person row is purged.
A removed integration keeps its persisted identity/owner and obligation; its
absence from the desired manifests is not completion. Independent deletion
credentials must remain available for that operation.

For a blocked job: verify the integration/operation, contact its recorded
owner, retry or manually purge, then record the operator, time, evidence and
resolution note. Never silently discard an obligation. Operator resolution is
an auditable alternative to an authenticated service ack, not fabricated proof
of remote deletion. Exact timeout values and the admin UI belong to wiring.

Remote MCPs without the deletion contract cannot declare
`holds_personal_data: true`. With `false`, the guarantee is narrower: core does
not know what the remote service retains. This is not a claim of zero
retention. A `deletion_contract: "v1"` declaration must be verified during
service onboarding before it can accept data. Builtins remain trusted code;
the manifest is not a sandbox.

Versioning: `deletion_contract: "v1"` fixes the ID-bound, authenticated,
idempotent ack semantics. Changing those semantics requires a new contract
version with the §6 overlap. Outstanding obligations must remain fulfillable
across upgrades, disabling and removal.

Open work: define which administrator may resolve a blocked obligation.
This contract introduces no new administrator authority.

## 5. Events: names, payloads, delivery and retention

Service events are core events, not copies of the runtime SSE stream. The M1
runtime's `native` fields and removal of `session.compacted` do not introduce
service event names. Version 1 defines:

| Name / Go constant | Data / Go payload | Emission boundary |
|---|---|---|
| `chat.finished` / `ChatFinished` | `chat_id`, `project_id`, `session_id` / `ChatFinishedPayload` | A completed root-chat run is durably recorded and eligible for scoped retrieval. A later run gets a new event ID; transient idle notifications and retries are not separate completions. |
| `account.deleting` / `AccountDeleting` | `operation_id` / `AccountDeletingPayload` | The durable deletion/revocation operation is recorded. Dispatch is authorized from the data-holder registry even when the integration is disabled. |
| `consent.changed` / `ConsentChanged` | `scope`, `version`, `accepted` / `ConsentChangedPayload` | The consent decision is committed. False means withdrawn, not “older consent still usable.” |
| `usage.recorded` / `UsageRecorded` | `usage_id` / `UsageRecordedPayload` | A metered usage record is committed. This names the usage event proposed in plan §7; footprint reads the record through scoped access. |

```json
{
  "schema": 1,
  "id": "event-42",
  "type": "chat.finished",
  "uid": "person-1",
  "generation": 7,
  "occurred_at": "2026-10-27T12:00:00Z",
  "data": {"chat_id":"chat-3","project_id":"project-2","session_id":"session-9"}
}
```

IDs above are opaque illustrative values. IDs are stable across redelivery,
not timestamps or sortable cursors. The envelope's timestamp is RFC3339 UTC.
Generation is the captured `users.generation` value (nonnegative integer).
Today's value is a container generation, not a completed deletion fence. The
future API must reject writes for older generations and deleting/deleted
accounts, and retain tombstones after deleting person rows. Runtime restarts
that advance the generation also invalidate old-context writes; consumers must
re-fetch authorized current state rather than relabel an old event. Deletion
acks use the authenticated operation exception in §4.

Events and their causing changes commit in the same database transaction.
Delivery is at least once, ordered per person; no ordering promise across
people. Consumers deduplicate by event ID and durably advance their cursor
only after recording work. Payloads contain references and small decision
metadata, never transcript text, prompts, responses, names or email. A service
fetches content through a scoped API that rechecks consent and account state
at that moment. Knowledge of an ID grants no read permission.

Pull is `GET /api/v1/events?after=<opaque-cursor>&types=chat.finished,...`.
`after` is exclusive; the returned cursor advances through the scanned stream,
including filtered-out events. Filtering never widens the token's subscriptions
or grants. Consumers must not infer generation or authorization from cursors.
Duplicate paid work is prevented separately: persist the event ID before the
LLM request and use it as the idempotency key. Core rejects a second
`llm.background` call with the same key for that integration; a retry must
retrieve the recorded outcome or failure, never charge again. Event retention
expiry cannot expire that protection while work remains retryable.

Reference retention decision for implementation: 30 days, bounded and
operator-configurable. Consumers cannot rely on an event being retained beyond
the configured window. An expired cursor returns HTTP 410 with
`code: "event_cursor_expired"` and `resync_url: "/api/v1/events/resync"`.
The planned authenticated resync endpoint supplies a consistent snapshot of
currently authorized record IDs, current account generations/consent decisions
and pending deletion obligations, together with a continuation cursor from the
same snapshot boundary. Page that snapshot without gaps. Consumers reconcile
local state, discard stale unauthorized work, keep their processed-event ledger,
and resume from that cursor. Resync never restores expired consent or deleted
content, and must not blindly replay paid work. Pending deletion obligations
live outside event retention and must survive it.

These retention/resync choices fill the plan's open question as a proposed
implementation baseline; no endpoint or event log is implemented in this step.
Before stable release, the two reference consumers must demonstrate transaction
atomicity, ordering, replay, cursor expiry/resync, stale-generation rejection
and paid-work deduplication. Wire-format unit tests do not prove delivery.

Versioning: schema-1 envelopes/payloads evolve additively. API readers ignore
unknown fields and skip unknown event types while advancing the cursor; the
strict manifest loader rejects unknown subscriptions until core supports them.
Renaming/removing an event or changing its meaning requires a new version and
§6's overlap. Existing event IDs and pending deletion operations survive it.

The 30-day baseline and resync path need operational confirmation with the
evaluation service and an interactive reference service.

## 6. `/api/v1` compatibility promise

Once stable `v1` is released, changes within it are additive only: fields,
events, scopes and endpoints may be added. Consumers ignore unknown response
fields. Existing fields, defaults, meanings, authorization requirements and
idempotency behavior cannot be removed or silently reinterpreted. Ordinary
permission revocation and consent/version enforcement remain effective.

```text
v1 reply: {"id":"chat-3","project_id":"project-2"}
additive: {"id":"chat-3","project_id":"project-2","new_field":true}
breaking: replace project_id with project -> release v2
```

For a breaking change, publish `/api/v2`; keep v1 working for **at least two
core minor releases or six months, whichever is longer**, measured from v2's
stable availability. The same rule covers event payloads and manifest schema
changes. Do not remove v1 merely because one side of that condition has passed.
If release numbering has not defined a minor line (the current project uses
CalVer), v1 cannot be retired by guessing that two date tags count as minors;
define the release mapping before starting that deprecation clock.

Contract tests belong in core CI and must run against both reference services:
evaluation (transcripts/background LLM) and an interactive service such as
rooms (tool context/workspace/LLM). No synchronous third-party request-path
hooks are offered. Service portal JavaScript cannot run with the core portal
origin's authority: own origin with OIDC session handoff is preferred, or a
sandboxed iframe with strict CSP. Core checks roles on every proxied route,
strips inbound identity headers and signs outgoing service requests; the
service network is not directly public.

Versioning: this section is the shared rule for stable contracts. The current
standalone package is pre-runtime preparation. The proof of concept may ship
`v1alpha` or no service API; it must not advertise stable `/api/v1` semantics
before the corresponding reference-service tests pass.

Open work: validate separate-origin or sandboxed service pages and both reference
consumers before releasing a stable API.

## 7. Grants and scoped calls

The manifest requests scopes. A separate DB record, changed by an authorized
administrator, grants scopes to an integration identity. `Options.Grants` is
only a snapshot of those records for the resolver; it is not a persistent
store, token or permission editor. Never copy requests into grants in production.

| Scope | Authority |
|---|---|
| `transcripts:read` | Read transcripts only for persons with current base and integration consent; audit every read. |
| `llm.background` | Call the gateway on the integration's own budget, with event-based idempotency. |
| `llm.user` | Call the gateway charged to the person, only within a current tool invocation. |
| `workspace:read`, `workspace:write` | Access the invocation's person/project files; writes additionally restricted to allowed paths. |
| `users:read` | UID, language and groups. No email; a future email scope needs its own definition and grant. |
| `notify` | Publish portal notices within the granted integration context. |

```text
manifest report@1.0.0 requests [notify]
DB grants report [notify] -> resolves
manifest report@1.1.0 requests [notify, transcripts:read]
DB still grants [notify] -> candidate fails; already-applied 1.0.0 stays
admin grants transcripts:read -> resolve again; person consent still required
```

Effective permissions are the intersection of requested and granted scopes,
further restricted by current consent, account state, tool policy and budget.
An old surplus grant cannot authorize a capability the manifest no longer
requests. A default-enabled integration has no exemption. The resolver checks
activation; the policy point checks current grants on every call so revocation
is immediate, including running chats and background jobs. Log every grant
change with actor, integration, old/new scopes, time and correlation ID.

Assistants grant their declared knowledge sources, skills and tools for
sessions bound to that assistant. Personal catalog switches apply only to the
normal helper: a fresh account or a personal opt-out does not disable an assistant
card or revoke its declared sources, and using an assistant never changes those
switches. Assistant grants do not include unrelated personal opt-ins or another
assistant's sources. Instance integration enablement, catalog availability, pinned
definitions, consent, account state and budget still apply. Knowledge remains
read-only: reviewed tool allowlists and upstream write/destructive annotations
are checked on each call. Enabled Assistants still reject arbitrary
skills/tools; declaring them does not bypass that validation.

OpenCode assistant projects load their source servers in project-local config.
The assistant endpoint resolves the owner/project binding from manager storage;
a call additionally checks the runtime session's directory, root status and
assistant agent. A URL, client-supplied assistant name, or session ID alone grants
no execution. Normal helper endpoints continue to require personal opt-in.
Legacy isolated support chats use the same assistant catalog grants through their existing
session authorization callback. Removing a source or disabling its integration
revokes access independently of personal catalog switches.

Integration tokens expire and are rotatable and revocable. A signed,
short-lived tool context additionally binds person, project, session,
integration and expiry (plus the generation fence). Workspace and `llm.user`
scopes require that current context: a general integration token cannot
impersonate a person outside a tool call. Revoke the context on deletion or
policy revocation; no paid or background operation bypasses the gateway.
Builtin code remains trusted manager code, with explicitly wired registries,
not a generic in-process plugin interface.

Versioning: new scope names are additive, never implicitly granted; expansions
of an existing scope's meaning are breaking. Tokens and grant APIs follow §6.
The recognized scope list deliberately excludes an undefined email scope and
any blanket administrative scope.

Open work: define the grant UI and authority of administrators or integration
owners before implementing runtime grant management.

## Current builtin inventory and tests

See [the manifest inventory](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/deploy/integrations) for the
mapping of each manifest to today's code and the remaining behavior gaps.
Examples are descriptors, not deployment overlays, installed services or
claims of per-integration consent/deletion support.

Reviewer commands with the repository's Go 1.27 toolchain:

```sh
cd manager
gofmt -l internal/integration
go vet ./internal/integration
go test -count=1 ./internal/integration
```

`TestLoad`, `TestLoadMalformed`, `TestPortalPaths`, `TestLoadYAML` and
`TestLoadReadError` cover accepted forms, required fields, strict decoding and
validation failures. `TestValidateConstructedValues` also checks invalid values
that bypass file decoding (nonfinite budgets and ambiguous MCP definitions). `TestToolName` fixes the naming boundary and length limit.
`TestVersionRequirements` covers bounds, comparison operators, CalVer and
unsupported syntax. `TestResolve` covers defaults/overrides, missing and
disabled dependencies, cycles, conflicts, compatibility, collisions and
separate grants; the determinism and upgrade tests cover stable order,
nonmutation and retention of the caller's applied set. `TestExampleManifests`
loads every shipped file and resolves all/default/minimal selections.
`TestEventWireContract` and `TestEventReadersIgnoreAdditions` fix event names,
JSON payloads/envelopes and additive consumer behavior.

Consent/deletion/delivery/token enforcement needs integration tests with its
future runtime implementation; none is simulated as already implemented here.
