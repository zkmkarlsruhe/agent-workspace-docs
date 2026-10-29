# Build and connect an MCP server

> **Prototype for evaluation only. Not production software, no support, no guarantees. Do not make it reachable from the internet; run it only in an internal network. Use at your own risk.**

The first release supports **LiteLLM as the MCP broker**. The manager exposes tools
from its reviewed catalog using a shared manager key. It does not implement a direct
remote-server registry, per-user OAuth, or a resources/prompts relay. Service
credentials belong in LiteLLM's environment or secret store, never in project files,
catalog entries or manifests. A manifest describes a service; it does not launch it.

The complete opt-in overlay is [deploy/example/mcp-hello](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/deploy/example/mcp-hello).
It builds [examples/mcp-hello](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/examples/mcp-hello) locally, exposes streamable HTTP
on an internal Docker network, registers broker server `hello`, loads an operator
manifest and adds the optional catalog item. No private image registry is needed.
The service has no credentials, storage or outbound requests. Its source URL is
illustrative; replace it with a real document when adapting the example.

## Options and defaults

| Option | Default and off switch |
|---|---|
| `OC_INTEGRATIONS_DIR` | Empty: embedded manifests only. When set, load every immediate `*.json` file at startup, including disabled manifests. No recursion or hot reload. |
| `OC_CATALOG_DIR` | Empty disables the catalog. The reference stack mounts `/srv/opencode/base/catalog`, initially empty. |
| `integrations.hello` | Omitted/false: off. Set true only after installing the manifest and catalog. |
| `catalog` in instance YAML | Empty. House-specific catalog entries live here. A catalog document's `include_instance: true` adds them; omitted/false leaves them out. |
| Assistant `enabled` | The minimal `support` assistant stays false. Enable only for the separate knowledge-source variant below. |

The directory uses the same strict schema validator as embedded manifests. Unknown
fields, duplicate JSON keys, invalid values and name collisions with embedded or
other operator manifests refuse startup, with the filename in the error. A missing
or unreadable configured directory also refuses startup. Restart to apply changes.
The renderer reads the same `OC_INTEGRATIONS_DIR`; pass it when rendering.

A catalog directory may contain `mcp.json` and an additive `catalog.json` overlay.
Both use `{"items": [...]}`. Duplicate IDs are errors, not overrides. A central item
uses `kind: mcp-central`, `tier: optional`, `litellm: [hello]` and native tool names
in `tools: [hello]`. Its ID must match the enabled remote integration. A builtin
item may omit `server` to use the selected instance's `mcp_server`.

## Deploy the ordinary helper example

Start from the working [reference installation](INSTALL.md). Run the following as
the operator on that VM, from `deploy/example`. The base Compose file must be the
first `-f` argument; overlay paths resolve relative to it.

```sh
install -d -m 0755 /srv/opencode/mcp-hello /srv/opencode/base/catalog
cp ../../instance/minimal/instance.yaml /srv/opencode/mcp-hello/instance.yaml
cp mcp-hello/catalog.json /srv/opencode/base/catalog/catalog.json
cat litellm.yaml mcp-hello/litellm.yaml > /srv/opencode/mcp-hello/litellm.yaml
```

Merge these changes into the copied instance (the shipped minimal stays off):

```diff
 integrations:
+  hello: true
```

Inside `artifacts.opencode.jsonc`, add this policy **after** the `mcp:*` deny
policy, keeping the surrounding YAML block indentation:

```diff
           "resource": "mcp:*",
           "effect": "deny"
         },
+    [[if:hello]]
+        { "action": "integration.use", "resource": "mcp:hello", "effect": "allow" },
+    [[end]]
```

The supplied [instance fragment](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/deploy/example/mcp-hello/instance.yaml) records
both edits. Do not replace the complete instance with that fragment. Render with
the same manifests mounted in the manager:

```sh
docker run --rm --network none --userns host --user 0:0 \
  --entrypoint /render-instance \
  -e OC_INTEGRATIONS_DIR=/integrations \
  -v /srv/opencode/mcp-hello/instance.yaml:/instance/instance.yaml:ro \
  -v "$PWD/mcp-hello/integrations:/integrations:ro" \
  -v /srv/opencode/base/etc-opencode:/rendered \
  workspace-manager:local -instance /instance/instance.yaml -out /rendered
chmod -R a+rX /srv/opencode/base/etc-opencode /srv/opencode/base/catalog

docker compose -f compose.yaml -f mcp-hello/compose.yaml config --quiet
docker compose -f compose.yaml -f mcp-hello/compose.yaml up -d --build hello litellm manager
```

Use your configured manager image instead of `workspace-manager:local` if different.
The host catalog directory reaches both manager and dynamic runtimes through the
existing mounts. The hello port is not published; only LiteLLM joins its internal
network. Restart existing workspaces to read the rendered policy. In **Capabilities**,
switch on **Example knowledge**. If project capabilities are enabled, also grant
`hello` to the project; the minimal instance uses personal opt-ins.

The reference stack uses `LITELLM_MASTER_KEY` as the manager key. For a deployment
using virtual keys, grant the manager key `object_permission.mcp_servers: [hello]`;
team/end-user restrictions must permit it too. Keep `allow_all_keys: false`.
[LiteLLM permission reference](https://docs.litellm.ai/docs/mcp_control)

The fragment pins `server_id: hello` and `transport: http`. Preserve the broker's
`hello-<tool>` naming convention. The manager sends `x-mcp-servers: hello`, requests
protocol `2025-06-18`, and exposes the native name `hello`. For a credentialed
replacement service, configure `auth_type: bearer_token` and
`auth_value: os.environ/HELLO_TOKEN` in LiteLLM and supply that environment secret
only to LiteLLM. [LiteLLM configuration reference](https://docs.litellm.ai/docs/mcp_config_reference)

To disable access, set `integrations.hello: false`, render and restart the manager
and workspaces. Keep the manifest while the instance still references `hello`.
To remove the overlay completely, restore the minimal instance and rendered files,
remove the hello catalog file, and start the base Compose stack without the overlay.
Stop the `hello` service explicitly before removing its Compose definition.

## Manifest schema 1

Fields come from `integration.Manifest`; all except the first row are optional.

| Fields | Meaning/checks |
|---|---|
| `schema`, `name`, `version`, `runs` | `1`; lowercase hyphenated ID, at most 40 characters; semantic version; `none`, `builtin` or `service`. |
| `kind`, `enabled_by_default`, `tools` | `builtin` or `remote`; default false; unique lowercase underscore tool names (integration-prefixed name at most 64 characters). Omitted kind follows `runs` (`builtin` means manager tools, otherwise remote). Explicit builtin kind requires builtin runs. |
| `mcp`, `image` | Service path such as `/mcp`, or `{url, auth_secret}` with an HTTP(S) URL and uppercase secret reference; optional service image pinned by SHA-256. Descriptive contracts only: the broker still owns connections and credentials. |
| `requires_core`, `requires_opencode`, `requires`, `conflicts` | Version constraints and integration IDs, checked during resolution. Dependencies must be explicitly enabled. |
| `scopes`, `integration_grants` | Manifest scopes need explicit instance `integration_grants` (the latter is not a manifest field). Known scopes: `transcripts:read`, `llm.background`, `llm.user`, `workspace:read`, `workspace:write`, `users:read`, `notify`. Hello needs none. |
| `skills`, `prompt`, `portal`, `settings`, `person_settings` | Relative content paths; portal entries `{path, roles}`; settings schema objects. These declarations do not install routes or service APIs. |
| `events`, `event_consumer`, `consent`, `holds_personal_data`, `deletion_contract` | Validated event names/consumer ID; consent `{required, version, text, text_en}` with relative paths. Non-builtin personal-data holders require deletion contract `v1`; declaration alone does not implement deletion. |
| `health`, `limits`, `owner` | `optional`/`critical`; nonnegative `{timeout_s, concurrency, llm_eur_month}`; `{name, contact}`. These service contracts do not configure broker timeouts or launch supervision. |

The [hello manifest](https://github.com/zkmkarlsruhe/agent-workspace/blob/main/deploy/example/mcp-hello/integrations/hello.json) sets
`kind: remote`, `runs: service`, `enabled_by_default: false`, `mcp: /mcp`, and
`tools: [hello]`. No manager rebuild is needed to add another manifest.

## Assistant knowledge-source variant

Use the same service, broker registration, manifest, catalog and runtime policy.
Add this top-level instance block:

```yaml
knowledge_sources:
  greeting:
    mcp_server: hello/hello
    read_only: true
    instruction: Use this service for the example greeting and cite its returned source URL.
    tools: [hello]
```

In the minimal instance's existing `support` assistant, set `enabled: true`,
`version: 3`, `consent_mode: support`, and `knowledge_sources: [greeting]`. Replace
both prompt statements saying no source is configured with instructions to read
`greeting` and cite its returned URL. Keep `builtin_tools: [question]`, empty skills
and MCP-tool lists, and the no-system-changes/no-messages rules. Render, restart,
accept the support notice and create a **new** assistant project. Existing projects
pin their definition; revisions require a new pin.

Assistant grants are independent of personal catalog opt-ins. Startup checks source
references. Each call checks project/session binding, current consent, integration
selection, source allowlists and upstream annotations. Explicit write annotations
remain denied. Disabling the integration revokes access even for existing pins.

## Verification

```sh
(cd manager && go vet ./... && go test -count=1 ./...)
(cd examples/mcp-hello && go test ./...)
python3 -I -B -m unittest discover -s tests/export
```

`TestManifestDirectory` covers valid/invalid manifests and collisions.
`TestDirectoryManifestInstance` covers selection, rendering and the off switch.
`TestHelloCatalogOverlay` covers catalog resolution and duplicate IDs.
`TestHelloBrokerOverlay` uses the hello in-memory protocol pattern behind a broker
fixture: discovery, native call, unlisted/prefixed-name denial before upstream access,
read-only annotation enforcement and revocation. `TestHello` tests the example
service directly. Export tests require the complete overlay and no private registry.

These tests do not run a real LiteLLM container. On the deployed stack, verify that
MCP discovery lists only `hello`, call it and check the returned source URL, attempt
`unlisted` and confirm denial, then disable the integration and confirm revocation.
For the assistant variant, repeat with a new consented project and after revocation.
