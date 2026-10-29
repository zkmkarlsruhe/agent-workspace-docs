# Connect LiteLLM

> **Prototype for evaluation only. Not production software, no support, no guarantees. Do not make it reachable from the internet; run it only in an internal network. Use at your own risk.**

This is the default broker path. A [direct OpenAI-compatible endpoint](connect-provider.md)
is also supported with separate model/MCP upstreams and no provider attribution.

The request path is runtime, manager LLM gateway, LiteLLM, model provider.
The manager's gateway listens on port 4000 inside each runtime's private network.
The runtime uses `http://llm-gw:4000/v1`; it never receives provider credentials.

1. Configure the upstream endpoint and provider key only in LiteLLM. The supplied
   `deploy/example/litellm.yaml` reads `MODEL_ID`, `MODEL_API_BASE` and `MODEL_API_KEY`
   from its environment. Use a model supporting streaming and tool calls.
2. Expose stable LiteLLM aliases, initially `default` and `small`. Map these in
   `instance/minimal/instance.yaml` under `models`; `thorough` can reuse `default`.
   These are gateway aliases, not UI model names or provider secrets.
3. Set manager `LITELLM_BASE_URL` to the internally reachable LiteLLM base URL
   (`http://litellm:4000` in Compose, without `/v1`). Set manager `LITELLM_API_KEY`
   to a LiteLLM key authorized for those aliases. Compose uses `LITELLM_MASTER_KEY`
   for the reference trial; use a restricted virtual key when extending it.
4. Match context limits, output limits and image-input capabilities in the instance's
   OpenCode artifact to the upstream model. Render the instance again and restart.
5. Run the two-alias request check in [INSTALL.md](INSTALL.md), then complete the
   browser chat/file/download check. A model-list response alone is insufficient.

Keys stay central: provider keys in LiteLLM, the LiteLLM credential in the manager.
Do not put keys in the instance, runtime config, catalog, assistant prompt or project.
The manager supplies authentication and `x-litellm-end-user-id`, meters requests
and applies its estimated daily cap. That cap is not a provider billing guarantee.

Keep LiteLLM and the manager gateway on internal service networks. Inspect gateway
logs without exposing keys or chat content. Model aliases can change upstreams
centrally without copying credentials into user environments.

The manager does no chat failover. Fallback chains belong to LiteLLM and must be
configured there; the supplied example has no fallback chain. The manager's
image tool retries its configured image-model list separately.

## Accounting contract

Upstream prices are not assumed to be euros. Set `OC_UPSTREAM_COST_CURRENCY`
(or instance `accounting.upstream_cost_currency`) to `EUR`, `USD`, or `none`.
The shared/minimal default is `none`: ignore upstream amounts for charging and
use local estimates. `EUR` accepts the reported amount directly. `USD` requires
`OC_USD_PER_EUR` (or `accounting.usd_per_eur`), a finite positive number of USD
per EUR; manager divides the USD amount by this rate. The rate defaults to `0`
(unconfigured); no exchange-rate lookup runs. Environment settings override the
instance. The example Compose exposes both settings. Verify the upstream's unit
before enabling billing amounts. Set the unit back to `none` to disable them.

`x-litellm-response-cost` and `x-litellm-model-id` are LiteLLM-specific response
headers. Both are optional. `usage.cost` is a nonstandard body extension and
wins over a header cost only when valid. Raw and converted costs must be finite,
positive and at most 1000; rejected billing falls back to estimates. A missing
model ID leaves `DeploymentID` empty and does not fail the request.
`x-litellm-end-user-id`, `x-litellm-session-id`, `x-litellm-call-id`, and
`x-litellm-spend-logs-metadata` are LiteLLM-specific request attribution headers;
the direct `openai` flavor sends none of them and ignores both LiteLLM response headers. Local event/session attribution
remains authoritative.

Migration 27 adds `raw_cost`, `raw_cost_unit`, and `raw_cost_source` alongside
`cost_eur` and `cost_source` in `usage_events`. Finite raw values are retained even
when the unit is `none` or the amount is rejected. Invalid body cost does not
replace accepted header evidence. Non-finite or unparseable amounts cannot be
stored as numbers. Existing rows retain their values and have NULL raw fields.
`cost_source` is `header`/`usage` for EUR, `header-usd`/`usage-usd` after conversion,
`estimate` for local prices, or `unknown` when there is no defensible cost.
Raw fields describe upstream evidence, never an estimated amount.

Configure local prices under the instance's `accounting` block. These are
operator estimates in EUR, not assertions about an arbitrary provider's tariff:

| Option | Shared/minimal default | Disable |
|---|---|---|
| `prices.standard`, `prices.fast`, `prices.thorough` | each `{input: 0.60, output: 3.60}` EUR per million tokens | `prices: {}` disables all chat estimates and holds; an explicit zero role price estimates zero |
| `largest_context` | `262144` tokens | must stay positive; size for the largest allowed model |
| `max_output_tokens` | `32768` tokens | must stay positive; bounds forwarded and internal chat requests in both flavors |
| `embedding_eur_per_million` | `0` | `0` means unknown, no embedding estimate |
| `image_eur` | `0.10` per attempt | `0` disables the local charge |
| `mcp_eur` | `0.01` per central tool call | `0` disables the local charge |
| `toolbox_eur` | `0.02` per run | `0` disables the local charge |
| `search_eur` | `0.005` per uncached search | `0` disables the local charge |
| `fetch_eur` | `0.002` per uncached fetch | `0` disables the local charge |

Role prices resolve through `models.default` (standard), `models.small` (fast),
and `models.thorough`. An omitted role uses the highest configured input and
output prices, still marked `estimate`. An omitted entire price map uses the
listed defaults; an explicit empty map disables it. Shared aliases use the
highest applicable prices. Unknown aliases use the highest configured prices.
`OC_SEARCH_CHARGE_EUR` and `OC_FETCH_CHARGE_EUR` still override their instance
values. Optional tool integrations can also be disabled separately.

The chat hold is `(largest_context * highest input price + max_output_tokens *
highest output price) / 1e6`, rounded up to the next EUR 0.10. Minimal's default
is EUR 0.30. Upstream currency remains an independent, explicit choice.
An instance with `upstream_cost_currency: EUR` already selects euro billing;
no duplicate GitOps environment override is needed.
Keep these limits at least as large as every allowed model's runtime limits.
With partial chat usage, each absent counter uses its configured limit; with
no usage, the full hold becomes the estimate. A request sent upstream without a
response also uses the hold; a request that never reached the connection does
not. An embedding estimate requires input tokens and a nonzero embedding price;
otherwise its cost source is explicitly `unknown`. Zero flat charges disable
only the local estimate, not valid upstream billing.

The daily cap controls local admissions, not provider invoices. Unknown costs,
provider-side retries, caching, model changes, and actual tariffs can differ.
Configure prices and limits before relying on local budget reports.

CO2 remains an alias-level estimate using optional instance `footprint` metadata.
Missing metadata stays unknown; unrelated aliases never inherit the primary
alias's coefficients. Shared aliases with conflicting or incomplete role metadata
also stay unknown. Use `footprint: {}` to disable all footprint estimates.
Actual fallback deployment identification remains outside this estimate; the
optional LiteLLM deployment ID is retained for reconciliation.
