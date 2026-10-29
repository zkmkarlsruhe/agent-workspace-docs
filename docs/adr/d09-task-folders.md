# D9: One folder per task

Status: accepted.

## Context

People should be able to work on files without learning repository management
or container commands.

## Decision

Expose projects as task folders with input, result and working areas. Let a
short task description start the project. Keep Git and snapshot mechanics
behind the interface; expose files, chats, downloads and cleanup directly.

## Consequences

The instance defines folder names and helper instructions. Snapshots support
undo but do not replace backups. Moving a project to trash and deleting an
account are separate operations with different retention behavior.
