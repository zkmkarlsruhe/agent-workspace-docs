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

The mail scan is bounded to 256 listed folders, 10,000 candidate messages and
16 MiB of IMAP response data. Exceeding a scan limit fails explicitly, rather
than returning an incomplete selection as the latest messages. Changes during a
read can also fail it. The worker has a 35-second deadline; the manager allows
45 seconds including container handling. There are four concurrent worker slots.
There is no mail sending, mailbox draft creation, share write or background poll.

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
4. Reject a request and confirm no result is delivered. Lock the safe and confirm
   subsequent reads require a new unlock and approval.
5. Verify the egress firewall denies other destinations and the disposable worker
   disappears after success, failure and cancellation.

Do not use real passwords in command lines or test fixtures. A successful local
test suite does not establish server compatibility or correct host firewall rules.
