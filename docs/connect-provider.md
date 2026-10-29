# Connect a model provider

The manager supports two paths: the supplied LiteLLM broker (default), or a
direct OpenAI-compatible model endpoint. Both use the same local identity,
consent, budget admission and usage recording. Provider credentials stay in the
manager or broker; runtimes use `http://llm-gw:4000/v1` without provider keys.

## Options and defaults

| Manager option | Default | Meaning |
|---|---|---|
| `OC_LLM_UPSTREAM_URL` | `LITELLM_BASE_URL`, including the instance default | Model API root base, without trailing `/v1`; required |
| `OC_LLM_UPSTREAM_KEY` | `LITELLM_API_KEY` | Model API bearer key |
| `OC_LLM_UPSTREAM_KEYLESS` | `false` | Allow an empty model key; an empty key sends no `Authorization` header |
| `OC_LLM_UPSTREAM_FLAVOR` | `litellm` | `litellm` or `openai`; selects request attribution and response-cost headers |
| `OC_MCP_UPSTREAM_URL` | `LITELLM_BASE_URL`, including the instance default | Independent central MCP broker root base; empty disables the integration; `-` explicitly disables it despite a legacy default |
| `OC_MCP_UPSTREAM_KEY` | `LITELLM_API_KEY` | Independent MCP bearer key; empty sends no `Authorization` header |

Nonempty new options take precedence over their legacy aliases. Empty environment
values fall back to instance/default values. Keys are environment-only secrets.
An instance no longer needs a `defaults.LITELLM_BASE_URL` when the model URL is
supplied through the environment. Existing LiteLLM environment settings continue
to configure both upstreams unchanged.

Both upstream URLs must be absolute HTTP(S) URLs without URL credentials, query
or fragment. They follow the **root-base convention**: the manager appends
`/v1/...` for models and `/mcp/` for central tools. A path prefix is allowed:
`https://models.example.org/api` becomes `/api/v1/chat/completions`. A base ending
in `/v1` or `/v1/` is rejected at startup with instructions to remove that suffix.
The runtime's own base still ends in `/v1`.

## Direct endpoint recipe

Start from `instance/minimal/instance.yaml`. Replace the manager's two legacy
LiteLLM environment entries with this block (also shown in the example Compose):

```yaml
OC_LLM_UPSTREAM_URL: https://models.example.org
OC_LLM_UPSTREAM_KEY: ${MODEL_API_KEY:?set MODEL_API_KEY}
OC_LLM_UPSTREAM_FLAVOR: openai
OC_LLM_UPSTREAM_KEYLESS: "false"
OC_MCP_UPSTREAM_URL: "-"
OC_UPSTREAM_COST_CURRENCY: none
```

Use a hostname reachable from the manager's container network. For a keyless
local server, omit `OC_LLM_UPSTREAM_KEY` and `LITELLM_API_KEY`, set
`OC_LLM_UPSTREAM_KEYLESS: "true"`, and use its reachable HTTP(S) root URL.
Keyless mode permits an empty key; it does not suppress a configured key.

For central tools behind a separate LiteLLM MCP broker, replace `-` with that
broker's root URL and set `OC_MCP_UPSTREAM_KEY`. This keeps the existing `/mcp/`,
server-selection and tool-prefix contract. It does not make an arbitrary MCP
server a drop-in broker. The unused LiteLLM service may be omitted when central MCP is disabled.
Without an MCP upstream, startup logs
`central MCP integration disabled: no upstream configured`; central endpoints
return HTTP 503 when an authorized operation needs the upstream. Independently configured builtin tools remain available.

Map the provider's exact raw model IDs to the three roles in your instance:

```yaml
models:
  default: provider-chat-model
  small: provider-fast-model
  thorough: provider-reasoning-model
```

Replace these example IDs with IDs your endpoint accepts. All roles may use one
model. Do not add LiteLLM's `openai/` routing prefix unless that is literally part
of your direct provider's model ID. The runtime IDs `litellm/standard`,
`litellm/fast`, and `litellm/thorough` remain **internal labels**, including when
no LiteLLM process runs. They map respectively to `models.default`, `models.small`
and `models.thorough`. The small role also serves naming, profile assistance and
evaluation; it must accept the same chat API and internal `max_tokens` field.

In the instance's `artifacts.opencode.jsonc`, set each role's `limit.context`,
`limit.output`, `capabilities.tools` and `capabilities.input` to the provider's
actual supported values. For a text-only model, use `"input": ["text"]`. Sample
context lengths and image capabilities are examples, not discovered capabilities.
Choose models supporting streaming and tools for workspace tasks. Match
`accounting.largest_context`, `accounting.max_output_tokens` and per-role prices
to these models; chat output token limits are enforced in both flavors.
Do not copy footprint coefficients from unrelated models.

Render the instance and restart the manager and runtimes as described in
[INSTALL.md](INSTALL.md). The static runtime metadata does not refresh from
`/v1/models`. Restarting the manager alone does not update running runtimes.

## Supported endpoint subset

| Caller | Method and upstream path | Contract |
|---|---|---|
| Runtime | `POST /v1/chat/completions` | JSON or SSE chat, including tool definitions, tool calls and tool results |
| Runtime | `GET /v1/models` | Forwarded discovery; no usage charge or metadata synchronization |
| Runtime | `POST /v1/embeddings` | OpenAI-shaped embedding request/response; local cost needs usage and configured pricing or a declared cost extension |
| Manager | `POST /v1/chat/completions` | Nonstreaming small-role calls and optional vision with a data-URL image |
| Manager image tool | `POST /v1/images/generations` | Only when `OC_IMAGE_MODELS` is configured; JSON, `n: 1`, `response_format: b64_json`, requested size |
| Manager image tool | `POST /v1/images/edits` | Only when `OC_IMAGE_EDIT_MODEL` is configured; multipart with PNG `image` and the same image fields |

Runtime `/v1/images/*` routes are not exposed. Image responses must contain
`data[].b64_json`; URL-only results are rejected. Image generation uses the
configured sizes `1024x1024`, `1536x1024` or `1024x1536`. Leave image tools off
for providers without this contract (`OC_IMAGE_MODELS=-`, no edit model; minimal
has neither configured). Vision is separately enabled by `OC_VISION_MODEL`;
`-` disables it. Responses, audio, rerank, batch, fine-tuning and other APIs are
not forwarded. `/router/settings`, `/v1/model/info` and SpendLogs are not polled.

The manager performs **no chat failover**. Chat fallback chains are a LiteLLM
feature and require upstream configuration; the supplied example has no chain.
The manager's image tool separately tries its configured model list in order and
records every attempt. This does not provide chat fallback.

## Request and response handling

Both flavors remove client `user`, `metadata`, `litellm_metadata`,
`litellm_session_id`, `litellm_trace_id`, `tags`, `fallbacks`,
`context_window_fallbacks`, `num_retries`, `timeout`, `mock_response`,
`mock_tool_calls`, `mock_testing_fallbacks`, `caching`, `cache`, `guardrails`,
`spend_logs_metadata`, `api_base`, `base_url`, `api_key` and `api_version`.
Both remove chat `n` (provider default: one choice) and force
`stream_options.include_usage=true` when `stream=true`.

In both flavors, the gateway inserts/bounds `max_tokens` and bounds an existing
`max_completion_tokens` using `accounting.max_output_tokens`. Both are standard
OpenAI fields. No token-field translation occurs. Other caller fields pass through; this is not a complete
schema validator. The gateway adds no nonstandard body fields. Internal
nonstreaming calls build `model`, `messages`, `max_tokens` and optional `tools`;
their token count stays bounded by `accounting.max_output_tokens`. Providers that
reject `max_tokens` for these models are not supported by this internal path.

With `litellm`, the manager sends `x-litellm-end-user-id` (username),
`x-litellm-session-id`, `x-litellm-call-id` and, when available,
`x-litellm-spend-logs-metadata`. With `openai`, it sends none of these and does not
send its local request ID or replace the stripped `user` field. Manager-owned
usernames, user IDs and session IDs are not added to provider requests; local
ownership and usage recording remain intact. User-supplied prompt content is
still transmitted. The optional MCP broker keeps its separate attribution
contract, regardless of the model flavor.

For `openai`, `x-litellm-model-id` and `x-litellm-response-cost` are ignored,
including on internal chat and image calls. Only a valid `usage.cost` extension
with declared `EUR` or `USD` currency can become reported billing; otherwise
configured local estimates apply, or cost is unknown. Default currency in the
minimal instance is `none`. See the [accounting contract](connect-litellm.md#accounting-contract)
for rates, raw cost evidence, estimates and daily-cap limits.

For both flavors, responses forwarded to runtimes retain only `Content-Type`,
`Content-Length`, `Cache-Control`, `Retry-After`, `X-Request-Id`, `Request-Id` and
`OpenAI-Request-Id`. All other upstream headers and trailers are removed,
including debug/API-base headers. LiteLLM billing headers are read locally before
removal. Response bodies and SSE chunks pass through unchanged.

## Verification

The direct contract is tested against an in-memory HTTP provider using the real
proxy and logging transport. From `manager/`, run:

```sh
go test -count=1 ./internal/config -run '^TestUpstream'
go test -count=1 ./internal/gateway/llm -run '^Test(Provider|OpenAI)'
go test -count=1 ./internal/gateway/central -run '^TestDisabledWithoutUpstream$'
```

`TestProviderSanitizerAndStreaming` checks forwarded spec fields, streaming tool
calls, usage and local ownership for both flavors.
`TestProviderHeadersAndInternalCalls` checks small-role naming, internal tools,
image generation/editing and bearer/keyless behavior.
`TestProviderResponseHeaderAllowlist` checks chat, embeddings and unmetered models.
`TestOpenAIUsageCostCurrency` checks declared and unknown currencies.
These are contract tests, not a live-provider certification.

For deployment acceptance, complete the browser chat/file/download check in
[INSTALL.md](INSTALL.md) with your endpoint. Check naming, streaming, an actual
tool-created file, usage counters and local ownership. Test all three role IDs;
exercise optional images/embeddings only if enabled. A successful model-list
request alone does not establish chat, tools, accounting or model limits.
