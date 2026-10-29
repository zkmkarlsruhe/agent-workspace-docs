# Instance configuration

> **Prototype for evaluation only. Not production software, no support, no guarantees. Do not make it reachable from the internet; run it only in an internal network. Use at your own risk.**

Start with `instance/minimal/instance.yaml`. It disables all optional integrations,
uses English project folders and contains no provider credentials. The commented
`instance/example/instance.yaml` demonstrates the larger builtin configuration;
its example endpoints and scope grants are not an operational deployment preset.

Set `OC_INSTANCE_FILE` to the mounted instance file (`/instance/instance.yaml`
in Compose). The optional top-level boolean `default: true` selects one embedded
definition when the variable is unset or blank. The private deployment marks its
instance as default; the public export removes that flag from the comprehensive
example. Public adopters must set `OC_INSTANCE_FILE`. Multiple flagged embedded
definitions fail during initialization. With no flag, only a build containing
solely `minimal` selects it automatically; other builds require explicit selection.
A missing or invalid explicit file fails without falling back. The renderer uses
`-instance` for the same selection rule.

Disabled rooms and Nextcloud integrations need no host, team, timezone or cloud
folder placeholders. Their values become required when enabled. `directory_url`
is optional unless `OC_LDAP_URL` enables the directory connection.

```sh
cd manager
go run ./cmd/render-instance -instance ../instance/minimal/instance.yaml -out ../instance/minimal/rendered
go run ./cmd/render-instance -instance ../instance/minimal/instance.yaml -out ../instance/minimal/rendered -check
```

The renderer validates the whole definition and writes deterministic files.
Edit the definition, regenerate, then restart the manager and affected runtimes.
Keep generated runtime assets and instance values together.

- `values`: product text, contacts, domain and paths; no credentials.
- `folders`: inbox, results, work, project metadata and trash names.
- `models`: default, small and thorough LiteLLM aliases.
- `integrations`: explicit enable/disable switches for the shipped manifests.
- `integration_grants`: explicit requested scope grants; this is not per-person consent.
- `capabilities`: project defaults and legacy catalog behavior.
- `sessions.archive_after_days`: dormant-session archive age; absent or `0` disables it.
- `consent` and `copy`: the operator's notice and user-facing wording.
- `knowledge_sources`: read-only references to catalog entries and upstream MCP servers.
- `assistants`: task definitions, source grants, tools, prompts and consent mode.

`assistants` replaces `profiles`; the old key is temporarily accepted with a warning.
See [contracts](CONTRACTS.md), [LiteLLM](connect-litellm.md) and [MCP](mcp-server.md).

## Portal navigation

The main navigation contains My projects, Assistants, Capabilities and Help
(German: Meine Projekte, Assistenten, Fähigkeiten, Hilfe). The account menu holds
About me & how I work, Usage, Connections (Nextcloud), Privacy and Delete account.
It uses a native disclosure and works without JavaScript.

Capabilities are optional abilities for tasks, such as searching documents or
working with tables. This label replaces Tools in the portal; the route remains
`/tools`. Assistants replace the former Profiles label and configuration key.

## Assistants and project modes

An enabled assistant has an ID, revision, audience, instructions, model role and
source/tool grants. `project_mode: per_task` (also the default when omitted) creates
a new project for each submission. `shared` reuses a folder per person and assistant;
each submission still starts a new session. Shared projects cannot be renamed.
Existing folder/trash conflicts and changed revision pins fail without overwriting
or adopting data. A changed title changes the derived shared folder name.

Existing projects pin their definition. After changing a revision, create a new
project or plan an explicit shared-project migration. Current assistants share the
person's runtime; prompts and tool settings are not a separate security boundary.

## Project Capabilities

`capabilities.projects` enables project selection. Minimal sets it to `false` and
ships an empty catalog. When enabled, `project_default` accepts `all`, `none` or
catalog IDs and selects only capabilities already available to the person.
`legacy_default: global` lets older projects inherit current personal choices;
`none` starts those projects empty until edited. Explicit empty selections stay
empty. Global opt-out revokes access across projects. Assistant projects use their
reviewed source/tool grants and have no project capability toggles.

Disabling project scoping returns ordinary projects to personal catalog grants;
it is not a deny-all switch. Managed MCP requests check current availability,
project ownership and the session's actual folder on every call.

## Dormant-session auto-archive

Set `sessions.archive_after_days` to an age in days; omission or `0` disables it.
Minimal disables it. Positive values range from one second (`1/86400` day) to
106751 days. Fractional days allow short evaluation runs.

The reaper scans already running, idle environments at most daily (or at the
configured interval when shorter). It never starts or keeps an environment alive
for archiving. Busy environments, lifecycle locks and failed calls defer the sweep.
Only root sessions in ordinary, non-trashed projects qualify; assistant projects,
child sessions and sessions without timestamps are excluded. The last update,
falling back to creation, must be strictly older than the threshold.

The project page separates **Archived chats** and offers **Restore** while the
owner's environment is running. Restoring gives the session a full grace period.
Archiving preserves the transcript and files; it does not count as project activity
or replace project trash retention. A dormant project can reach trash first.

The manager rechecks activity before each archive request. OpenCode has no atomic
idle-and-archive operation, so a newly starting session can race the final request.

## Reviewed claims and estimates

The comprehensive example's consent is **operator-reviewed example text for that
instance only**. Its prototype approval status, evaluation access and responsibility
terms do not apply automatically to a new operator. Review and replace both language
versions, the evaluation copy and the consent version before granting access.
Renaming or exporting the example does not approve or adopt its policy.

Provider names, locations and fallback descriptions belong in `copy.providers` and
optional `copy.providers_intro`, `providers_standard`, `providers_fast`,
`providers_thorough` and `providers_images`. Keep these EN/DE claims consistent with
the actual upstream configuration. Minimal has no provider or fallback promises.

`copy.pricing` explains chat prices, `copy.pricing_models` describes the runtime
price metadata, and `copy.pricing_method` explains usage accounting. Artifact text
can use `[[copy.pricing.en]]` (or `.de`) through the existing token renderer.
`commands/help.md` is generated with each instance, alongside `opencode.jsonc`.
The copy uses `[[accounting.upstream_cost_currency]]`,
`[[accounting.usd_per_eur]]` and `[[accounting.prices]]` from the existing
`accounting` block. Runtime model `cost` values are generated from each role's EUR
prices multiplied by `usd_per_eur`; without a positive rate or a role price, the
renderer omits that role's USD cost metadata. No exchange rate is inferred.
Environment overrides update the manager's effective instance copy; keep the YAML
and rendered runtime assets synchronized when changing pricing or rates.

`accounting.prices` holds per-role input/output estimates in EUR per million tokens.
`largest_context` and `max_output_tokens` determine the conservative reserve.
`embedding_eur_per_million`, `image_eur`, `mcp_eur`, `search_eur`, `fetch_eur` and
`toolbox_eur` configure the other estimates. `prices: {}` disables chat estimates;
a zero flat charge disables that charge. Minimal explicitly configures estimates
and uses `upstream_cost_currency: none`, so upstream cost values are not treated
as known billing. EUR values are used directly; USD values require a positive
`usd_per_eur`. Local budget accounting cannot guarantee the provider's invoice.
See [the cost contract](connect-litellm.md) for overrides and partial usage handling.

`footprint` contains optional per-role coefficients. Minimal omits them and reports
unknown footprint. `footprint_assumptions.pue` (default `1.2`) and
`footprint_assumptions.grid_g_per_kwh` (default `344`) are explicit assumptions,
not measurements or promises of provider location. The grid default originates in
the German 2025 consumption mix; use an appropriate factor for your deployment.
Output coefficients already include data-centre overhead; review them when changing
PUE. Optional `copy.footprint_billing` and `copy.footprint_rough` describe local
billing and coefficient limitations; neither is inherited by minimal.

Optional `copy.capability_web`, `capability_pdf`, `capability_knowledge` and
`capability_library` preserve reviewed local descriptions; otherwise help uses
the configured catalog descriptions. Help follows enabled integrations, wired
services/models and catalog availability. Project
selection still determines which available capabilities a particular chat can use.

## Timezone and folder names

`timezone` selects an IANA timezone for budget-day boundaries, PDF footer dates,
room dates, fetched-page timestamps, Nextcloud timestamps and local transcript
and export timestamps. It defaults to `UTC` when omitted; minimal explicitly uses
`UTC`. Set `OC_TIMEZONE` to override it when starting the manager. Invalid names
and the host-dependent `Local` timezone are rejected. Day boundaries follow the
selected zone's daylight-saving rules.

`copy.folder_name_prompt` supplies the folder-name instruction sent to the small
model. Both `en` and `de` entries are required. The internal naming call uses the
`en` entry; that instruction determines the requested output language independently
of the portal language. Minimal requests an English name. Operators may choose
another language in their instance copy. Existing instances must add this copy
field before upgrading.
