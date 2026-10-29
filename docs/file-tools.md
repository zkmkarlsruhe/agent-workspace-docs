# Image, vector and PDF tools

The optional `file-tools` integration processes individual project files. Each
operation saves new files and returns their paths for another operation to consume.
Originals remain unchanged. Word and spreadsheets are outside this integration.
Handwriting transcription uses a separately configured vision route.

| Tool | Input | Output |
|---|---|---|
| `background_remove` | Raster image | PNG with foreground alpha |
| `raster_to_vector` | Raster logo or illustration | SVG paths and PNG preview |
| `svg_create` | Complete SVG markup | Validated SVG and PNG preview |
| `svg_edit` | Source path, source SHA256, replacement markup | New SVG and PNG preview |
| `image_transform` | Image; crop, dimensions or format | PNG, JPEG or WebP |
| `pdf_to_text` | PDF; optional inclusive page range | UTF-8 text and page mapping |
| `handwriting_to_text` | Image or explicit PDF page | Literal UTF-8 transcript and review metadata |

The existing `images` integration supplies `image_generate`, `image_view` and the
new dedicated `image_edit`. Generation keeps its configured model provider.
Legacy `image_generate(source_image=...)` calls still work, but new calls should
use `image_edit`. Edit inputs retain resolution and transparency within the input
limits; the provider still determines output size. Animated edit inputs are rejected;
select a single frame before editing. Viewing images retains its smaller, flattened
representation for visual inspection and requires a source in the session's project.

## Processing contract

The manager resolves person and project from the session. Absolute source paths
must belong to that project. The file service receives bytes, never credentials,
workspace mounts or caller-selected URLs. Every local file operation checks the
integration and catalog grants, reads a bounded source, processes it, and saves new
results with SHA256 hashes. Metadata records the source, options, engine/version,
page mapping where applicable, and warnings.

`structuredContent` and its JSON text representation share this shape:

```json
{
  "schema_version": 1,
  "status": "complete",
  "outputs": [
    {"path": "/workspace/example/results/file.svg", "media_type": "image/svg+xml", "role": "result", "sha256": "..."}
  ],
  "metadata_path": "/workspace/example/results/file.metadata.json",
  "warnings": []
}
```

The exact result folder comes from the instance configuration. `partial` means
some content or companion file is missing; inspect warnings before chaining.
When saving a companion fails, already saved outputs remain listed. Publication
of SVG, preview and metadata is not a multi-file transaction.

`svg_create` and `svg_edit` validate markup authored by the caller. They do not
call another text model. The `media-tools` skill explains selection and visual
checks. SVG uses a static subset: paths, geometric shapes, text, groups, gradients
and local clipping. CSS, scripts, embedded images, external references, `use` and
animation are rejected. Rejected features are not silently deleted. Text remains
text and therefore depends on installed fonts; tracing lettering produces paths.

PDF extraction uses only an existing text layer. A page with no text is reported
as blank or potentially scanned; the tool cannot distinguish those cases without
OCR. No-text documents fail explicitly. Mixed documents return partial text and
page warnings. Text-layer presence does not prove correct reading order or accuracy.

## Handwriting transcription

`handwriting_to_text` is available only when file tools are enabled and
`OC_HANDWRITING_MODEL` selects an approved vision route on the existing gateway.
The operator configures that route; callers cannot change the model, endpoint,
prompt or provider. The gateway credential must permit the selected alias.
Empty or `-` disables it. The `images` integration is not required.

```json
{"path":"input/notes.pdf","options":{"page":2}}
```

Use the configured input-folder name. Images accept `path` alone. PDFs require
an explicit 1-based page number, one call per page; process the requested pages
in order. The metadata's `processing.preparation.document_pages` reports the
PDF's total page count. A result never silently represents other pages.

The offline worker renders PDFs at 192 DPI. Images retain their original pixels
with EXIF orientation applied and transparency flattened onto white. It does not
receive model credentials or make network requests. The manager sends the prepared
PNG through the existing metered gateway as the requesting person and session.
The fixed prompt requests literal text, preserving spelling, abbreviations,
names and numbers, and marking genuinely unreadable text as `[unlesbar]`.
It requests no summary, translation, spelling correction or drawing description.
Source text remains untrusted content, not executable instructions.

The result contains a new `.txt` and metadata file. Read both. Metadata records
the source hash, page, preparation, image hash, model, returned model, usage,
finish reason, prompt and `review_status: unreviewed`. `complete` means the
operation finished, not that the transcript is accurate. Check names, numbers
and unclear passages against the original before treating them as verified.
A polished version or summary is a separate requested result.

An empty answer, non-stop finish reason or suspicious repeated lines returns
`partial`; partial text is retained. Repetition detection is a heuristic, not a
hallucination detector. Errors before a model result create no transcript.
Previously saved pages remain available. No automatic retry or provider fallback:
a timeout is reported for that page, and another billed attempt needs a deliberate
choice. The model call requests `disable_fallbacks=true` and `num_retries=0` from
the compatible gateway; operators must retain that routing contract.

Each call has at most 90 seconds for preparation and 120 seconds for the model,
within the existing 240-second builtin MCP deadline. It requests up to 8192 output
tokens, capped by instance accounting limits. Inputs remain limited to 20 MiB;
prepared pages to 25 megapixels and 20 MiB PNG. Larger pages must be cropped or
split explicitly. PDF page count is capped at 1000. No source downscaling occurs.

## Enable in an existing installation

This integration is disabled by default. No new public hostname is required.

1. Build the file service with `services/file-tools/Dockerfile` and the manager with
   the updated code. The service image includes the foreground model; runtime needs
   no internet access. Publish images only through the installation's normal process.
2. Add these entries to the existing instance configuration:

   ```yaml
   integrations:
     file-tools: true
   integration_grants:
     file-tools: ["workspace:read", "workspace:write"]
   ```

   Merge the entries into the existing maps. Do not replace the other integrations.
3. Merge `deploy/example/file-tools/catalog.json` into the
   installation's catalog. It uses the existing builtin `mcp` kind.
4. Add `deploy/example/file-tools/compose.yaml` after
   `deploy/example/compose.yaml`. Paths resolve relative to that base file.
   It sets `OC_FILE_TOOLS_URL=http://file-tools:8080` and creates an internal network
   shared only by manager and worker. The worker has no public port or workspace mount.
   For handwriting, also set `OC_HANDWRITING_MODEL` to the approved gateway alias
   and permit that alias on the existing gateway key. The example defaults it to `-`.
5. Render the instance, install the updated `media-tools` skill, and restart through
   the normal deployment process. Enable the catalog capability for the person and,
   with project capabilities enabled, for the project. Existing project configs are
   refreshed through the usual capability apply/start path.

Builtin MCP execution now allows 240 seconds, including project-specific configs.
The central broker remains at 60 seconds. File processing stops after 90 seconds;
the manager's file-service request ends after 100 seconds. The existing image
provider handler retains its 180-second deadline. There is no persistent job queue.
Provider results with an uncertain outcome stop image fallback and report
`IMAGE_OUTCOME_UNKNOWN`; clear refusals can still try the next configured model.

## Bounds and operation

- 20 MiB input/output file limit; raster input and generated output up to 25 megapixels.
  Provider PNGs are fully decoded before publishing, including replies with a valid header.
- Vector tracing up to 4 megapixels; SVG markup up to 512 KiB and 10000 elements.
- SVG previews fit inside 1024 by 1024 pixels.
- PDF up to 1000 pages, at most 100 explicitly selected pages per call. Large
  documents require a page range instead of silently truncating after page 100.
- One active worker subprocess per service. Busy requests return 429.
- The overlay limits memory to 12 GiB, CPU to 2, and temporary storage to 256 MiB.
- Disconnect or deadline kills the worker process. Restart loses in-progress work;
  completed files live in the project. No source files are persisted by the service.

PDF page preparation additionally uses pypdfium2 (PDFium); its packaged licenses
and third-party notices apply.

The implementation uses [rembg](https://github.com/danielgatis/rembg) with
[BiRefNet lite](https://huggingface.co/ZhengPeng7/BiRefNet_lite),
[VTracer](https://github.com/visioncortex/vtracer),
[CairoSVG](https://cairosvg.org/documentation/), Pillow, defusedxml and pypdf.
VTracer is pinned to `1.0.0a4`: its updated Python bindings fix the CPython 3.14
crash affecting 0.6; see the [upstream release](https://github.com/visioncortex/vtracer/releases).
This is a prerelease dependency. Review output regressions when updating it.
CairoSVG is LGPLv3; rembg, VTracer, BiRefNet lite, defusedxml and Pillow use permissive
licenses, and pypdf uses BSD-3-Clause. Model quality on real institutional images
still requires a representative acceptance set.

## Verification

Worker checks run offline in the built image:

```sh
docker build -t workspace-file-tools:local services/file-tools
docker run --rm --network none \
  -v "$PWD/services/file-tools:/tests:ro" -w /tests \
  workspace-file-tools:local python -m unittest -v test_worker test_server
```

Go tests cover project boundaries, capability gates, stale SVG sources, partial
writes and image edit input fidelity. For the real worker chain, run the service
on a test network and set `FILE_TOOLS_TEST_URL` before running
`go test ./internal/gateway/mcp -run TestFileToolsLiveChain -v` from `manager/`.
This test covers SVG creation, resizing, tracing, editing and real foreground
segmentation. It uses synthetic inputs and does not call an external image provider.


The opt-in `TestMediaLive` adds actual HTTP MCP discovery/calls, disk persistence,
hash checks, a real worker and the configured image/vision providers. It makes
billable calls with a separate test identity and a EUR 2 test cap. Supply a private
JSON file containing the deployment's provider environment settings through
`MEDIA_LIVE_CONFIG`; never commit that file. `MEDIA_LIVE_DIR` must be a fresh,
dedicated directory. Prepare its PDFs with `tests/e2e/media-fixtures.py`, using
the file worker image's Python packages, then run from `manager/`:

```sh
MEDIA_LIVE_CONFIG=/private/provider.json \
MEDIA_LIVE_DIR=/private/media-test \
FILE_TOOLS_TEST_URL=http://worker:8080 \
go test ./internal/gateway/mcp -run '^TestMediaLive$' -v -count=1 -timeout=12m
```

The JSON uses `LITELLM_BASE_URL` and `LITELLM_API_KEY`, or their
`OC_LLM_UPSTREAM_URL`/`OC_LLM_UPSTREAM_KEY` overrides, plus
`OC_IMAGE_MODELS`, `OC_IMAGE_EDIT_MODEL` and `OC_VISION_MODEL`.
Artifacts, MCP responses and usage summaries remain in the test directory.
`MEDIA_LIVE_SERVE=1` instead serves the same test gateway on loopback for up to
ten minutes. Read its URL from `MEDIA_LIVE_DIR/endpoint`, use session
`ses_medialive1234` and mount that directory as `/workspace` in an isolated runtime.
Create `MEDIA_LIVE_DIR/done` to stop it. This is a test harness, not a deployment.


## Deployment resource check

The example caps the worker at 12 GiB and two CPUs; transforms remain serialized.
Size the host for the active worker alongside user runtimes. A healthy parent process
alone does not prove that the model subprocess has enough memory to finish.


