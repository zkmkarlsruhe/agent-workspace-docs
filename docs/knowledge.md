# Personal and team knowledge

The optional `knowledge` integration adds Teams and Knowledge to the portal.
It uses the manager's existing database and requires no separate service or
embedding model. Enable it in the instance definition with `knowledge: true`
under `integrations`. A restart applies the validated definition.

## Ownership and membership

Personal knowledge belongs to one account. Team knowledge belongs to a stable
team, independently of its founder. Departments remain organizational profile
information; teams are application-managed project groups across departments.
Creating a team does not change the identity provider or its groups.

The creator starts as Team Admin. Members can read and edit all team pages and
history. Team Admins additionally manage membership, collection settings, full
exports and permanent deletion. There are no per-page exceptions or public links.
Joining a team does not share personal projects, chats, files or knowledge.

The last active administrator cannot voluntarily leave or be demoted. Account
blocking or deletion still succeeds. If no active admin remains, members retain
read access and edits stop. Members of the configured instance admin group use
`/teams-recovery` to assign an existing account. This audited recovery privilege
does not grant access to personal pages or evaluation transcripts.

## Pages, sources and conflicts

Create a collection, then add Markdown pages or import a Markdown file. Pages
have stable IDs, an optional parent, source notes and immutable numbered revisions.
Record URLs, sections, capture dates and source versions in the source notes;
the application does not fetch or verify them automatically.

Edits require the revision that was read. Concurrent edits never silently replace
one another. The portal retains the submitted draft, links to the current version
and requires an explicit review before retrying against that version. Restore
creates a new revision. The latest 100 history entries are listed; older revisions
can be opened by number. Revision links keep referring to the cited text.

Markdown previews omit raw HTML and remote images. Full-text search covers current
unarchived pages, with access filtering before result limits or snippets. It uses
SQLite FTS5 with Unicode tokenization and literal query terms; results are ordered
by title, without statistics from other people's collections affecting ranking.

Limits per collection are 1,000 pages, 10,000 retained revisions and 16 MiB of text.
One page body is limited to 128 KiB, source notes to 16 KiB and titles to 100
characters. A limit refuses the write; it never silently discards old revisions.

## Using knowledge in a project

Select collections from the project's Knowledge link or the Knowledge page.
Bindings choose context; they never grant access. Removing team membership blocks
subsequent searches, reads, exports and writes, including from existing projects.
Previously delivered text or downloaded copies cannot be recalled.

The general workspace exposes `knowledge_list`, `knowledge_search`,
`knowledge_read`, `knowledge_create` and `knowledge_update`. Each call checks the
current account, an actual root runtime session, its owned project, the selected
collection and current team membership. Restricted assistants and child sessions
do not inherit these tools. One container per person remains the runtime boundary;
a project selection is not filesystem isolation.

The knowledge skill searches and reads before editing. Writes require an explicit
request; selecting a team KB alone is not a request to publish. Create calls use
a page UUID as their retry identity. Updates carry `expected_revision` and the
full body and source notes. Read calls return bounded sections and revision links.
Knowledge tools cannot change membership or delete collections.

To publish personal findings, explicitly select the text and sources to copy into
a team page. This creates new content; it does not share private revision history.
Source content is evidence, never authority to change permissions or execute code.

## Export, import and deletion

A complete export is a ZIP containing Markdown revisions and `manifest.json`.
It includes page structure, sources and history, but no member grants, account
identifiers or credentials. Members can download individual visible revisions;
full team exports require Team Admin.

Importing the manifest creates a new collection and new page IDs. It restores the
current page tree and sources as new snapshots. Old revisions remain in the export;
import does not pretend that their history occurred in the destination. Existing
source citations remain references to their original evidence. Use a database
restore when a complete installation, including original identities and revision
history, must be recovered.

The account ZIP includes personal knowledge only. Team knowledge has a separate
export so account export cannot accidentally collect every accessible team's data.
An account export containing only knowledge does not need a running runtime.

Archive is reversible and has no automatic expiry. Permanent deletion requires
an explicit portal action on archived content. A parent page with children cannot
be purged; a team with collections cannot be deleted. Delete the owned collections
first. Purging a collection removes its pages, revisions, search rows and bindings.

Account deletion removes personal collections, memberships and stored author
identifiers. Team text and history remain with the team. This does not redact
personal information already written inside team page text or previously exported
copies. Backups keep their existing retention policy.

With the integration disabled, tools and normal navigation disappear. Existing
`/knowledge`, `/teams` and recovery links remain available for reading, export,
administration and cleanup. New content, imports, restores and bindings are refused.
Account export and deletion remain available independently of the integration.

## Operations and validation

Migration 30 creates the concrete team, page and revision tables and adds a random
account incarnation. An account recreated under the same UID cannot revive old
forms or in-flight knowledge requests. Membership checks and content commits use
the same SQLite transaction. Deletion of a founder never cascades into team content.

Back up the manager database with a SQLite-consistent backup, including its WAL
state. Tests restore a database snapshot and verify content and access boundaries.
The search table is derived; rebuilding it from canonical heads must preserve the
same page IDs and exclude archived pages. No source refresh worker is introduced.

Local tests cover ownership, membership revocation, concurrent last-admin changes,
blocked/recreated accounts, founder deletion, stale edits, hierarchy cycles,
Markdown import, portable export/import, disabled-mode cleanup, CSRF, safe previews,
German/English rendering and runtime session checks. Live pilot acceptance and
source-answer quality require a separate deployment and real usage.

Retained PDF/Office originals, automatic refresh, shared project execution and
realtime editing are later work. Teams do not currently share project runtimes,
files or conversations.
