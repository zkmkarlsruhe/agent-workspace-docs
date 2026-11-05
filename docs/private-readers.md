# SMB and mail readers

Optional private readers use a secret from the person's [safe](personal-safe.md)
only after an explicit browser approval. Unlocking the safe does not approve a
read. Each request displays its operation and destination. The signed-in account
name supplies the login; the selected safe entry supplies the password.

The manager starts one disposable worker per approved operation. Credentials pass
through its private standard-input pipe, never through container environment
variables, command arguments, logs or the chat runtime. Results are untrusted
input and can become part of the chat and its model requests.

## Operations

- `smb_list`: list a directory in an operator-approved share, at most 200 entries
  with an explicit truncation flag.
- `smb_read`: read one file of at most 1 MiB. SMB 3.1.1 encryption is required;
  DFS, reparse points, path traversal and writes are refused.
- `mail_recent`: read the latest 20 messages across INBOX and its selectable
  descendants, ordered by server `INTERNALDATE`. Read and unread messages both
  count. The worker uses IMAPS on port 993, read-only selection and `BODY.PEEK`;
  it does not mark messages read. Plain-text body parts are returned with explicit
  truncation flags; attachments and HTML-only bodies are not converted.

- `mail_folders`: inspect the mailbox hierarchy, including Archive, Sent and
  non-selectable parent folders. Returns actual hierarchy delimiters and parent
  paths, 200 entries per page. Continue with `next_offset` until it is null;
  `prefix` narrows the returned names. Listing reads no message bodies.
- `mail_search`: search one folder, optionally including its descendants, by
  sender, recipient, subject, text, receipt dates and unread status. Filters are
  ANDed. `since` includes the date; `before` excludes it. Results contain up to
  20 messages, newest first, with `next_offset` for further pages.
- `mail_read`: read one exact message using its returned folder, `uid` and
  `uidvalidity`. A changed mailbox identity or missing UID fails explicitly.
- `mail_thread`: find messages with exact Message-ID, References or In-Reply-To
  links to a chosen ID, oldest first, 20 per page. Prefer the returned `thread_root`.
  Equal subjects alone do not establish a relationship. Missing or malformed
  references, and messages outside the chosen folders, can leave gaps; the result
  explicitly does not guarantee a complete conversation.

Search and thread reads default to INBOX. Set `folder` to a name returned by
`mail_folders`; add `recursive: true` for its descendants. An empty folder with
`recursive: true` includes all selectable folders, including Sent. If that scope
exceeds a limit, narrow it instead of treating a partial scan as complete.
Search runs on the IMAP server with escaped literal criteria and UTF-8 charset;
servers that reject that charset fail explicitly. No raw IMAP commands are accepted.

Each page, exact read and related-mail lookup needs its own browser approval.
The popover shows folder scope, filters and pagination before approval. Reading
an already returned result file does not access the mailbox or require another
approval. Changes between calls can shift offset pages; use the returned stable
message identifiers when selecting a particular mail.

The legacy recent-mail scan is bounded to 256 listed folders and 10,000 messages.
Folder discovery allows up to 10,000 listed folders; recursive search allows up
to 256 selectable folders and 10,000 matching messages per call. Every operation
has a 16 MiB IMAP response budget. Limits fail explicitly. The worker has a
35-second deadline; the manager allows 45 seconds including container handling.
There are four concurrent worker slots. Bodies remain bounded plain text with
truncation indicators; HTML-only bodies and attachments are not converted.
There is no mailbox draft creation, share write or background poll. Optional plain-text
mail submission is described below.

## Plain-text mail submission

`mail_send` accepts `to`, optional `cc` and `bcc`, `subject`, `body` without a
signature, and optional `attachments` containing PDF paths relative to the current project. It uses the signed-in SSO email address as sender. The person must first
save their approved plain-text signature in **Settings → Mail signature**. The
manager appends that signature unchanged, separated by `-- ` on its own line.
A missing signature blocks sending. Changes to sender or signature invalidate
pending requests; prepare a fresh message for review.

The browser displays the full sender, recipient lists (including Bcc), subject,
and body with signature. Unlocking the safe does not send. A fresh click on
**Send this mail now** approves this exact message once, using the selected safe
entry. The popover closes after submission and reports the outcome by toast.
The result returns to the requesting chat session too.

The body uses `text/plain` UTF-8; HTML-looking text remains literal text.
PDF attachments use standard multipart MIME, at most 5 files and 5 MiB total.
Fetch cloud PDFs into the current project with `nextcloud_fetch` or
`nextcloud_share_fetch`; export other documents to PDF first. Put existing cloud
share links in `body` when requested. Sending does not create public shares.
The browser shows attachment names and byte sizes. The manager freezes the file
bytes before requesting approval, so edits after preview cannot change the mail.
Only regular files from the bound project are read; hidden paths and symlinks are
refused. No arbitrary headers, sender override or Sent-folder copy are supported.
Use bare ASCII addresses without display names, at most 50 distinct recipients
across all lists. Subject is limited to 512 UTF-8 bytes; input body to 32 KiB;
saved signature to 1000 characters and 4096 bytes. Bcc is used only in the SMTP
envelope, never in message headers. All recipients must be accepted before DATA.

SMTP server acceptance does not prove delivery. A timeout, disconnect or lost
response after approval can mean the message was already sent. Never retry
submission automatically. Check the outcome before preparing another request;
every new submission requires another explicit browser approval.

Submission is disabled unless the content-addressed operator policy includes:

```json
"submission": {"host": "mail.example.org", "port": 587, "sender_domain": "example.org"}
```

This is an additional top-level policy field; preserve the existing `version`,
`enabled`, `smb` and `mail` sections. Permit TCP 587 only to that fixed server from
the isolated credential network and add its fixed address to `OC_CREDENTIAL_HOSTS`
if it differs from the IMAP host. STARTTLS certificate and hostname validation and
SMTP authentication are mandatory. No anonymous relay or plaintext fallback exists.
The manager, Docker proxy and worker must use the same new policy path and image.

Tests cover synthetic SMTP success/refusal/uncertain outcomes, TLS failure,
recipient validation, unchanged signatures, exact one-shot approval, wrong-owner
and wrong-tab rejection, and browser preview/notifications. Real mailbox sending
requires a separately approved test message; fixture success is not a delivery claim.

## Build and configure

Build the worker from the public source tree, publish it to the operator's
existing registry and use its resolved digest:

```sh
docker build -t registry.example.org/workspace/credential-connectors:local services/credential-connectors
docker push registry.example.org/workspace/credential-connectors:local
docker image inspect registry.example.org/workspace/credential-connectors:local --format '{{join .RepoDigests "\n"}}'
```

The build context includes the worker, tests, dependency requirements and a
disabled policy example. The worker image is not a continuously running service.
The manager creates and removes its containers on demand. Pull the digest-pinned
image on the Docker host before enabling the integration.

Copy `services/credential-connectors/policy.example.json` to an operator-managed
directory outside the source checkout. Set `enabled` to `true`, enter the SMB and
mail hostnames, and list the allowed SMB shares. Both destinations are required
by the current policy format, including at least one share. Leave `domain` empty
unless the SMB server requires a specific domain prefix for the signed-in login.
The policy contains destination configuration, never passwords.

After editing, calculate the SHA-256 of the exact policy bytes and name the file
`credential-readers-<sha256>.json`. Any later edit requires a new digest and filename.
Set these values identically on the manager and Docker proxy:

```text
OC_CREDENTIAL_IMAGE=registry.example.org/workspace/credential-connectors@sha256:<resolved-image-digest>
OC_CREDENTIAL_NETWORK=oc-credential-egress
OC_CREDENTIAL_POLICY_FILE=/srv/opencode/policy/credential-readers-<policy-sha256>.json
OC_CREDENTIAL_HOSTS=files.example.org:192.0.2.10,mail.example.org:192.0.2.11
```

Replace the documentation addresses with the actual target IPv4 addresses.
Hostnames must match the policy. At most eight static host entries are supported;
DNS in the worker points at loopback and cannot resolve other destinations.
IMAP certificates must validate for the configured hostname. For a private CA,
build it into the worker's system trust store; do not disable verification.

The policy file must exist at that absolute path on the Docker host. Also bind
mount it read-only at the same path into the manager so startup can validate it.
The reference Compose file already passes the four environment settings to both
services; add the policy bind mount to its manager volumes. The worker runs as
UID/GID 65532 with user-namespace mapping, so set file and parent-directory access
for the mapped identity on the host. The Docker proxy authorizes the exact worker
image, network and policy mount; do not give the manager the Docker socket directly.

Create the dedicated `oc-credential-egress` bridge on the Docker host. Its name
must start with `oc-credential-`. Use the host's managed firewall to allow worker
traffic only to the configured SMB IPv4 address on TCP 445 and mail IPv4 address
on TCP 993, with established reply traffic. Deny other destinations, host services
and peer containers. A static hosts file is not an egress firewall. The reference
Compose file does not create this network or its firewall rules.

Enable both integrations in the selected instance and grant their declared scopes:

```yaml
integrations:
  browser: true
  private-readers: true
integration_grants:
  browser: [notify]
  private-readers: [secrets:use, notify]
```

Merge these keys into the existing instance configuration. Keep unrelated entries.
Restart the manager and Docker proxy with the matching configuration. People
enable the corresponding tools through their available capabilities and project
selection. They create their safe through the portal, store a matching password,
and approve requests from the chat notification. A locked safe can be unlocked
inside that same popover. Successful completion closes it and restores chat focus.

## Verification

Run the exported worker tests in an isolated environment:

```sh
python3 -m venv /tmp/workspace-readers-venv
/tmp/workspace-readers-venv/bin/pip install -r services/credential-connectors/requirements-test.txt
/tmp/workspace-readers-venv/bin/python -B -m pytest -q -p no:cacheprovider services/credential-connectors
```

These tests use protocol fixtures; they do not log in to real servers. Before
enabling users, test the deployed configuration with a dedicated test account:

1. Confirm a locked safe cannot run a read, and unlocking alone starts none.
2. Approve one allowed directory listing and file read; verify the result.
3. Approve a mail read with known messages in INBOX and a child folder, including
   read and unread messages. Confirm ordering and unchanged read flags.
   List a hierarchy with more than 200 entries and follow its continuation;
   search a folder outside INBOX, read a returned UID, and follow reply references
   across the chosen folders. Confirm that the approval shows the exact selection.
4. Reject a request and confirm no result is delivered. Lock the safe and confirm
   subsequent reads require a new unlock and approval.
5. Verify the egress firewall denies other destinations and the disposable worker
   disappears after success, failure and cancellation.

Do not use real passwords in command lines or test fixtures. A successful local
test suite does not establish server compatibility or correct host firewall rules.

## Protocol references

- [IMAP4rev1: mailbox hierarchy, UIDVALIDITY, SEARCH and BODY.PEEK](https://www.rfc-editor.org/rfc/rfc3501.html).
- [IMAP threading algorithms](https://www.rfc-editor.org/rfc/rfc5256.html).
  The related-mail lookup uses explicit reference headers; it does not implement
  the complete server THREAD/REFERENCES algorithm or subject-based fallback.

SMTP implementation uses the standard-library [SMTP client](https://docs.python.org/3/library/smtplib.html)
and [EmailMessage](https://docs.python.org/3/library/email.message.html).
