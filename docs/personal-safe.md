# Personal safe

The personal safe stores names, account labels, target labels and secret values
as one encrypted database blob. It uses a separate password, Argon2id and
AES-256-GCM. Normal sign-in never unlocks it. Supported private-read tools require separate, explicit approval for each
operation; target labels do not authorize network destinations.

Unlocking lasts 60 minutes, without sliding renewal. Explicit locking, portal
sign-out, account disconnection and service restart invalidate the unlock.
Logging out directly at the identity provider does not notify the safe; its
existing unlock still expires after 60 minutes. Separately unlocked portal and
chat sessions keep their own deadlines; unlocking one does not revoke or extend
the others. Up to eight active unlocks are allowed per account. Further unlocks
are refused until a lease expires or the person locks the safe; existing unlocks
remain valid. Locking, deleting the safe, changing its password or changing the
account identity revokes every lease and cancels their running operations. Keys
remain in service memory, not in browser storage,
runtime containers or the database. Memory clearing is best effort; this is not
a guarantee of forensic erasure from process memory or browser-rendered text.

The OpenCode overlay shares the chat application's trust boundary. A script
execution vulnerability there could capture the password during entry. Browser
cookies are opaque references with Secure, HttpOnly and SameSite=Strict; they
are never forwarded to the runtime. Password fields start masked and have a Show/Hide toggle. Opening a stored
secret loads a closed disclosure; showing it requires a separate click. Switching
tabs or leaving the page hides visible values again. Displaying a secret in the
portal makes that value available to the person and browser; later locking
cannot recall a displayed or copied value.

Only the owning account can manage the safe. Forms use the account incarnation
and ciphertext fingerprint to reject stale writes, including deletion followed
by recreation. Administrative identity rebinding preserves the ciphertext but
invalidates old authorization stamps. Account deletion removes the encrypted
row. Independent backups and downloads remain.

The ordinary account export excludes the safe. Use the separate encrypted JSON
backup. Import requires its password and an empty safe; it installs fresh
cryptographic binding for the receiving account. Password changes do not change
older backups. A forgotten password cannot be recovered by signing in.

For operator setup and supported SMB/IMAP operations, see
[private readers](private-readers.md).

Limits: 100 secrets, 8 KiB per value, 128 KiB plaintext total, 200 KiB encrypted
backup. Passwords require at least 12 characters. Unlock derivation is limited
to five attempts per minute per account and two concurrent operations globally.


Read requests open directly from their notification in a single nonmodal popover.
If locked, enter the safe password there; entry selection and approval stay in
that view. An already unlocked safe skips the password step. When there is only
one entry it is visibly selected; several entries require a choice. Unlocking
alone never approves a read. Success closes the popover and restores chat focus;
errors leave it open for correction.
