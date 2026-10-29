# D60: Run heavy tools in networkless containers

Status: accepted for optional toolboxes.

## Context

Occasional media or conversion tools need substantial packages that do not
belong in every person's base runtime image.

## Decision

Start a separate toolbox on demand from an explicitly allowed image pinned
by digest. Mount only the person's workspace, disable networking, and apply
a read-only root filesystem, temporary storage, UID 1000, dropped
capabilities, no-new-privileges and resource limits. Bound command duration
and returned output.

## Consequences

Tools can process local files without acquiring network access. A toolbox can
still modify or delete files in the mounted workspace. It follows the main
environment's lifecycle and account cleanup. The reference implementation is
Docker-based; a possible orchestration-platform mapping is not a shipped
deployment.
