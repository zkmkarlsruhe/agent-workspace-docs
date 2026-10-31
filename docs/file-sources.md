# File-source boundary

`manager/internal/filesource.Reader` is the initial provider-neutral read
capability. Existing `nextcloud_list` and `nextcloud_fetch` use it through the
Nextcloud adapter in `manager/internal/ncsync`. They retain their tool names,
arguments, capability gates, connection-expiry handling and result fields.
This is an internal migration step, not a stable extension HTTP API.

The boundary separates read, metadata and write capabilities:

| Operation | Result | Ownership |
|---|---|---|
| `List(context, path)` | Immediate children, excluding the directory itself | Adapter validates the root and bounds the response |
| `Open(context, path)` | Original byte stream, reported size and optional revision | Caller bounds actual bytes and closes the stream |
| `Stat(context, path)` | Metadata for exactly the requested resource | Optional read capability; adapter checks its root |
| `Write(context, path, body, previous, modified)` | New revision, if supplied by the provider | Separate capability; create-only or revision-conditional |

A reader is bound to one authorized connection and storage root before use.
File paths cannot select another account, endpoint or credentials. The current
Nextcloud dispatcher resolves credentials anew for every operation through the
configured connection registry. A registered reader is bound to the originating
call's context; it cannot outlive that call. The interface does not itself
implement consent, project selection, token refresh or revocation.

## Configured connections and lifetime

`filesource.Registry` snapshots operator-configured connection IDs and resolver
functions. It holds no account secrets. Its caller supplies the owner from trusted
session state, and its resolver looks up that owner's current connection for every
operation. The registry is dispatch, not an authentication layer: the dispatcher
must authorize the caller and the resolver must enforce current connection policy.
Unknown connections fail explicitly; there is no fallback to another connection.

The Nextcloud resolver uses the existing encrypted login store. Disconnecting or
expiring a connection prevents subsequent operations through an already acquired
handle. A current download uses the credentials already sent to the provider;
revocation is not a rollback of received bytes. Ending the originating invocation
cancels outstanding requests, and closing a stream releases its operation context.
Results arriving after invocation cancellation are discarded. Handles are private
Go values, not persistent references or authorization tokens for external services.

Registry handles currently expose `Reader`; optional stat and write capabilities
are obtained explicitly from the provider adapter by authorized sync operations.
No model argument can upgrade a reader to a writer.

Entries contain relative paths, directory flags, sizes, modification times,
optional media types, resource IDs and revisions. Resource IDs are meaningful
only within the originating provider, connection and storage namespace. Equal
IDs or paths from two connections are not proof that they identify the same
file. Revisions are opaque; an absent revision is not an overwrite permission.
An unknown stream size is `-1`, so a declared size never replaces a byte limit.

## Nextcloud adapter

The adapter reuses the existing guarded WebDAV client. Nextcloud URL layout,
Basic authentication, file-ID validation and HTTP status handling stay in
`ncsync`; MCP retains presentation and project import. Listing no longer has a
second XML parser inside the MCP package. The existing sync client also uses the
same file-opening implementation.

The adapter accepts only direct children of the requested folder under the
authenticated user's root. It ignores foreign origins, neighboring user roots,
query-bearing references and nested descendants. Listed resource IDs are
validated Nextcloud numeric file IDs; other providers may use other formats.
Redirects remain disabled and `ncguard` checks credentialed requests. Login names
and WebDAV user IDs remain separate fields.

The tool listing response is bounded to 8 MiB before parsing and displays at
most 500 entries. Sync/search retain their 16 MiB response bound. Oversized
responses fail even when their prefix contains complete XML. File import keeps
its 2 GiB limit, deadline, partial-file cleanup and create-new local output policy.
Cancellation interrupts the download stream. Remote files are never modified by
this read capability.

Nextcloud synchronization and upload use the `Writer` capability. Collection
validation uses `Statter`. An empty previous revision means create-only; a concrete
revision means replace only if the provider still has that revision. A missing
returned revision never grants permission to replace an existing file. There is
no unconditional write or automatic retry in this capability. Nextcloud search,
scheduling, conflict-copy naming and directory creation remain provider-specific.
The existing write guard restricts writes to the configured transfer folder.

Adapters classify errors as disconnected, expired authentication, forbidden,
missing, revision/name conflict, unavailable, invalid request or unsupported
capability. Callers use `errors.Is`; wrapped provider causes remain available for
existing sync handling and diagnostics. Public error text excludes provider details.
Cancellation and deadlines preserve their standard context errors.

## OpenCloud and remote references

The optional [OpenCloud adapter](opencloud.md) uses authorization code with PKCE,
encrypted access/refresh tokens, Graph drive discovery and Spaces DAV paths.
It is selected independently from Nextcloud and remains disabled by default.
Listing/fetch and conditional uploads have fixture coverage. Real-provider token
exchange and DAV acceptance remain unverified. Opaque remote references across
service boundaries remain outside this internal file-source API.

Processing tools continue to consume local project files. A cloud file is
explicitly fetched into a project before transformation or transcription. Remote
writeback remains a separate operation; the new reader does not turn cloud
storage into a mounted filesystem.

## Development checks

From `manager/`:

```sh
go test -race -count=1 -timeout 120s ./internal/filesource ./internal/ncsync ./internal/ncguard ./internal/gateway/mcp
go vet ./internal/filesource ./internal/ncsync ./internal/gateway/mcp
```

These checks use local fixtures. They cover separate credentials and roots,
metadata, invalid paths, hostile listing references, redirect refusal, response
bounds, credential refresh, invocation expiry, conditional writes, existing MCP
output and sync conflict handling. They are
not live-provider acceptance or a deployment check.
