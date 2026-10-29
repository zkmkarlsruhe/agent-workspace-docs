# D58: Restrict cloud-file writes to a transfer folder

Status: accepted for the optional Nextcloud integration.

## Context

An app password permits more operations than the workspace needs. A mistaken
write or deletion could affect unrelated documents or shared collections.

## Decision

Permit reads across files available to the connected person. Restrict writes
to the configured personal transfer folder. Never delete remote files. Use
conditional writes for files previously written by the manager, and preserve
conflicts as separate copies instead of overwriting an unknown version.

## Consequences

Every request using the app password passes the same method, host and
normalized-path guard. Shared collections are read-only sources. Calendars,
contacts, mail, sharing administration and other unrelated service APIs are
outside the allowed operations. Disconnecting or deleting the local account
revokes the credential but leaves remote files for the person to manage.
