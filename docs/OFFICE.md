# Live Office editing

The optional `office` integration connects the existing project MCP gateway to a
private HTTP browser worker. It supports ONLYOFFICE documents and spreadsheets
through `nextcloud-browser-bridge`. No Nextcloud or editor extension is installed.

## Enable

1. Build and publish the bridge image from its repository. Set `OC_OFFICE_IMAGE`
   to the same **digest-pinned** reference on the manager and Docker proxy. Preload
   that image on the Docker host; the manager does not pull images. In the example
   stack, `docker compose --profile office run --rm office-image` performs the pull.
2. Configure exactly one Nextcloud house service and the egress container. In the
   instance file set `integrations.office: true` and grant
   `integration_grants.office: [nextcloud:live-edit]`. Keep `nextcloud` enabled.
3. Allow only worker addresses to reach the actual Nextcloud and ONLYOFFICE hosts
   through Squid, as described below. The browser authenticates and navigates through
   this proxy. Include every editor host used by the deployment, without broad wildcards.
4. Restart the manager and Docker proxy with that configuration. Install/reload the
   catalog entry from `deploy/catalog/mcp.json`. Connect the person's Nextcloud
   account through the portal, then enable the Office capability in the project.
5. Test with a disposable `.docx` and `.xlsx`, opened in a visible browser too.
   Use `nextcloud_list` to obtain `fileId`, then `office_open`, `office_read`,
   `office_find`/`office_capture`, `office_replace`, and read back. Confirm persistence
   after reopening independently. A successful tool response does not prove saving.

The server derives the person from the authenticated project request. Callers cannot
choose another person's credentials or worker. Assistant-chat tools do not currently
include this capability. Project permission authorizes the connected account's
Nextcloud files; it is not a per-project file allowlist.

## Egress

Workers use `10.90.<slot>.11`; user runtimes use `.10`. Do not add the Office domains
to the general package-registry ACL. Generate `deploy/example/office-egress.conf`
with the real hosts and the configured `OC_USER_NET_PREFIX` (default `10.90`):

```sh
python3 - <<'PY' > deploy/example/office-egress.conf
prefix = '10.90'
hosts = ['cloud.example.org', 'office.example.org']
print('acl office_workers src ' + ' '.join(f'{prefix}.{slot}.11/32' for slot in range(1, 255)))
print('acl office_hosts dstdomain ' + ' '.join(hosts))
print('http_access allow office_workers office_hosts CONNECT SSL_ports')
PY
```

The example mounts this include before `internal_dst` denial, after the CONNECT
port check. This permits HTTPS to a configured institutional host even if its
address is in a blocked internal range. Other sources still hit the existing denial.
Validate with `squid -k parse`, reload Squid, and check that an Office worker can
connect while a `.10` runtime cannot. Keep the proxy private to the slot networks.

## Lifetime and failures

One worker serves one person and one runtime generation. It opens multiple documents;
the bridge deduplicates canonical Nextcloud file identities. It retains documents for
15 idle minutes and the browser worker for one idle hour. Status/list polling does not
extend that lifetime. Active calls prevent idle cleanup.

The manager delivers credentials and a random bearer token through Docker exec stdin,
into files with mode `0600` on the worker's private tmpfs. Neither the project runtime
nor container environment contains those secrets. The worker has no user-data mount,
a read-only root, dropped capabilities and bounded memory, CPU and process counts.

Disconnect, credential replacement, runtime teardown and manager shutdown close the
worker. Manager shutdown stops accepting requests and closes Office workers in parallel.
Set the manager's Compose `stop_grace_period` to `75s`, as in the example, so request
draining and browser cleanup can finish before Docker sends SIGKILL. Main workspace
containers remain running across manager restarts; Office bindings must be opened again.
Startup reconciliation stops orphan Office workers gracefully before removing them.
Failed disconnect revocation
keeps the credential row for retry but blocks its use immediately. A transport failure
invalidates the worker; only a subsequent explicit `office_open` starts another one.
No write is automatically replayed. An interrupted write may already have taken effect.

## Current boundaries

- Word editing uses explicit search matches; spreadsheets use explicit sheet/range.
- A separate browser's mouse selection is not supplied by this MCP. Remote Word mouse
  selection remains an upstream feature request; spreadsheet network selection is
  separate research, not part of these eight tools.
- `persisted: false` means the edit was checked in the editor, not independently saved
  back to Nextcloud. Concurrent external edits remain possible.
- No public-share URL entry point, arbitrary browser URL, Mail bridge or Collabora adapter.
- HTTP worker transport uses the official MCP SDK. FastMCP is not a runtime dependency.

## Validation before production

Automated tests cover project grants, per-person workers, repeated/concurrent calls,
generation changes, idle cleanup, credential invalidation, disconnect during a write,
transport failure without replay, Docker proxy restrictions and `fileId` discovery.
The bridge additionally tests browser edits, proxy authentication, HTTP authentication,
private bootstrap files and graceful container shutdown.

Production acceptance still requires the configured Squid allowlist and a complete
portal-to-editor run on the installed Nextcloud/ONLYOFFICE versions. Fixture tests do
not establish compatibility with that deployment.


