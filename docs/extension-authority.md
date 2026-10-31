# Extension authority and lifecycle

The operator selects installed manifests in the instance definition. New database
policies start with its explicit `integration_grants`; existing policies survive
restart unchanged. A manifest requests authority and never grants it to itself.
The effective scope is restricted by the manifest, database grants, current account,
base notice, integration notice, project capability and invocation where applicable.

## Operator and user controls

`/extensions` shows the selected integrations. Members of the configured admin group
can enable or disable integrations and change their declared grants. Other users
can accept or withdraw only their own integration notices. Required notices are
loaded from `<OC_INTEGRATIONS_DIR>/<name>/<consent.text>` and its English counterpart.
Changing notice text requires increasing its integer version. The base notice uses
its existing string hash; it does not replace required integration consent.

The existing authenticated operator listener also provides:

| Method and path | Purpose |
|---|---|
| `GET /admin/extensions` | Selected manifests and current policies |
| `PUT /admin/extensions/{name}` | Full policy object: `name`, `enabled`, `scopes` |
| `POST /admin/extensions/{name}/tokens` | Issue a service token; `days` is 1–365 |
| `DELETE /admin/extensions/{name}/tokens` | Revoke all tokens for that integration |
| `GET /admin/extensions/deletions` | Pending core cleanup and external obligations |
| `POST /admin/extensions/deletions/{operation}/{name}` | Record operator resolution with `evidence` |

Token plaintext is returned once. Only its hash is stored. Keep issued tokens in
the service's secret store; never put them in manifests, browser URLs or user
runtimes. Operator policy changes record the actor and previous/new policy.

## Service events

These routes are on the private manager gateway and require the integration's
service token in `Authorization: Bearer ...`:

| Method and path | Purpose |
|---|---|
| `GET /api/v1alpha/extensions/events?after=<cursor>` | Ordered event references and next cursor |
| `GET /api/v1alpha/extensions/events/resync` | Create a bounded snapshot and capture its cursor |
| `GET /api/v1alpha/extensions/events/resync?snapshot=<token>&page=<offset>` | Continue that snapshot |
| `GET /api/v1alpha/extensions/deletions` | This integration's outstanding obligations |
| `POST /api/v1alpha/extensions/deletions/{operation}/ack` | Acknowledge completed deletion (empty body) |

Event IDs remain stable across redelivery. Consumers persist their cursor and make
their own processing idempotent. Delivery rechecks current authorization; event
payloads contain identifiers rather than transcript bodies. Subscriptions and
appropriate grants are required. Chat references additionally recheck current chat
visibility. A withdrawal exception applies only to previously authorized observers
of that account incarnation. Deletion events use the durable holder registry.

Expired cursors return HTTP 410. Take a snapshot, consume its pages, then continue
from its captured cursor. Snapshots expire after ten minutes, with two per service
and eight globally. Every page rechecks authorization. Retention advances only over
a contiguous expired event prefix, using a thirty-day cutoff.

## Account deletion

A durable operation fences the current account incarnation before cleanup. Existing
runtime access is revoked before external provider revocation, which can fail.
Core cleanup is retried against that same operation and incarnation; it cannot
remove a newly created account with the same identity. Required external deletion
acknowledgements survive core account removal and integration disablement.

Consumers acknowledge only after their held data is deleted. An unavailable service
leaves a visible obligation. Operators can resolve an obligation with evidence;
there is no automatic success acknowledgement. Cleanup failures retain allocations
and quota until removal succeeds. Local observer records and cached snapshots for
the deleted account are removed.

These endpoints are experimental. They do not announce the stable `/api/v1`
transcript, background-model, notification or arbitrary workload-acquire contracts.
