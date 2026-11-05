# Browser-approved Nextcloud share links

`nextcloud_share_create` creates a public link for an existing file or folder in
the connected person's Nextcloud. Both the Nextcloud and browser integrations
must be enabled. Supply only `path`, relative to the Nextcloud file root; this is
not a local project path or a URL. Upload a newly created document first if needed.

The browser displays the exact server, path and originating project/session. The
person chooses the kind of link:

- **Read and download** for a file or folder.
- **Edit** for a file; for a folder this also permits upload and deletion.
- **Upload only** for a folder: recipients can deposit files without reading its contents.

A link password and expiry date are optional browser inputs. Empty expiry leaves
Nextcloud's defaults in force; server password and expiry policies still apply.
Passwords are masked with an explicit visibility toggle. A password must be
communicated separately if recipients need it.

Clicking **Create share link** consumes one browser claim and creates the link.
The popover closes and reports the result by toast. It uses the existing encrypted
Nextcloud connection, so no additional safe unlock is required. Cancelling does
not create a share. Opening or renewing the dialog does not grant permission.

The tool waits and receives **only the share URL**. Browser choices, passwords,
credentials, share IDs and server response metadata are not returned to the tool.
Choices remain in browser memory until completion, dismissal or account change;
no browser storage is used. The returned URL is an access capability and becomes
part of the chat. Anyone with the URL and, when set, its password can use the
selected permissions. No email is sent by this tool.

Requests are tied to the owner, current runtime generation, personal root session,
project and browser tab claim. Other accounts, isolated assistant sessions and
replayed approvals cannot use them. Before creation, the manager rechecks the
connection and file identity. Source or connection changes invalidate the request.
The share remains a live reference to the Nextcloud item, not a frozen file copy.

The credential guard allows only the exact public-share POST constructed by the
approved path. It does not open general sharing administration. Returned URLs must
belong to the configured Nextcloud, and returned file identity and access must
match the request. Response bodies from sharing calls are never logged.

A timeout or connection loss can leave a share created without a confirmed result.
Never retry automatically; check Nextcloud before requesting another link.
Existing shares can be managed or revoked in Nextcloud. Account disconnect does
not revoke existing public links.

Protocol contract: [Nextcloud OCS Share API](https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/ocs-share-api.html).
Unit and browser tests cover authority, redaction, choices and uncertain outcomes.
An opt-in local fixture covers actual read/edit file shares and read/edit/upload-only
folder shares, including password and expiry persistence, on a disposable Nextcloud.
