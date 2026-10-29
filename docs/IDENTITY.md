# Username identity guard

The username is the exact, case-sensitive external account key, with a unique
index. Its stored internal UID, slug, slot, files, chats and consent stay unchanged.
A renamed username is a separate account, never an automatic data transfer.

At the trusted-header boundary, a present mapped UID must match `[0-9a-f]{64}`
and is kept byte-for-byte. A present but empty or malformed UID fails closed.
Only an absent UID header triggers derivation, or `OC_IDENTITY_HEADER_UID=-`
explicitly disables reading a UID header and always derives, ignoring any incoming
UID fields. The bootstrap UID is the lowercase hex encoding of
`sha256(issuer + "\x00" + subject)` (UTF-8 bytes, one NUL separator). This accepts
ordinary OIDC subjects, including UUIDs, without weakening filesystem validators.
This is only a candidate for new accounts: the store looks up the username and
uses its existing UID after checking the issuer/subject binding. No stored value
is migrated or rehashed. If a new username's candidate UID is already occupied,
the store's existing deterministic collision handling allocates a separate key.

## Bring your own OIDC provider

Supported pattern: an OIDC-capable authentication proxy validates login, tokens
and sessions; the edge calls forward-auth and replaces identity headers; the
manager trusts only configured direct proxy peers. The manager contains no OIDC
client, discovery, token exchange or JWKS validation. The supplied Authentik
Proxy Provider remains the default. An oauth2-proxy overlay supplies the alternate
path without changing manager code.

| Manager option | Default | Purpose |
|---|---|---|
| `OC_IDENTITY_ISSUER` | `authentik` | Fixed namespace, never read from a request |
| `OC_IDENTITY_SUBJECT_HEADER` | `X-Authentik-Uid` | Stable, non-reassignable person ID |
| `OC_IDENTITY_HEADER_UID` | `X-Authentik-Uid` | Bootstrap UID candidate; `-` disables the header and always derives |
| `OC_IDENTITY_HEADER_USERNAME` | `X-Authentik-Username` | Exact account key; surrounding whitespace trimmed |
| `OC_IDENTITY_HEADER_EMAIL` | `X-Authentik-Email` | Profile email |
| `OC_IDENTITY_HEADER_NAME` | `X-Authentik-Name` | Optional display name |
| `OC_IDENTITY_HEADER_GROUPS` | `X-Authentik-Groups` | Group names |
| `OC_IDENTITY_GROUPS_SEPARATOR` | `\|` | Literal separator; each group is trimmed, empty entries discarded |
| `OC_LOGOUT_URL` | `/outpost.goauthentik.io/sign_out` | All four sign-out links, in both languages |
| `OC_TRUSTED_PROXY_CIDRS` | none; required | Direct edge peers; example `172.30.0.2/32` |

Both defaults now come from `instance.yaml` (`defaults`); the existing env
variables override them for the transition release. Select the file with
`OC_INSTANCE_FILE`; public exports have no flagged default and require explicit
selection when multiple instances are embedded. Without a `default: true` flag,
only a sole embedded `minimal` is selected automatically. Minimal keeps the values above. Loading an instance does not migrate or rebind identities.

The mapped field headers must be valid, non-empty HTTP header names and
case-insensitively distinct. Only the UID mapping accepts `-` to disable its header;
username, email, name, groups and subject mappings cannot be disabled. The subject header may reuse a mapped field (normally
UID). Missing, duplicate or malformed subjects still fail closed. Unset or empty
environment variables use instance defaults, then built-in defaults; whitespace
is not a valid header name. A separator may contain multiple characters but must
be non-empty and contain no CR, LF or NUL. Logout accepts a local absolute path
or an HTTP(S) URL without embedded credentials. These options may also be supplied
as `instance.yaml` defaults; environment values take precedence. Loading an
instance does not migrate identities. Issuer and subject defaults already live
in the supplied instance files.

Complete claim-to-header mapping:

| Field | Authentik Proxy Provider | oauth2-proxy with `--provider=oidc --set-xauthrequest=true` |
|---|---|---|
| Issuer | Fixed `OC_IDENTITY_ISSUER`, default `authentik` | Fixed namespace chosen by operator; `OIDC_ISSUER_URL` separately configures discovery |
| Subject | Authentik stable user UID: `X-Authentik-Uid` | OIDC `sub`: `X-Auth-Request-User` |
| UID candidate | Same `X-Authentik-Uid`, required to be 64-hex when present | `OC_IDENTITY_HEADER_UID=-`; always derive from issuer and the subject in `X-Auth-Request-User` |
| Username | Authentik username: `X-Authentik-Username` | `preferred_username`: `X-Auth-Request-Preferred-Username` |
| Email | Authentik email: `X-Authentik-Email` | `email`: `X-Auth-Request-Email` |
| Display name | Authentik name: `X-Authentik-Name` | Not emitted by stock `set-xauthrequest`; map to unused `X-Auth-Request-Name`, resulting in an empty name |
| Groups | Authentik group names: `X-Authentik-Groups`, pipe-separated | `groups` string array: `X-Auth-Request-Groups`, comma-separated |

Configure the IdP to emit stable `sub`, unique non-reused `preferred_username`,
verified `email` and a `groups` string array. Group names must not contain the
chosen separator. Matching is exact and case-sensitive. The overlay requires
`workspace-users` for ordinary access and `workspace-admins` for `/admin`;
an administrator needs both. `OC_REQUIRED_GROUP=-` allows every authenticated
person. Separately, `OC_ADMIN_GROUP=-` disables administration; allowing ordinary
users does not grant admin rights. The base Authentik example sets both to `-`.
The manager's group checks remain independent of the proxy's allowed email domains.

### oauth2-proxy recipe (new installation)

1. Follow [INSTALL](INSTALL.md) through host, DNS, TLS, storage and base `.env`
   preparation. Do not start or bootstrap the Authentik services for this path.
   Keep the generated base `.env` values: Compose still interpolates Authentik's
   required variables, although the overlay disables those services by profile.
2. Register a confidential OIDC client with callback
   `https://<OC_DOMAIN>/oauth2/callback`. Enable authorization code with PKCE S256
   and scopes `openid email profile groups`. Supply the claims above. Keep issuer
   and TLS verification enabled. The provider must support the requested scopes.
3. Add `OAUTH2_PROXY_IMAGE` (a reviewed oauth2-proxy v7 image digest),
   `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, and
   `OIDC_EMAIL_DOMAINS` (allowed email domains, comma-separated) to `.env`.
   Generate `OAUTH2_PROXY_COOKIE_SECRET` with `openssl rand -base64 32`.
   Choose `OC_IDENTITY_ISSUER` once for this new installation. Keep `.env` mode 0600.
4. Apply the supplied overlay from `deploy/example`:

   ```sh
   docker compose -f compose.yaml -f compose.oauth2-proxy.example.yaml config --quiet
   docker compose -f compose.yaml -f compose.oauth2-proxy.example.yaml build manager runtime-image
   docker compose -f compose.yaml -f compose.oauth2-proxy.example.yaml pull traefik oauth2-proxy egress litellm
   ```

   Run the renderer and `chmod` commands from INSTALL section 4 to populate
   `/srv/opencode/base/etc-opencode`; skip its Authentik startup/setup commands.
   Then start the alternate stack:

   ```sh
   docker compose -f compose.yaml -f compose.oauth2-proxy.example.yaml up -d
   ```

   The overlay mounts `traefik.oauth2-proxy.yaml`, installs the full manager header
   map, and keeps Authentik/PostgreSQL behind the inactive `authentik` profile.
   No manager port is published on the edge. Trust stays at `172.30.0.2/32`;
   neither forwarded client IPs nor the entire Docker subnet gain header trust.

The recipe uses oauth2-proxy's [static-upstream forward-auth integration](https://oauth2-proxy.github.io/oauth2-proxy/7.8.x/configuration/integration/#forwardauth-with-static-upstreams-configuration):
`/` redirects unauthenticated visitors to login and returns a static 202 when
signed in. `/oauth2/auth` alone returns 401 and would need an additional redirect
middleware. Cookies cover the portal and its person subdomains; redirects are
restricted to that domain. Cookie refresh during forward-auth is disabled in
this minimal recipe; expiry requires login again. Large token/group sets can
exceed cookie limits and require a separately configured server-side session store.
The [header options](https://github.com/oauth2-proxy/oauth2-proxy/blob/master/docs/docs/configuration/overview.md)
describe the four response headers copied by Traefik.

Callback paths and sign-out belong to the proxy. Traefik sends `/oauth2/` directly
to oauth2-proxy at higher priority, without forward-auth or manager consent.
The Authentik configuration similarly routes `/outpost.goauthentik.io/` to its
outpost. The manager has no provider callback exception in its consent gate.
`OC_LOGOUT_URL=/oauth2/sign_out` clears the proxy cookie only; the IdP session can
still log the user back in. For full logout configure the provider's supported
end-session URL through an encoded `rd` parameter and add only that destination
to the proxy redirect allowlist. See the proxy's [sign-out semantics](https://oauth2-proxy.github.io/oauth2-proxy/7.3.x/features/endpoints/#sign-out).

At ingress, `authResponseHeadersRegex` removes all client-supplied
`X-Auth-Request-*` and `X-Authentik-*` fields before trusted response values are
copied, including absent optional fields. Forward-auth receives only the cookie
and edge-generated forwarding metadata. Before runtime proxying, the manager
removes every mapped header, the subject header, the entire `X-Authentik-*`
prefix and cookies. It replaces Authorization with the runtime credential.
Never expose the manager edge listener directly or let a second untrusted
service use the trusted peer address. Custom mappings require matching edge
replacement rules; changing only manager settings is insufficient.

### New-install verification

Repository checks exercise the shipped YAML/template, header response fixtures,
group mapping, UID derivation, header stripping and both-language logout links:

```sh
cd manager
go test -count=1 ./internal/config ./internal/identity ./internal/router ./internal/store ./internal/portal
```

`TestOAuth2ProxyRecipe` checks the actual example mapping and callback route;
it does not perform a live OIDC authorization exchange. On the new installation:

1. In a private browser window, open the portal. Confirm login returns through
   `/oauth2/callback`, then the consent page. Decline consent and test sign-out.
2. Sign in as a non-admin `workspace-users` member. Accept consent, create a
   project, open its runtime and reload. Confirm the same UID/slug and files remain.
   Verify `/admin` is denied. A user lacking `workspace-users` must be denied access.
3. Sign in with both groups. Confirm `/admin` opens. Change `OC_ADMIN_GROUP=-`,
   restart manager and confirm administration is denied while ordinary access works.
4. Send forged identity headers without a session through Traefik: expect login,
   never the forged account. With a valid session, forged headers must not change
   username, subject, groups or access. A direct request from any non-trusted peer
   to manager must return 403 regardless of headers or `X-Forwarded-For`.
5. On a disposable staging runtime, inspect upstream request headers: no mapped
   identity field, subject, Authentik field or cookie may arrive. Do not log tokens
   or runtime Authorization. Check login and cookies on a person subdomain too.
6. Test all four sign-out locations (navigation, declined consent, deleted account,
   no access), in English and German. Verify proxy cookie removal and separately
   verify the intended IdP logout behavior. Restart the stack and recheck persistence.

Live provider/browser verification remains an installation acceptance step.

## Migration of existing accounts

Changing environment variables never transfers data. A changed username creates
a separate account. A changed issuer can refuse startup. A changed subject under
the same issuer blocks that username until an administrator verifies ownership
and explicitly rebinds it; rebinding grants all existing account data.

Before switching an existing installation:

1. Stop manager processes and runtimes. Back up SQLite consistently (including
   any WAL state), all user directories and secrets. Test restoring the backup.
   Inventory UID, exact username, issuer, subject and pending blocks.
2. Build an operator-reviewed old-to-new identity table for every account. Verify
   each person with the IdP operator, including admins. Check exact and Unicode
   case-folded username collisions and duplicate target `(issuer, subject)` pairs.
   Check incoming usernames against every existing account, not only active users.
   Resolve collisions, unbound legacy ownership and pending blocks before switching.
   Do not use display names or email equality alone as proof of ownership.
3. For unchanged subject IDs, the namespace-only procedure below is sufficient
   after ownership verification. For changed subjects within the retained namespace,
   keep usernames unchanged, test one known account, then use the existing admin
   rebind workflow for each verified pending subject. Keep a separately verified
   admin account accessible; do not clear bindings to bypass the guard.
4. If issuer and subjects both change, prepare and review a per-account offline
   rebind against that verified table. Update only issuer/subject bindings in a
   transaction, conditioned on each exact old UID/username/issuer/subject. Require
   exactly one affected row per mapping and repeat collision checks before commit.
   There is no automatic provider migration command; the namespace-only SQL below
   does not perform this operation. Keep UID, slug, slot and data paths unchanged.
5. Verify startup, consent, project ownership, admin access and runtime isolation
   against the backup inventory before reopening access. Retain the reviewed
   migration mapping and audit; never infer success from a successful login alone.

Migration 21 adds nullable `users.identity_issuer`, `identity_subject`,
`blocked_issuer` and `blocked_subject` columns, the unique username index, and
`identity_releases`. Before any schema change, its migration function checks
for exact and case-insensitive duplicate usernames (Unicode simple case folding).
The diagnostic lists the duplicate names, leaves migration 21 unapplied and
changes no data. Resolve ownership of those accounts explicitly and retry;
accounts are never merged automatically. Lookup and the unique index remain
case-sensitive.

On startup, before runtime initialization or opening listeners, the manager
counts accounts whose stored or pending issuer differs from
`OC_IDENTITY_ISSUER`. Any mismatch refuses startup with the count and the
configuration name. Legacy accounts with no binding are ignored. Request-time
checks also refuse an issuer mismatch without creating a subject block.

This startup error is safer than recording a block for every user: an
accidental configuration change leaves bindings and pending blocks untouched,
and restoring the configuration restores service. Changing
`OC_IDENTITY_ISSUER` rebinds nobody. Subject comparisons happen only within the
same issuer namespace.

For an intentional namespace rename, stop all manager processes and back up
the database. First verify that stable subject IDs still identify the same
people; this procedure is not a migration to an unrelated identity provider.
With the manager stopped, explicitly rename the old namespace in one SQL
statement (replace the example literals):

```sql
UPDATE users
SET identity_issuer = CASE WHEN identity_issuer = 'old-issuer'
                           THEN 'new-issuer' ELSE identity_issuer END,
    blocked_issuer = CASE WHEN blocked_issuer = 'old-issuer'
                          THEN 'new-issuer' ELSE blocked_issuer END
WHERE identity_issuer = 'old-issuer' OR blocked_issuer = 'old-issuer';
```

Set `OC_IDENTITY_ISSUER=new-issuer`, then restart. Subjects, data and existing
blocks stay unchanged; historical release hashes remain as recorded. Review
any remaining mismatch count before starting service. For an installation
that tested the earlier provider-URL binding, `old-issuer` is that stored URL;
there is no automatic conversion to `authentik`.

Every authenticated request checks the stored binding before consent, profile
refresh, portal data or runtime routing. New accounts bind when consent permits
account creation. Existing unbound accounts bind on their next request. A
mismatch stores the first conflicting pair and blocks the username, including
requests from the original subject, until an admin acts. No environment is
started by a blocked request. The response is a neutral German/English 403 page;
only static assets and the cookie-only language switch remain available.
Error events contain hashes of both bindings, never their full subject values.

The existing `/admin` page, protected by `OC_ADMIN_GROUP` and the portal's CSRF
checks, offers one action: rebind to the recorded conflicting subject. The form
shows hashes and warns that the new identity receives all existing data. Stale
or replayed submissions fail. Rebinding and its audit row are one transaction:
timestamp, account UID, admin UID, old/new subject hashes. Audit rows are removed
with the target account. The action works without enabling chat evaluation.

The IdP must still never reuse usernames. In particular, migration cannot
identify reuse that happened before a legacy account first binds. An admin
must verify ownership with the IdP operator before rebinding. If the only admin
account is blocked, another trusted member of the admin group is required.

`shortcut:` already-open runtime streams are not disconnected by the guard;
new HTTP requests and handshakes are checked. Add stream revocation when the
identity contract includes termination of established sessions.

Identity regression checks (Go 1.27):

```sh
cd manager
go vet ./...
go test ./internal/identity ./internal/store ./internal/config ./internal/router ./internal/portal ./cmd/manager
```

## Legacy restricted support sessions

Current Assistant cards start normal OpenCode sessions in the person's shared
runtime. The restrictions below apply only to the older manager-owned support
executor, not to the current card flow. See [instance configuration](instance.md).

The legacy support executor uses the same authenticated portal identity and internal
UID; task definitions introduce no second login or user identity. Session IDs are
owner-scoped lookups in manager-owned storage, not bearer credentials. At each
turn the manager captures the account's creation/generation and issuer/subject
binding. Blocked/rebound/deleted accounts and expired two-minute turn leases
cannot commit results. Every model/tool step and returned result rechecks
ownership, current consent, pin and source grants. The commit repeats account,
pin, consent, session revision and lease checks transactionally.

Support sessions never enter the person's shared OpenCode runtime. They have no
shell, filesystem or child-session executor. Public runtime MCP and LLM routes
reject the reserved `ses_profile_` namespace; only the internal executor can
make scoped calls with it. General projects retain existing network identity
and catalog behavior. See [integration contracts](CONTRACTS.md).
