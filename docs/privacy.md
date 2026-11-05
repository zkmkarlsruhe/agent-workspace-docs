# Privacy and data handling

This describes the proof of concept's current behavior. The operator chooses
the identity provider, model endpoints, integrations, administrators, logging
and backups. Publish an instance-specific notice naming those recipients and
their retention policies before inviting people. The minimal instance disables
optional integrations and chat evaluation. This document is not a claim that
all installations have the same processing arrangements.

## Data flows

1. The browser authenticates through the edge proxy and IdP. The manager
   receives a stable subject, username, profile fields and groups from trusted
   headers. Login credentials stay with the IdP; the manager uses identity
   assertions to authorize portal and runtime requests.
2. Uploaded files enter the person's workspace. OpenCode stores conversations
   and reads files as needed for a task. Content read into model context can
   leave the host: prompts, conversation history, file contents, images and
   tool results pass through the manager and LiteLLM to the configured model
   endpoint. Uploading a file does not itself mean every byte is sent, but
   there is no automatic confidential-content filter.
3. The model gateway sends the username as `x-litellm-end-user-id` to LiteLLM
   for attribution. This is not a pseudonymous identifier. The operator must
   verify LiteLLM logging and what its upstream providers receive and retain.
4. Enabled integrations send requests to their configured services. Search
   queries, URLs, MCP arguments and cloud-file operations can reveal task
   content. Retrieved data can enter the chat and subsequent model context.
   Disabling an integration does not recall requests already sent.
5. Optional semantic knowledge search automatically sends saved page titles and
   bodies to the configured embedding provider, even without a chat. Search queries
   use the same endpoint. Derived vectors and chunk text stay in the manager database
   and follow current page permissions and permanent deletion. Historical revisions
   and source notes are not embedded. The instance notice must identify the recipient.
6. Downloads and ZIP exports create copies on the person's device. Optional
   cloud-file uploads create copies at the connected service. Those copies
   have separate access and deletion rules.

## What is stored where

| Store | Data and access |
|---|---|
| Browser | IdP session cookies and web UI state/cache. A downloaded result or export remains on the device until its owner removes it. |
| IdP and its database | Login accounts, credentials, group memberships and authentication records, governed by the IdP operator. The reference uses a PostgreSQL-backed Authentik installation. |
| Personal host storage, `/srv/opencode/users/<uid>/` | Project files, trash, snapshots, personal skills/configuration, runtime data and chat history. Mounted into that person's runtime; accessible to host and backup administrators. |
| Manager SQLite, `/srv/opencode/manager/manager.db` in the reference | Account UID, username, display name, email, slug/slot, issuer/subject binding, project/trash metadata, consent version and acceptance time, personal settings, catalog choices and usage records. Enabled integrations can add connection records, feedback and upload metadata. |
| Manager connection records | Service app passwords encrypted with AES-GCM using `OC_MASTER_KEY`. The key lives in deployment secrets. Access to both database and key permits decryption. This is not encryption against the operator. |
| Optional evaluation tables | Bounded root-chat transcripts, titles, project names, counts, evaluation results and transcript-read audit records. The minimal instance does not collect these snapshots. |
| Task template tables | Account-private task definitions and current revisions. Each created project retains the definition revision used, submitted values and rendered task text. Host and backup administrators can access the database. |
| Knowledge and team tables | Personal collections, team membership and administration audit, Markdown pages, retained original documents and extraction details, source notes, immutable revisions, derived search vectors, indexing state and project selections. Personal knowledge is account-private; team members can read team history and edit pages. Host and backup administrators can access the database. |
| Operational logs | Request and lifecycle diagnostics, identity/account identifiers, project/session identifiers, errors and usage metadata. Destinations and rotation depend on the deployment; do not treat logs as anonymous. |
| Model gateway, providers and integration services | Request content and associated identifiers according to each service's configuration and policy. Local deletion is not proof of remote erasure. |
| Backups | Copies of databases, workspace storage, configuration and secrets. Backup readers may have access to all personal data. Expiry and restore procedures belong to the operator. |

Tool evidence in these snapshots is limited to execution state, exit codes,
truncation, result counts, search coverage, browser approval state and document
check counts. It does not copy returned mail bodies, document text, passwords or
clipboard contents. A refreshed snapshot invalidates its previous evaluation;
collection and evaluation still require the current consent and enabled policy.

Usage events include account, project and session identifiers, capability,
model/tool, timestamps, token counts, estimated cost/emissions, latency,
status and additional metadata. They are distinct from the chat database.

Chats are not shared with other users through the product. This does not
exclude operator access. With evaluation enabled, authorized administrators
can read stored transcripts; reads are audited, and transcript excerpts may
be sent to a model for evaluation. The present implementation uses the base
consent version for this processing, not a separate per-integration acceptance.

Current Assistant sessions are excluded from operator transcript collection and
evaluation. Older isolated support sessions have separate acceptance and optional
evaluation rules. These restrictions do not prevent host-administrator access.

## Consent and control

The portal requires acceptance of the selected instance's current notice
before normal use. The manager stores the accepted version and timestamp;
a changed version requires acceptance again. Declining does not silently
accept it or delete an existing workspace. The current consent gate also
blocks the ordinary account export and deletion pages until the current
notice is accepted. If you decline a revised notice and need an export or
deletion, contact the deployment operator; the current portal does not provide
a consent-free route for those actions.

Optional catalog selection and connecting a service are separate actions.
They are not substitutes for a complete processing notice. Installed extensions
have persistent operator policies and grants. Required integration notices are
versioned; users accept or withdraw them through the Extensions page. Access
checks include the current base notice and required integration consent.
This does not authorize arbitrary transcript access or implement the proposed
stable service API. See [extension authority](extension-authority.md).
Turning off a feature does not delete data it already stored.

The account export contains visible project files and readable root-chat
transcripts, including trashed projects and the personal settings for a full
export. Full exports include `remembered.md`, the personal instructions outside
the managed profile, and start the personal runtime when needed to read it.
A failed memory read fails the export instead of silently omitting it.
If a project is still moving into trash, export returns HTTP 409 before starting
the ZIP response. Retry after the move finishes. Missing expected trash files
also fail the export rather than producing an apparently complete archive.
It omits other hidden paths and Git history, symlinks, configuration,
credentials, model reasoning and child-session transcripts. Tool calls appear
as summaries. It is a portable result export, not a complete database dump or
backup. It includes personal knowledge collections, retained originals and their revision history;
team collections use a separate export restricted to Team Admins. Full account exports also
include personal task definitions and project task provenance; a single-project
export includes only that project's provenance.

Document imports require confirmation of the collection audience. Originals remain
in the database independently of projects and follow current collection access.
The internal file worker receives bytes for bounded extraction; searchable text
follows the same embedding and chat-provider rules as authored pages.

Knowledge selected for a project can enter tool results and model context. Removing
membership prevents subsequent access; it cannot recall text already delivered to
a chat, provider or downloaded export. See [knowledge access rules](knowledge.md).

Personal memories can be reviewed, edited, downloaded or cleared under
**About me & how I work → Personal memories**. The canonical text is the
personal runtime configuration `AGENTS.md`; the editor preserves the managed
profile and refuses stale saves. It does not automatically collect facts from
conversations. This text is available to general chats and can be sent to the
configured model; it is not copied into restricted Assistant runtimes. Keep
secrets out of it. Clearing memories leaves earlier chats, exports and backups
unchanged. Account deletion purges the personal configuration with the rest
of the owner’s runtime storage.

## Deletion and retention

| Data/action | Current behavior |
|---|---|
| Stop an environment or sign out | Persistent files and chats remain. |
| Archived session | Auto-archive preserves transcripts and files. Restore is available in the running environment; archiving does not reset project retention. See [instance options](instance.md#dormant-session-auto-archive). |
| Inactive project | After 30 days without recorded activity, the daily sweep marks it for trash. The directory move waits for a running environment and a non-busy project. |
| Project trash | Restorable for 30 days from the trash timestamp, then eligible for purge. Physical cleanup depends on a running environment and successful operations; this is not an exact erasure deadline. |
| Clear personal memories | Removes unmanaged remembered instructions from the personal configuration, preserving the managed profile. Earlier chat text, exports and backups remain separate. |
| Delete a task template | Removes the reusable definition. Existing project provenance survives until the project is permanently purged; account deletion removes both. |
| Personal safe | Password-encrypted database blob; unlock keys exist only temporarily in service memory. Ordinary account export excludes it; separate encrypted backup is available. Account deletion removes the blob, not independent backups. See [personal safe](personal-safe.md). |
| Delete a personal skill | Permanent after confirmation; no skill trash. Backups remain separate. |
| Archive knowledge | Reversible, without automatic expiry. Explicit permanent deletion removes archived pages or collections, their revisions and attached originals. Failed imports can be explicitly deleted without archiving a page. |
| Delete the account | Attempts credential revocation, stops/removes runtimes and toolboxes, drains in-flight operations, removes the network, purges personal storage and quotas, then removes account-linked database rows. A subsequent authorized login can create a fresh account. |
| Usage records after account deletion | Retained under a random `deleted-…` identifier. Other event fields remain, so this is identifier replacement, not a guarantee against re-identification. |
| Knowledge after account deletion | Personal collections, their originals and memberships are deleted; author identifiers are cleared. Team pages, originals, history and team administration audit remain. Personal information written inside page text requires separate content removal; deletion does not redact that text. |
| Spend ledger after account deletion | Copies the last 48 hours of cost entries under the original UID so deletion cannot reset the daily cap. Old ledger entries are pruned on later account deletions, not by a scheduled expiry job; physical retention can exceed 48 hours. |
| Evaluation after account deletion | Evaluations and personal feedback are deleted. Chat snapshots lose title, project and transcript; count stubs remain under the replacement identifier. Transcript-read audit records are separate and are not erased by this account deletion. |
| Logs, backups, external services and downloaded copies | Not purged by the local account-deletion operation. The operator and each recipient must provide their own retention and deletion process. |

Account deletion records a durable operation and fences the current account
incarnation before cleanup. Failed core cleanup is retried by the lifecycle loop;
it cannot delete a newly created account with the same identity. Credential
revocation or provisioning failures can block completion, and account rows remain
until core cleanup reaches its final step. Required external deletion obligations
survive core account removal and integration disablement. Services acknowledge
after deleting their held data; operators can record resolution with evidence.
See [extension deletion](extension-authority.md#account-deletion).
Do not report a failed request or an outstanding external obligation as complete.

For the optional Nextcloud connection, disconnecting or deleting the local
account revokes the app password but leaves files in Nextcloud. Reads may
cover all files available to the connected person; writes are restricted to
the configured transfer folder. The manager never deletes remote files.
The IdP account is also outside local account deletion.

There is no implemented general automatic expiry for usage events, retained
count stubs or transcript-read audit records. Do not adopt older planning
figures as deployed retention guarantees. Set and test an operational policy
for these stores, external logs, provider records and backups. A restore can
bring deleted data back; the restore procedure must account for deletions
that occurred after the backup.

## Identity provider precondition

**The IdP must never reuse a username for a different person.** Username
lookup is exact and case-sensitive; changing a username creates a separate
account. The existing internal UID, files, chats and consent remain tied to
the original username.

The manager binds each account to a configured issuer and trusted stable
subject. A changed subject blocks that username, including the original
subject's new requests, until an administrator verifies ownership and acts.
Rebinding gives the new subject all existing data and records an audit entry;
it is not a safe automatic response to an IdP migration. Changing the issuer
does not rebind users and causes startup refusal if stored bindings disagree.

Legacy accounts bind on their next request. Reuse that happened before that
first binding cannot be detected. Already-open runtime streams are not
disconnected by the identity guard; new requests and handshakes are checked.
The operator must verify ownership with the IdP administrator before rebinding
and keep the issuer stable across upgrades and restores.

## Instance processing record

Use the following as an inventory to complete for the actual deployment;
the software cannot supply these organizational facts.

| Field | Operator supplies |
|---|---|
| Purpose and operator | Tasks supported, operator identity and privacy contact. |
| People and data | Eligible accounts; identity/profile fields; permitted project, chat and file contents. |
| Recipients | Hosting and backup operators, administrators, IdP, model gateway/providers and each enabled integration. |
| Locations | Storage and processing locations, including provider logs and backups. |
| Authorization and notice | Applicable processing basis, notice text/version, access rules and any additional acceptance requirements. |
| Retention and deletion | Period and enforcement mechanism for every store above, failure handling, external deletion and restore handling. |
| Safeguards | Proxy trust, identity lifecycle, isolation, access review, secret handling and tested backup/restore procedures. |
