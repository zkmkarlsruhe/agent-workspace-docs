# Managed container plugins

An operator can add a mountless HTTP/MCP application without changing Go code.
Install its manifest with a `runtime` declaration in `OC_INTEGRATIONS_DIR`. Both the
manager and the independent Docker socket proxy must read the same immutable
manifest directory and `OC_WORKLOAD_PROFILES_FILE`. Their effective policy digest
includes every installed container declaration, image digest, resource limit and
manifest contract. A mismatch rejects container creation.

The [container-hello example](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/examples/container-hello/README.md) includes a
working server, Dockerfile, manifest and Compose overlay. Its browser page and MCP
`greet` tool run in the same isolated worker. It uses only the Go standard library.

## Declaration and installation

The normal schema-1 integration fields still apply. A managed plugin adds:

```json
{
  "schema": 1,
  "name": "container-hello",
  "version": "1.0.0",
  "runs": "service",
  "image": "registry.example.org/workspace/container-hello@sha256:<actual-64-hex-digest>",
  "runtime": {
    "network_slot": 1,
    "port": 8080,
    "memory_mib": 128,
    "cpu_milli": 250,
    "pids": 32
  },
  "mcp": "/mcp",
  "tools": ["greet"],
  "portal": [{"path": "/app", "roles": ["user"]}]
}
```

Replace the illustrative digest before loading. Use a unique `network_slot` from
1 to 30 across installed plugins, including disabled plugins. The port must be
1024–65535. Memory is 64–8192 MiB, CPU 100–4000 millicores and processes 16–512.
The entrypoint comes from the pinned image. The image must run as UID/GID 1000,
listen on `0.0.0.0:<port>`, and tolerate a read-only root with only a 64 MiB `/tmp`
tmpfs. Memory limits include tmpfs. There are no command/environment overrides,
host mounts, workspace mounts, published ports, custom Docker options or egress.
Unknown/duplicate fields and conflicting network slots fail startup.

1. Build and publish the image in the operator's registry. Record its immutable
   repository digest. Pull that exact digest on the Docker host; the manager does
   not have image-pull authority through the socket proxy.
2. Install the manifest as a regular `.json` file in an operator-owned directory.
   Do not give user containers write access to this directory. Mount it read-only
   into both manager and Docker proxy and set `OC_INTEGRATIONS_DIR` on both.
3. Enable the plugin in the instance, set `capabilities.projects: true`, and
   configure the catalog. Declare any required `integration_grants`. Restart both
   processes with the same policy snapshot. No database migration is needed.
4. The plugin appears automatically as an optional capability. The person enables
   it globally and explicitly selects it for a general project. Legacy projects
   with inherited capabilities must select it explicitly. Assistant projects are
   excluded.
5. In a root chat in that project, call its declared tools. `open_browser` is added
   automatically when the manifest has portal pages. It returns an authenticated
   `https://plugin-<random-id>.<OC_DOMAIN>/<declared-path>` URL. The existing wildcard
   DNS, certificate and forward-auth route must include these hosts.

The MCP endpoint is `/mcp/project/<project-id>/<plugin-name>` on the internal
manager gateway. The catalog writes that endpoint into the project's configuration.
Only the current personal runtime's source address is admitted. Discovery requires
project authority; execution also requires the validated root chat in
`_meta.ai.opencode/sessionID`. Tool arguments cannot choose an owner, host, project,
image or filesystem path. `open_browser` is reserved and must not be declared as an
upstream tool. The upstream must implement streamable HTTP MCP with initialization,
`tools/list` and `tools/call`. Startup initialization is retried for up to 15 seconds;
tool executions are never retried. Inventory must match the manifest exactly across
all pages: missing, extra, duplicate and null tools reject discovery and execution.
Requests and responses are bounded. Calls repeat current authority and session checks
every two seconds, cancel the upstream HTTP request on revocation, and recheck before
returning results. Cancellation cannot undo an operation already performed upstream.

## Isolation and browser contract

Each user/plugin pair has a dedicated internal bridge: `oc-p<user-slot>-<network-slot>`.
The reserved range is `10.92.0.0/16`; it must not overlap other host networks. Each
bridge uses a /29 with only the manager at offset 2 and the worker at offset 3.
Docker's isolated gateway mode is mandatory. DNS stays local. Neither user or
assistant containers nor the egress proxy may join it. The socket proxy independently
checks the exact image, owner/project labels, policy digest, resource limits, complete
container shape, network subnet, address and manager-only attachment. Plugin source
addresses cannot authenticate to the public edge or operator listener.

There is one ephemeral worker per user/plugin pair. Opening the same plugin in
another project cancels and drains the old browser requests, removes the old worker
and network, then creates a new allocation. No project state is carried over. Workers
are charged to the existing persistent workload quotas. Failed removal retains its
allocation and quota for retry. Revoked, deleted and superseded allocations are
removed during reaping. Startup retires old plugin allocations and browser locators;
it never replays an application operation. The controller records the exact network
in the allocation fingerprint before creating the bridge. Cleanup disconnects its
endpoints (including the manager), then removes that bridge and container. Failed
network cleanup keeps the allocation and quota for reconciliation. This also covers
interrupted creation, missing containers, removed declarations and orphan containers
after a manager restart. Allocation and network ownership checks fence stale cleanup
and prevent it from touching another user's or project's replacement allocation.

Portal paths authorize their exact path and descendants. The longest matching
path supplies the role requirement. `user` means the authenticated account;
`admin` is mapped from `OC_ADMIN_GROUP`; other role names match authenticated
identity-provider groups. The URL's random component is only a locator. Every
request verifies the current owner, project, root chat, grants and consent.
Long-running browser requests repeat authorization checks every two seconds.
Identity-provider group claims are those authenticated for the current request;
the extension authorization hook can enforce additional current account policy.

Plugin HTML is never served under the core origin. Requests lose cookies,
authorization and identity headers before forwarding. Responses cannot set cookies
or CORS grants. CSP restricts scripts/connections/forms to the plugin origin,
blocks workers, embedding, external frames and top navigation, and applies a
sandbox. Browser writes and WebSockets require an exact matching Origin. All page
assets and browser endpoints must live under a declared portal path. External
redirects are rejected. HTTP cookie authentication inside a plugin is unsupported;
the manager supplies session authentication at the edge. Persisted personal data,
external login and filesystem capabilities belong to the extension service, not
this mountless container adapter.

## Extension service integration

`containerplugin.Service.Authorize(context.Context, Access) error` is mandatory and
fails closed when absent. `Access` contains the trusted manifest, current store
user and project, operation (`discover`, `call`, `browser`, `maintain`), tool and
session. The adapter must verify the selected manifest revision, current extension
consent/grants and account eligibility. `BindSession` must bind a validated root
chat to the requested extension, tool, session, project ID/folder, account incarnation
and runtime generation. These hooks are invoked before discovery/execution/browser
access, during calls and before returning results; they do not accept authority from the
plugin's response.

`cmd/manager/configureContainerPlugins` accepts the extension authorization callback
as its final argument. Existing selection, explicit user/project capability, base
consent and shared-runtime checks remain mandatory around that callback. Production wires the persistent extension service into that callback. Its database
grants and integration consent are checked on every operation. With no callback,
manifests requiring separate integration consent are denied.

Account deletion revokes admission, then calls `Service.CloseUser(ctx, uid)` for
synchronous cleanup before disconnecting external providers. It cancels browser streams before removing containers. `Service.Sweep`
provides startup/reaper cleanup and retries failed removals. Extension event delivery,
deletion contracts and durable plugin data are owned by the separate extension
service; this adapter neither records consent nor acknowledges deletion events.

## Verification

Run from `manager/`:

```sh
go test ./internal/containerplugin ./internal/runtime ./internal/dockerproxy ./internal/router ./internal/catalog ./internal/integration ./cmd/manager
go test -race ./internal/containerplugin ./internal/runtime ./internal/dockerproxy ./internal/router
```

The end-to-end fixture builds and runs the shipped example executable, then exercises
MCP discovery/execution, the browser entry, persistent allocation, revocation and
failed cleanup. Focused regressions cover exact paginated inventory, in-flight grant
and session revocation without replay, result suppression after revocation, queued
stale calls, mismatched bindings and fenced/restarted network cleanup. Its container engine is a deterministic test double. Separate proxy
tests reject image/policy drift, extra mounts, privilege, commands, environment,
resource overrides, DNS changes, extra networks and unauthorized joins. A local Docker 29.9.0 smoke test also verified MCP execution, browser ownership and
origin checks, header stripping, kernel resource limits, blocked cross-user/plugin
traffic and external egress, active revocation, and removal of all three test
containers, allocations and bridges. Wildcard TLS and forward-auth behavior for
a newly installed plugin still require a deployment smoke test on the operator's host.
