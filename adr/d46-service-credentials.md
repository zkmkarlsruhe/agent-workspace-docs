# D46: Store connected-service credentials in the manager

Status: accepted for supported personal service connections.

## Context

An app password may grant access to an entire external account, beyond the
operations the workspace should expose.

## Decision

Use the service's connection flow and store the resulting credential encrypted
in the manager database. Keep it out of runtimes and data exports. Allow
reconnection and disconnection; revoke credentials during account deletion.

## Consequences

The manager is the enforcement point for the narrower tool policy. Encryption
protects database contents only while the master key is separate; the operator
can decrypt them. Revocation failures must be surfaced and can block current
account deletion. This does not create a general secret vault for user scripts.
