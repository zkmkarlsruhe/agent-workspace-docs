# Workload ownership and operator resource policy

The manager wraps its container runtime with a persistent allocation controller.
Existing application adapters retain their authorization, readiness probes, HTTP
leases and save/close protocols. The controller owns the shared engine boundary:
reservations, resource accounting, immutable container bindings and cleanup.
There is one manager process per database and engine namespace.

## Policy

Set `OC_WORKLOAD_PROFILES_FILE` in both manager and Docker proxy. Mount the same
operator-owned JSON file read-only into both containers. The
[example policy](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/deploy/example/workload-profiles.json) preserves previous limits.
Without the variable, compiled defaults apply. Unknown shapes, unknown fields,
invalid limits, unsupported schemas and files larger than 64 KiB fail startup.

Schema 1 allows resource overrides for `workspace`, `assistant`, `toolbox`, `office`
and `freecad`. Each supplied profile declares memory and reservation in MiB, CPU in
millicores, process count and shared memory in MiB. Omitted profiles retain defaults.
This resource file cannot add images, mounts, commands or network access.
[Managed container plugins](container-plugins.md) add workload types through trusted
integration runtime declarations; they cannot supply arbitrary Docker specifications.

The effective profiles and quota have a content digest. Every new container request
carries the profile ID and digest; the independent proxy checks both and validates
the actual limits. Existing image, mount, command, network and hardening checks
remain enforced. A configured proxy rejects unlabelled requests. A policy mismatch
fails new creates rather than silently using one side's limits. Restart manager and
proxy together after changing policy. Existing containers keep their original limits
until their normal shutdown; policy changes do not terminate dirty applications.

Quota covers all newly journaled profiles, including pending creation/removal:
16 allocations per account, 256 total and 32 GiB of configured memory per account
by default. Memory accounting sums limits, not current RSS or reservations.
The existing workspace concurrency cap still applies separately. Pre-migration
containers retain compatibility until their normal removal and are not retroactively
charged to the journal. Drain them before relying on quotas as a complete host cap.

## Allocation and recovery

SQLite migration 34 adds allocation records and account deletion barriers. Reserve
before contacting Docker. Record account incarnation, shape, specification digest,
resource charge and random allocation ID. Secrets and environment values are not
stored in the journal. Label the container with the allocation and account incarnation;
after creation, bind its immutable Docker ID. All subsequent managed start/exec/remove
calls use that ID, so a reused name cannot redirect an old operation.

States are `reserved`, `created`, `running` and `removing`. The last records the
cleanup obligation before sending a removal. A failed or ambiguous removal retains
ownership and quota. A lost create response can be recovered by observing the same
allocation, without issuing another create. Identical concurrent creates share one
allocation; a changed specification conflicts until the old workload is released.

Startup and each existing reaper tick reconcile the journal. After the two-minute
creation grace period, abandoned reservations are cleaned up. Cleanup retries do not
replay tool calls or restart application work. Missing immutable container IDs release
their records. Delayed containers without a current allocation cannot receive work
and are removed by immutable ID on the next pass. Engine errors retain obligations.
Existing adapters still decide when a live application is idle, ready or safe to close.

Account deletion drains adapters, installs a persistent reservation barrier, removes
remaining allocations, then purges files and deletes the account. A failed deletion
keeps the barrier across manager restarts; retry deletion to finish. The database
also prevents deleting an account with remaining allocation records. Recreating an
account creates a new incarnation and does not inherit its deletion barrier.

`GET /admin/workloads` on the existing operator listener returns the effective policy
digest, quota and allocation metadata, including pending states. It requires the
existing `OC_ADMIN_TOKEN` bearer credential and excludes runtime network callers.
It does not expose environment values or specification hashes. The endpoint is not
routed through the public portal.

## Boundaries still owned by adapters

Managed container plugins use the same controller and provide authenticated browser
routes on separate origins. They do not replace application-specific leases or
expose an arbitrary acquire API. FreeCAD still mounts the
account workspace; a narrower project mount requires its separate compatibility
migration. Office owns tabs, document identity and browser credentials. Neither
application's save or close protocol is replayed by the controller. Full external
extension lifecycle and provider-specific login migrations remain separate work.
