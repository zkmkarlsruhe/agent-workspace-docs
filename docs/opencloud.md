# OpenCloud connection

This integration uses a registered public OAuth client, authorization code with
PKCE S256, and bearer tokens. It does not use Nextcloud Login Flow v2, Basic auth,
OCS account discovery, or `/remote.php/dav/files/<username>`.

## Operator setup

Register a separate public client with the OpenCloud identity provider:

- Authorization code with PKCE S256; no client secret.
- Exact redirect URI: `https://<workspace-host>/connections/opencloud/callback`.
- Scopes: `openid profile offline_access`; permit refresh tokens for continued access.
- UserInfo must return `sub` and `preferred_username`. The latter must match the
  person's workspace username (case-insensitive). The stored subject must remain
  unchanged on reconnect. Account mapping can use the existing `house.LoginFor` hook.

For OpenCloud's built-in IDP, add the client to `idp.clients` in `opencloud.yaml`.
Include the existing standard clients too: setting this list replaces the default
list. A new client entry has this shape:

```yaml
idp:
  clients:
    # Keep the existing Web, Desktop and mobile client entries here.
    - id: workspace
      name: Workspace
      trusted: false
      secret: ""
      redirect_uris:
        - https://<workspace-host>/connections/opencloud/callback
      application_type: web
```

Set manager environment variables through the operator's existing configuration:

```text
OC_OPENCLOUD_URL=https://<opencloud-host>
OC_OPENCLOUD_ISSUER=https://<identity-provider-issuer>
OC_OPENCLOUD_CLIENT_ID=workspace
OC_OPENCLOUD_REDIRECT_URI=https://<workspace-host>/connections/opencloud/callback
```

Use the issuer exactly as published in its discovery document, including any
trailing slash. It may differ from the storage origin. Discovered authorization,
token, UserInfo and optional revocation endpoints must share the configured
issuer's origin. HTTPS and normal certificate verification are required.
Configure trusted private certificate authorities through the manager's normal
system trust bundle. There is no insecure production switch.

Enable the integration and its existing workspace scopes in the instance layer:

```yaml
integrations:
  opencloud: true
integration_grants:
  opencloud: [workspace:read, workspace:write]
```

The integration is off by default. Existing Nextcloud configuration is independent.
The operator endpoint alone does not enable the integration. No database migration
is required: tokens use the existing encrypted connection and revocation tables.
Keep `OC_MASTER_KEY` stable. Tokens are bound to owner, connection ID, storage URL,
issuer and client ID. Disconnect before changing these connection settings.

People must visit **Connections**, choose **OpenCloud**, and sign in themselves.
The callback requires the authenticated workspace identity and single-use state.
Pending login state lasts 20 minutes and is lost on manager restart. Workspace
consent remains subject to the existing portal/router checks; setup accepts no
consent for existing users.

## Files

`opencloud_list` with an empty path discovers the person's accessible drives using
`GET /graph/v1.0/me/drives`. Results include each drive's ID and display name.
Use `<drive-id>/<relative-path>` for subsequent lists and fetches. The adapter
uses the drive's validated `root.webDavUrl`, under `/dav/spaces/<root-id>`.
Deleted spaces are omitted. Redirects and foreign origins are refused.

`opencloud_fetch` copies a file into the current chat project's inbox using the
existing workspace upload path. It cannot select another person's account or
another project. File contents and names are data, never instructions.

Optional writes require:

```text
OC_OPENCLOUD_WRITE_ROOT=Workspace
```

Create that transfer folder in each desired space using OpenCloud itself.
`opencloud_upload` then accepts a local project `file` and remote `path`. It uses
`If-None-Match: *` when `previous_revision` is omitted. For a reviewed replacement,
supply the exact quoted revision from a fresh listing; the request uses `If-Match`.
A conflict is returned without retrying or overwriting. Wildcards, weak tags,
multiple revisions, dot paths and writes outside the transfer folder are refused.
The parent folder must exist. No delete, share, move or automatic sync operation
is exposed. Without a write root, the upload tool is absent and direct calls fail.

Limits: 500 entries per listing; 8 MiB per Graph/DAV response; at most 10 drive
pages and 500 total drives; 2 GiB per file, including unknown-length streams.
Listings exceeding limits fail explicitly. Requests have timeouts and never follow
redirects carrying credentials.

Tokens stay encrypted in the manager and never enter workspace containers.
Refreshes serialize with disconnect/reconnect. Invalid grants mark the connection
expired; users reconnect through the portal. If discovery publishes RFC 7009
revocation, disconnect revokes both tokens before deleting the local connection.
Failed revocations retain the connection or enter the existing encrypted retry
queue. When the issuer offers no revocation endpoint, disconnect removes local
access only; remove the grant in the identity provider to invalidate outstanding
tokens. OpenCloud's built-in IDP in the local 9.0.0 smoke did not advertise revocation.

## Verification

From the repository root:

```sh
go -C manager test \
  ./internal/opencloud ./internal/house ./internal/config ./internal/ncguard \
  ./internal/filesource ./internal/gateway/mcp ./internal/portal \
  ./internal/integration ./internal/instance ./cmd/manager
```

HTTP fixtures cover PKCE exchange, owner/state binding, replay, denial, expiry,
username mismatch, encrypted storage, refresh serialization, revocation retries,
provider isolation, Graph drive discovery, DAV listing/fetch, conditional writes,
SSRF/redirect refusal, size bounds, project binding, and disabled capabilities.

A temporary loopback-only OpenCloud 9.0.0 container was started from the official
rolling image. Its digest is recorded in the local test evidence.
Discovery and sign-in succeeded. The scripted consent continuation returned
`interaction_required`, so real token exchange and authenticated DAV were not
verified by that smoke. The temporary container and data were removed. No external
endpoint or real user credentials were supplied; those live checks remain open.

## Upstream references

- [Custom OIDC clients](https://docs.opencloud.eu/docs/dev/server/services/idp/information/)
- [Graph spaces and drive roots](https://docs.opencloud.eu/docs/dev/server/apis/http/graph/spaces/)
- [WebDAV paths and conditional uploads](https://docs.opencloud.eu/docs/dev/server/apis/http/webdav/)
- [Official temporary Docker setup](https://docs.opencloud.eu/docs/admin/getting-started/container/docker/)
