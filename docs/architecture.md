# Architecture

Agent Workspace wraps OpenCode with identity, lifecycle, storage and service
controls for multiple people. The reference deployment is a single Linux VM
running Docker Compose. It is a proof of concept; the current architecture
does not promise stable APIs, upgrades or production support.

## Components and request paths

```text
Browser
  |
  v
TLS reverse proxy <-> Authentik forward auth
  |
  v
Go manager ------------------------> SQLite: identity, projects, usage
  | portal and runtime routing
  |-> filtered Docker proxy -------> Docker: per-person containers/networks
  |-> filesystem provisioner ------> host directories and XFS quotas
  |
  `-> OpenCode runtime: one per active person
        |-> persistent workspace, config, data and state
        |-> manager model gateway -> LiteLLM -> configured model endpoint
        |-> manager integration gateways -> enabled services
        `-> egress proxy -> allowed package registries
```

The portal is at the configured base domain. Each person receives a runtime
hostname under that domain. The manager verifies the authenticated identity
against the hostname; a request for someone else's runtime redirects to the
portal. OpenCode's server password is supplied by the manager, without a
second browser login. Identity headers and cookies are stripped before
requests reach the runtime.

The example IdP is Authentik. Its proxy provider authenticates requests and
supplies identity headers through the trusted edge proxy. The manager is not
a generic OIDC client. A different IdP requires an adapter preserving this
identity contract, including the expected bootstrap UID format.

Only explicitly trusted proxy peers may provide identity headers, and the
edge must replace client-supplied values. The configured issuer is stable
instance configuration, never request metadata. The username is the current
account key; the stored issuer and subject guard against reassignment. See
[the identity decision](adr/d64-identity-guard.md) and the [IdP
precondition](privacy.md#identity-provider-precondition).

## Lifecycle and storage

One runtime serves all projects and chats of one active person. It starts
on demand, and the manager observes runtime activity to stop idle environments
or drain environments that reach their lifetime limit. A stopped runtime can
be recreated with the same persistent data. Reconciliation handles manager
restarts and orphaned containers.

Each task has a project folder with input, result and working areas. Folder
names come from the instance. Git snapshots support file undo within projects;
they are not a backup. File operations go through the person's runtime.
Project trash and account deletion have separate lifecycles, described in
[privacy](privacy.md#deletion-and-retention).

The reference layout stores manager SQLite data under
`/srv/opencode/manager/` and personal workspace, home, configuration, runtime
data and state under `/srv/opencode/users/<uid>/`. The filesystem provisioner
creates and purges personal storage and assigns XFS project quotas. Stopping
a container does not erase these directories. Backups need a consistent
snapshot of databases, data, instance configuration and keys.

## Assistants, Capabilities and session controls

Assistants launch normal sessions with a pinned, reviewed task definition. They
create a project per task or reuse a shared project while starting a new session
for each question. Ordinary projects can select Capabilities from the person's
available catalog; Assistant projects use their reviewed source/tool grants.

Optional auto-archive hides dormant root sessions without deleting their files
or transcripts, and the project page offers restore. Watchdog notices expose
silent runs and let the person interrupt a selected session. The watchdog does
not automatically abort work. See [instance options](instance.md) for defaults
and boundaries; project isolation remains unchanged.

## Isolation and trust boundaries

The supported runtime uses Docker with `userns-remap` and a shared remapped
UID range. Runtimes run as UID 1000, with a read-only root filesystem,
temporary writable mounts, dropped capabilities, no-new-privileges and
resource limits. The reference instance requires the specific host UID mapping
documented in [INSTALL.md](INSTALL.md).

Each person has an internal network. Runtimes reach the manager's gateways
and a restricted egress proxy; they do not receive unrestricted host or
internet access. Web research, if enabled, uses manager tools with URL and
destination checks. Untrusted pages and documents can still contain prompt
injection. A model's tool request must pass the same server-side policy as
any other request.

The manager does not mount the raw Docker socket. A separate Docker proxy
validates lifecycle requests; a separate privileged provisioner handles
filesystem ownership and quota operations. Both helpers are sensitive trust
boundaries. The manager, host administrators and backup operators can affect
or access personal data. Container isolation does not protect a person from
the operator or from a host-kernel compromise.

## Models, integrations and configuration

Model requests pass through the manager to LiteLLM. The manager supplies
credentials, sets the end-user identifier and records usage. Cost and carbon
figures are estimates based on configured coefficients. They are not invoices
or measured emissions. A runtime must not hold an upstream provider key.

`instance.yaml` selects models, branding, folder layout, consent text,
policies and integrations. Rendering produces runtime configuration from
that instance. The minimal instance explicitly selects no optional
integrations. Set `OC_INSTANCE_FILE` to the mounted YAML file. Startup rejects
an unset selection when multiple instances are embedded and none has `default: true`.
The public export removes that flag. Without it, only a sole embedded `minimal`
can be selected automatically; multiple flagged defaults fail initialization.

Builtin integrations run as trusted manager code. Catalog opt-ins and tool
allowlists restrict what a person can call. Central MCP tools use a gateway;
per-person service credentials remain in the manager. Optional toolbox
containers run with no network and mount only the person's workspace. They
share that person's files, so their commands can change or remove those files.

Structured logs support operations; SQLite stores usage accounting. External
log collection is an operator choice. Evaluation is optional and disabled in
the minimal instance. Enabling it adds stored chat snapshots, administrator
transcript access and possible model-based evaluation; see [privacy](privacy.md).

## Current limits

Service-side consent storage, durable deletion jobs, event delivery and a
scoped integration API remain contract work, not completed runtime guarantees.
There is no released stable service API. Scheduled projects, hosted project
apps and a Kubernetes deployment are not part of the reference installation.
The installation guide defines the login, project, chat and download checks
needed for a clean-VM trial.

## Decisions

These records retain the original decision numbers for source references.
They describe current, reusable choices; deployment-specific and superseded
choices are omitted.

- [D6: Per-person runtimes and hostnames](adr/d06-personal-runtimes.md)
- [D9: Task folders](adr/d09-task-folders.md)
- [D12: A dedicated manager](adr/d12-manager.md)
- [D15: Gateway-held model credentials](adr/d15-model-credentials.md)
- [D30: Restricted runtime egress](adr/d30-egress.md)
- [D33: Separate filesystem provisioning](adr/d33-provisioner.md)
- [D44: Docker user namespaces](adr/d44-docker.md)
- [D46: Manager-held service credentials](adr/d46-service-credentials.md)
- [D48: Private chats](adr/d48-private-chats.md)
- [D49: Mail text without mailbox access](adr/d49-mail.md)
- [D58: Restricted cloud-file writes](adr/d58-cloud-files.md)
- [D59: Allowlisted central MCP tools](adr/d59-central-mcp.md)
- [D60: Networkless toolboxes](adr/d60-toolboxes.md)
- [D62: Product and instance names](adr/d62-product-name.md)
- [D64: Username identity guard](adr/d64-identity-guard.md)
