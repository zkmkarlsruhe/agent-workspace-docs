# Assistant project isolation

Each assistant project has a dedicated OpenCode container. Two projects owned by
one person do not share files, chat databases, state or runtime credentials.
Ordinary projects still share the person's general environment. `shared` assistant
mode means repeated conversations in one assistant project, never shared storage
between people or between different assistants.

## Enforcement

- The provisioner creates private directories below
  `<users-root>/<uid>/assistants/<project-id>/`. Only this project's workspace,
  data, state and read-only managed configuration enter its container. They count
  against the owner's existing disk quota.
- The runtime uses the normal non-root, read-only-root, capability-drop and
  resource-limit settings. Production requires the existing user-namespace mapping.
- Each runtime has an internal isolated bridge. Only the manager joins it.
  There is no egress proxy, external DNS or direct Internet access. The default
  prefix is `10.91`; `OC_ASSISTANT_NET_PREFIX` must match in manager and Docker proxy.
- The gateway resolves owner and project from the runtime's source address.
  Caller-supplied project headers cannot select another project. Only the assigned
  model and approved assistant MCP routes are admitted. Existing budget, source
  allowlist, account and consent checks remain in force.
- Configuration comes from the database and is mounted read-only. Project config
  loading is disabled. Managed policies deny undeclared tools, outside-directory
  access and writes to hidden paths or runtime configuration. Formatters are off.
- The browser proxy authenticates the owner on `assistant-<project-id>.<domain>`.
  It admits chat and file views, binds new sessions and uploads to this project,
  and rejects terminal, shell, configuration, credential and integration-control
  APIs. The OpenCode web client remains the chat interface.
- Changed definitions, withdrawn consent, disabled accounts and deleted projects
  revoke execution. Streams recheck authorization every five seconds. A runtime
  address is reused only after requests end and the old container/network vanish.
  Owner file access, export, trash and deletion remain available independently of
  execution grants.

## Existing projects and lifetime

While shared assistant data still exists, its owner’s general runtime cannot make
model or tool calls, including from cached sessions or forged project headers.
The periodic lifecycle pass migrates active projects once the owner’s runtime is idle.
Opening an assistant project also starts migration. Old trash can be restored or
permanently deleted through the portal.
Private assistant runtimes continue to use their own grants.

When migrating an existing assistant project, the manager waits for the owner's
runtime to be idle. It ends its browser leases, transfers files and conversations,
checks conversation content and the file archive fingerprint, then removes the old
copies. The general environment stops and can be reopened. Failed transfers retain
untransferred source data and do not expose the new runtime.

Old Git hooks and links are excluded from the live workspace. The original file
archive remains inert in this project's private state, preserving Git history.
Permanent project deletion removes that archive together with files and chats.
Trash and restore retain private storage. Account deletion removes every project.
Container stop or manager restart preserves storage; runtime workers are recreated
on demand with current policy. The common running-container cap includes assistants.

## Validation and boundary

Tests cover cross-project gateway attribution, Docker API mount/network restrictions,
filesystem symlinks, request binding and migration verification. Native OpenCode
checks cover allowed project reads/writes, denied outside reads, denied shell/hook/
policy writes, and attempted session/project permission overrides. Docker bridge
checks cover gateway reachability and denied peer, host, Internet and external DNS
access. Session transfer is checked with the deployed runtime API.

This is container isolation on a shared Linux kernel, not a virtual machine boundary.
The manager and its provisioner remain trusted. Model answers and source text are
untrusted; isolation does not make an answer correct or extend a source grant.
