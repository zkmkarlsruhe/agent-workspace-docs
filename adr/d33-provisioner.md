# D33: Separate privileged filesystem provisioning

Status: accepted for the helper boundary. UID mapping follows D44.

## Context

Creating host directories, assigning ownership and managing filesystem quotas
needs privileges that ordinary portal and runtime requests should not carry.

## Decision

Use a narrow privileged provisioner for personal storage setup, quota
assignment and purge. Perform ordinary project reads and writes through the
person's runtime API. Keep the manager inside its user namespace.

## Consequences

The manager does not need unrestricted host filesystem access for each file
operation. The helper must validate every request. Provisioner availability
and working quotas are prerequisites for normal provisioning and account
deletion. This boundary does not prevent a privileged operator, or a manager
with runtime access, from accessing personal data.
