# Personal and team knowledge

The optional `knowledge` integration adds Teams and Knowledge to the portal.
It uses the manager's existing database. Full-text search works without an
embedding service; optional semantic retrieval combines both search methods. Enable it in the instance definition with `knowledge: true`
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

When semantic retrieval is enabled, searches also find similar meanings across
wording and languages supported by the configured embedding model. New and edited
pages enter a background queue. Keyword search immediately includes the latest
revision; stale vectors never participate. The portal indicates pending indexing
or keyword fallback. Similarity is a retrieval hint, not proof that a page answers
the question: read the source and cite its revision.

Page titles and bodies are sent automatically to the configured embedding provider,
including pages that have not been used in a chat. Search queries use that provider
too. Source notes and historical revisions are not embedded. The operator must name
this recipient in the instance notice. Vectors and chunk text remain in the manager
database with the page's access rules; they never expand sharing or project selection.

Limits per collection are 1,000 pages, 10,000 retained revisions and 16 MiB of text.
One page body is limited to 128 KiB, source notes to 16 KiB and titles to 100
characters. A limit refuses the write; it never silently discards old revisions.

## Retained PDF and Office documents

With `file-tools` enabled, open a knowledge base and choose **Import document**.
Upload a PDF, DOCX, XLSX or PPTX and confirm that the original may be retained
for everyone who can access that collection. Originals live in the manager
SQLite database, independently of projects and runtime files. Project deletion
does not delete them. Team originals remain with the team after a member leaves
or deletes their account. Every download checks current collection access.

The isolated file worker extracts searchable text into an ordinary, unreviewed
knowledge page. Source notes retain the original download link, SHA-256, import
time and extraction status. Document details retain the extractor and version.
PDF sections identify pages; Word sections identify XML paragraphs; spreadsheets
identify sheets, rows and cells; presentations identify slides in presentation
order. Compare extracted content with the original before relying on it.

PDF extraction reads the text layer only. Scans without text fail visibly; OCR
is not included. Office extraction omits layout, images and some content such
as headers, notes and charts. Formula results are cached values and are never
recalculated. Office results are marked partial with format-specific warnings.
Legacy Office formats, macro-enabled files and ODF are not supported. No macros
run, external links are not fetched and original downloads use attachments.

Limits are 10 MiB per original, 100 originals and 64 MiB per collection, and
256 MiB per personal owner or team across its collections. Text extraction is
limited to 128 KiB and 5,000 sections. PDFs have the file worker's 100-page limit;
Office ZIPs have at most 2,000 entries and 32 MiB of expanded content. Oversized
input fails instead of silently truncating text. Split such documents first.

Processing is synchronous and bounded by the existing worker timeout. Failed
or interrupted processing retains the original and error details, without a
searchable page. Retry explicitly from the document card. Startup marks unfinished
attempts failed; a late response cannot publish after a retry or restart. Access
and integration policy are checked again when publishing extracted text.
There is no automatic source refresh or background retry queue.

## Using knowledge in a project

Select personal or team collections directly in the new-project form. The selection
is saved with the project before its first chat starts. Nothing is preselected.
You can change it later from the project's Knowledge link or the Knowledge page.
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
Version 2 also includes retained originals under `documents/<id>/<filename>`
and as base64 bytes in the manifest, together with hashes and processing details.
Text-only exports remain version 1. It includes no member grants, account
identifiers or credentials. Members can download individual visible revisions;
full team exports require Team Admin.

Importing the manifest creates a new collection and new page and document IDs.
Hashes and quotas are validated; original download references are remapped.
Both manifest versions are accepted, up to 110 MiB (114 MiB multipart request).
Import does not run extraction; interrupted attempts become failed and can be retried. It restores the
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
first. Purging a collection removes its pages, revisions, originals, search rows, vectors,
indexing state and bindings. Purging an extracted page also deletes its retained
original. Team Admins or personal owners can explicitly delete failed imports
from their document cards.

Account deletion removes personal collections, memberships and stored author
identifiers. Team text and history remain with the team. This does not redact
personal information already written inside team page text or previously exported
copies. Backups keep their existing retention policy.

With the integration disabled, tools and normal navigation disappear. Existing
`/knowledge`, `/teams` and recovery links remain available for reading, export,
administration and cleanup. New content, imports, restores and bindings are refused.
Account export and deletion remain available independently of the integration.

## Operations and validation

Migration 38 adds collection-owned original documents with cascading deletion.
The same consistent database backup covers text, originals and metadata.

Migration 30 creates the concrete team, page and revision tables and adds a random
account incarnation. An account recreated under the same UID cannot revive old
forms or in-flight knowledge requests. Membership checks and content commits use
the same SQLite transaction. Deletion of a founder never cascades into team content.

Back up the manager database with a SQLite-consistent backup, including its WAL
state. Tests restore a database snapshot and verify content and access boundaries.
The search table is derived; rebuilding it from canonical heads must preserve the
same page IDs and exclude archived pages. No source refresh worker is introduced.

### Semantic retrieval configuration

Enable `knowledge` and set these instance defaults or manager environment variables:

| Setting | Meaning |
|---|---|
| `OC_KNOWLEDGE_EMBEDDING_MODEL` | Fixed embedding route on the configured model endpoint; unset or `-` disables semantic retrieval. |
| `OC_KNOWLEDGE_EMBEDDING_REVISION` | Operator-maintained version of that exact model, required when enabled. |
| `OC_KNOWLEDGE_EMBEDDING_DIMENSIONS` | Exact output dimensions, from 1 to 4096. |

The existing manager credential must permit that embedding route. The endpoint must
support OpenAI-compatible `/v1/embeddings` with batched string input, float vectors
and explicit response indices. No model fallback is allowed. Retargeting an alias
requires changing the revision even if dimensions remain identical. Endpoint,
route, revision, dimensions or chunking changes invalidate the old vector space
and trigger a rebuild from current pages. Index rows are derived and need not be
included in portable knowledge exports; database backups preserve them.

Migration 32 adds vectors and persistent indexing state. The worker selects a
current consenting personal owner or active accepted team member (administrators
first). Requests use that account's normal usage attribution and daily budget;
team indexing is charged to the selected member. A failed page waits five minutes,
while other pending pages can progress. Queries time out after five seconds and
fall back to current keyword matches. Gateway indexing requests time out after
15 seconds; batches contain at most 16 chunks. There is one worker per manager.

Titles prefix 1,600-character chunks with a 200-character overlap. Normalized
float32 vectors use cosine similarity. Retrieval filters permissions, project
bindings, archives and current revisions in SQLite before scoring; it combines
the top 50 lexical and semantic pages with reciprocal rank fusion (`k=60`).
Search returns at most 50 distinct pages. It rechecks authorization after provider
requests, including failures. Newer revisions and deletion prevent an in-flight
index job from publishing stale content.

`knowledge_search` returns `hits`, `mode` (`keyword`, `hybrid` or
`keyword-fallback`), `indexed_pages` and `pending_pages`. Counts cover only the
selected, accessible scope. Read page content and its revision citation with
`knowledge_read` after retrieval.

The initial implementation scans authorized vectors exactly in SQLite. There is
no additional vector database or chat model choice. Corpus size determines cost
and latency; measure with representative content before claiming load acceptance.
Disabling semantic retrieval retains vectors but stops provider calls. Re-enable
with the same revision to reuse current vectors, or change revision to rebuild.

Local tests cover ownership, membership revocation, concurrent last-admin changes,
blocked/recreated accounts, founder deletion, stale edits, hierarchy cycles,
Markdown import, portable export/import, disabled-mode cleanup, CSRF, safe previews,
German/English rendering and runtime session checks. Live pilot acceptance and
source-answer quality require a separate deployment and real usage.

Retained PDF/Office originals, automatic refresh, shared project execution and
realtime editing are later work. Teams do not currently share project runtimes,
files or conversations.
