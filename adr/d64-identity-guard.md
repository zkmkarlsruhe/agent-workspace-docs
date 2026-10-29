# D64: Guard username ownership with issuer and subject

Status: accepted and implemented.

## Context

Existing workspace data is keyed by username and internal UID. Reassigning a
username must not silently give another identity access to that data. An
automatic migration to a new identity key would risk merging accounts.

## Decision

Keep the unique, case-sensitive username as the account key and preserve its
internal UID and data. Bind it to the stable subject received through a
trusted header and to one configured instance issuer. The issuer is not
derived from request metadata. Bind new accounts when consent permits account
creation and legacy accounts on their next request.

Reject subject mismatches and block the username until an administrator
verifies ownership and explicitly rebinds it. Audit the actor, time and old
and new subject hashes. Refuse startup when configured and stored issuer
namespaces disagree; changing configuration alone cannot migrate identities.
Detect duplicate legacy usernames before applying the identity migration.

## Consequences

The IdP must never reuse usernames. Reuse before a legacy account's first
binding is not detectable. A renamed username is a separate account, while
rebinding transfers access to all existing account data. The administrator
must verify ownership with the IdP operator before using that action.

New requests and handshakes are checked; already-open runtime streams are not
disconnected by this guard. This is the current username guard, not a completed
migration to issuer/subject as the primary account key. Preserve the issuer
across upgrades and restores, and plan identity migrations explicitly.
