# D44: Docker with user namespace remapping

Status: accepted. Replaces the earlier rootless Podman runtime choice.

## Context

The earlier per-person UID-range approach required expensive image copying
and ownership changes. Runtime startup and storage overhead made that
approach unsuitable for the prototype.

## Decision

Use Docker with `userns-remap`, sharing one remapped UID range. Run personal
containers unprivileged with a read-only root filesystem, dropped capabilities,
no-new-privileges, resource limits and separate networks. Route lifecycle
operations through a validating Docker proxy.

## Consequences

Images can be shared without per-person ownership conversion. The separation
is container and network isolation, not a unique host UID range per person.
All containers share the host kernel. The provisioner and Docker proxy remain
privileged components. The reference host mapping must match the provisioner's
ownership rules; arbitrary remapping is not supported by that example.
