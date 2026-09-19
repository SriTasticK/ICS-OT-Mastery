# FIELDNOTES — private research lab

A Python/Flask application for a single learner, with local SQLite persistence and a Docker deployment. Python dependencies are managed exclusively with **uv**, `pyproject.toml`, and the committed `uv.lock`.

## What is included

- A six-stage guided learning flow, separate practice and final validation pages, a simulation workbench, and a research notebook.
- All **42 requested subject areas and 915 topic labels**, ordered around the requested dependency chain. Safety, foundational mathematics, and research methods come early.
- **42 expanded guided lessons, 42 worked examples, 84 assumption checks, and 42 distinct foundation cases**, each with a result check and three case-specific causal/evidence/counterfactual probes. This is an introductory curriculum spanning the requested areas, not 915 fully developed lessons or a certification of subject mastery.
- Primary-source reading paths for every module. Learning text is available offline; external references require your browser to access their sites.
- Hypotheses, confidence, reasoning, observations, reflections, complete teach-back workflows, optional inert code evidence, drafts, attempt history, and linked notebook snapshots.
- Notes, journals, and observations with search, editing, module association, and JSON export. A separate topic research map records definitions/examples and sources for deeper study.
- Three bounded, offline simulators: fixed-width integer representation, a tank with a latched trip, and Modbus TCP frame parsing.
- Optional GPU-backed local semantic review through Ollama. No cloud AI endpoints are supported.

## Deployment status and the localhost fix

Docker 29 left the configured port mapping inactive when the app was attached only to an internal network. The app could report healthy from inside its container while `127.0.0.1:8080` refused connections. The repaired architecture is:

```text
Browser -> 127.0.0.1:8080 -> unprivileged gateway
                                 | internal network
                                 +-> private-research-lab:8080
                                 +-> ollama:11434 (optional, no published port)
```

The app and reviewer have no ingress-network connection. The gateway is the only service attached to the dedicated ingress bridge, where IP masquerading is disabled. It forwards to a fixed app upstream, not to arbitrary destinations. Both Compose and CLI launchers implement this layout.

To repair an existing deployment made with the old launcher without touching its database:

```bash
sudo bash scripts/gateway.sh
sudo bash scripts/check-deployment.sh
```

## Start with Docker on this machine

Docker is installed, but the Compose plugin is absent and the current user cannot access `/var/run/docker.sock`. Use the provided equivalent Docker CLI launcher from the repository root:

```bash
sudo bash scripts/lab.sh start
sudo bash scripts/lab.sh status
sudo docker exec private-research-lab cat /data/setup-token
```

Open **http://127.0.0.1:8080**, enter the one-time setup token, and create a password of at least 12 characters. The launcher does not print or choose a password for you. Startup can take a few seconds before the token file exists.

The first image build needs internet access for base images and locked Python dependencies. The running application uses an internal Docker network. A separate unprivileged gateway bridges localhost ingress to that network; only the gateway publishes a port. There is no dependency download at runtime.

```bash
sudo bash scripts/check-deployment.sh
```

This checks the ACTIVE publication address, internal network, non-root app user, read-only root filesystems, and the actual localhost HTTP endpoint. A configured port mapping alone is insufficient: Docker 29 left publication inactive for an internal-only container. Review `sudo docker logs private-research-lab` if startup fails.

If Docker permissions are already configured on another machine, omit `sudo`.

### Compose equivalent

With Docker Compose v2 installed:

```bash
docker compose up -d --build
docker compose ps
docker compose exec lab cat /data/setup-token
```

Use either the CLI launcher or Compose as the deployment manager. They intentionally use the same container, volume, and network names, so running both simultaneously is not supported.

### Access from another device on your LAN

The application port is deliberately bound to loopback, not to every interface. Use an existing SSH connection over your private LAN to forward it:

```bash
# Run on the other device; replace the user and private LAN address.
ssh -N -L 8080:127.0.0.1:8080 your-user@192.168.1.20
```

Then open `http://127.0.0.1:8080` on that device. This keeps the lab port unpublished to both the LAN and internet, and encrypts the remote connection. No router port-forwarding or public reverse proxy is needed. This repository does not install or reconfigure SSH.

### Runtime boundaries

- The unprivileged gateway alone publishes `127.0.0.1:8080`. Its separate ingress bridge disables IP masquerading; the app and reviewer stay on the internal network only. No IPv6 wildcard or `0.0.0.0` host binding is used.
- `private-lab-internal` is an internal Docker network without the usual internet-egress route. Host bridge services can still be reachable; this is not a boundary against a compromised host or Docker administrator.
- The web container runs as UID/GID 10001, drops all capabilities, forbids new privileges, has a read-only filesystem, and has memory/CPU/PID limits.
- Only `/data` is persisted; `/tmp` is a bounded tmpfs. No Docker socket, host filesystem, host network, or physical device is mounted into the web app.
- Browser assets are bundled locally. There are no analytics, external fonts, CDNs, remote scripts, or background cloud calls.
- Learner code is **never executed**. Artifacts, firmware excerpts, malware events, and industrial frames are inert educational data. This web container is not a live-malware or untrusted-native-code sandbox.
- Host/router/proxy configuration remains outside the application’s control. Do not forward this port or place it behind a public tunnel. Docker explains loopback publication and routing caveats in its [port-publishing documentation](https://docs.docker.com/engine/network/port-publishing/).

## How progression is evaluated

Practice follows the ordered path. Lessons and deeper-topic research remain readable before practice unlocks.

1. **Purpose:** understand why the module matters and the mental model it builds.
2. **Explanation:** study the concept and mechanism, predict a worked example, reveal its step-by-step walkthrough, and examine failure conditions and prevention/correction.
3. **Further reading:** resources appear after the explanation, with prompts for extending the model. External reading is encouraged, not required to answer the foundation case.
4. **Assumption checks:** record the lesson and answer two module-specific questions. Corrections explain the mechanism; retry until both checks pass. The server enforces this before practice.
5. **Practice:** predict, solve a separate inert problem, and record reasoning and observations. A correct result and complete record open final validation but do not unlock the next module.
6. **Teach it back:** explain the concept, complete causal workflow, failure condition, prevention/correction, and observations in your own words. Complete the case-specific reasoning probes, reflect, and link a notebook entry. Only a passed final checkpoint unlocks the next module.

Practice records are stored separately and the final submission references a server-owned practice snapshot; changing hidden form values cannot replace that evidence. Drafts persist for both stages. New teaching and assumption-check records use a separate version from existing checkpoint history, so the upgrade preserves previous completions and notes. New submissions must follow the guided stages. JSON export includes assumption-check and practice records.

**Every dimension must pass.** A correct answer cannot compensate for an incorrect causal claim. Confidence changes feedback, not marks. A failed attempt provides a corrective principle and a link back to the lesson. Drafts and past attempts remain available.

In **structured mode**, free text is checked for completeness (12 words and 8 distinct words per required field) and self-reviewed. This is not a semantic assessment of prose or code. Selected claims test specific misconceptions but cannot prove that a learner understands everything or prevent intentional gaming. The UI states these limits.

In **local AI mode**, a local model independently assesses the explanation, observation, reflection, linked notebook, and complete workflow. The workflow must cover definition, causal steps, failure, prevention/correction, and evidence; a definition alone is insufficient. The initial hypothesis is context for reflection, and optional code has its own consistency assessment without execution. Every required dimension needs at least 2/3 and the server derives the overall verdict from those scores. The model returns field-specific evidence IDs under a constrained JSON schema. The server rejects unknown or cross-field IDs and retrieves the cited original text itself, preventing quote-copying errors. Incomplete model output also holds the gate. Contradictory explanations should receive revision feedback; errors, uncertain verdicts, malformed responses, or invalid citations hold progression. A model can still misjudge reasoning or be influenced by adversarial text, so inspect the feedback rather than treating it as certification.

Successful attempts remain historical evidence. Switching review modes does not retroactively invalidate previously completed checkpoints. Each attempt records its mode and curriculum version.

Alternative: a trusted human can inspect the JSON export and immutable reports. A separate mentor account/approval workflow is not implemented. Cloud review is intentionally not part of this private deployment.

## GPU review on your laptop

Read-only hardware inspection found:

- NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB VRAM.
- 3764 MiB free at inspection time; actual availability changes with desktop activity.
- Working NVIDIA driver 610.57.04.
- NVIDIA Container Toolkit 1.20.0 and libnvidia-container 1.20.0 are now installed. Docker runtime configuration was added while preserving the existing settings; the original is backed up at `/etc/docker/daemon.json.before-lab-nvidia`.

The RTX 3050 is listed in [Ollama’s supported NVIDIA hardware](https://docs.ollama.com/gpu). An earlier 128-token synthetic generation test of the original `qwen3:4b` model measured **9.28 tokens/s on CPU and 59.32 tokens/s on GPU (6.39×)**, excluding model-loading time. The instruction-tuned replacement measured **9.53 tokens/s on CPU and 58.42 tokens/s on GPU (6.13×)** on the same 128-token synthetic benchmark. The GPU launcher repeats this comparison before activation. This is a single synthetic speed sample, not a complete review-latency benchmark. The original semantic review copied a notebook sentence into the reflection evidence field and failed validation. The revised reviewer assesses reasoning, observations, reflection, notebook, and teach-back workflow independently, plus code when provided. Every field must score at least 2/3. It uses field-specific evidence IDs and server-side excerpt retrieval instead of asking the model to copy quotations. Reference answers retain their questions, including counterfactual conditions. An initial mistaken hypothesis is acceptable when the final reflection explicitly corrects it. No learner data is used for its regression checks. Docker GPU access requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html); see also [Ollama’s Docker instructions](https://docs.ollama.com/docker). The lab scripts do not modify host drivers or daemon configuration; the toolkit installation and runtime setup are separate system administration steps.

Guided-teaching validation on 2026-09-19: **56 automated tests**, **17 live-model cases**, and the real-model submission-to-unlock flow passed. Browser validation covered worked-example reveal, correction and retry, saved drafts, notebook linking, final unlock, and desktop/mobile layouts using a disposable account. Warm five-field reviews took approximately 10–13 seconds in the synthetic suite. The model still runs fully on the GPU; these tests cover introductory cases, not every topic or possible learner explanation.

The optional reviewer uses `qwen3:4b-instruct-2507-q4_K_M` (approximately 2.5 GB of weights), a 4096-token context, quantized KV cache, and one concurrent inference. This is a constrained, fallible tutor suitable for introductory cases, not a research-grade judge. Inputs, including evidence identifiers, over an 8 KB review budget are refused rather than silently truncated; keep concise case-specific text and store longer notes separately.

A network-isolated test container successfully reported the RTX 3050 through the toolkit. The GPU configurations request `nvidia.com/gpu=all` through CDI explicitly. On this hybrid AMD/NVIDIA machine, generic `--gpus all` selected AMD, and the legacy NVIDIA device-driver registration would require a daemon restart. CDI permits NVIDIA access without interrupting other running containers.

To prepare and enable the reviewer:

```bash
# One-time connected model download; no learner data mounted and no ports published.
sudo bash scripts/model-prepare.sh

# Benchmark CPU/GPU, test correct/contradictory reasoning, and require full GPU offload before changing the web mode.
sudo bash scripts/gpu-start.sh
sudo docker exec private-lab-reviewer ollama ps
sudo bash scripts/check-deployment.sh
```

The preparation container exits after downloading. The runtime reviewer has **no published API port** and joins only the internal network. Cloud functionality is disabled. The web app accepts only local/private reviewer addresses and ignores HTTP proxy environment variables for review requests.

The CLI GPU launcher first benchmarks a synthetic prompt on CPU and GPU, requiring at least a 10% generation-speed improvement. It builds a candidate image, runs the complete synthetic suite and submission-to-unlock flow against that image using disposable data, and confirms full GPU offload. Each intentionally incorrect field must itself be rejected; failure in an unrelated field cannot satisfy the test. If any check fails, the current web application and grading mode remain unchanged. Activation takes a SQLite backup within the private data volume, retains the previous stopped app container, and automatically restores that container if startup fails. The expanded 17-case regression suite includes safety boundaries, C pointers, TCP framing, and PLC scan timing, plus contradictory notebooks/code, invented observations, corrected initial hypotheses, prompt injection, incomplete teach-back, and incorrect prevention claims. These checks do not prove general grading accuracy. If the reviewer is unavailable, returns invalid evidence references, or expresses uncertainty, submissions remain pending with a saved draft and a retry message; the app does not silently fall back to a passing structured grade.

For Compose users, after model preparation:

```bash
docker compose -f compose.yaml -f compose.gpu.yaml up -d
docker compose -f compose.yaml -f compose.gpu.yaml exec ollama ollama run qwen3:4b-instruct-2507-q4_K_M 'Reply ready.'
docker compose -f compose.yaml -f compose.gpu.yaml exec ollama ollama ps
```

The Compose override explicitly enables AI review and holds the gate if the service cannot review. Unlike the CLI GPU launcher, Compose does not automatically verify GPU offload first.

To deliberately return to structured mode under the CLI launcher, run `sudo bash scripts/lab.sh rebuild`, then stop the separate reviewer with `sudo docker stop private-lab-reviewer`. Data is preserved. For Compose, return to the base compose configuration and recreate the lab service.

## Development with uv

```bash
uv sync --frozen
uv run pytest -q
uv run gunicorn --bind 127.0.0.1:8080 --workers 1 --threads 4 --timeout 120 'lab.app:create_app()'
```

Native development stores private data in `.lab-data/`, ignored by Git. Set `LAB_DATA` to choose another location. Docker stores data in the named volume, not this directory. No pip commands or separate requirements file are used.

Useful configuration:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LAB_DATA` | `.lab-data` natively; `/data` in Docker | Database and setup token directory |
| `LAB_HOSTS` | `localhost,127.0.0.1` | Host-header allowlist |
| `LAB_REVIEW_MODE` | `structured` | `structured` or `local-ai` |
| `LAB_REVIEW_URL` | `http://ollama:11434` | Private local model service |
| `LAB_REVIEW_MODEL` | `qwen3:4b-instruct-2507-q4_K_M` | Preloaded Ollama model name |
| `LAB_HTTPS` | unset | Set `1` only when serving through a configured local HTTPS endpoint; enables secure cookies |

The default loopback HTTP deployment uses HttpOnly, SameSite=Strict session cookies, CSRF tokens, origin checks, a Host allowlist, an eight-hour session lifetime, login throttling, escaped templates, and a strict self-only content policy.

### Browser checks

The browser smoke test needs Chromium at `/usr/bin/chromium`, or update its executable path. The script automatically creates a temporary database and a loopback-only test server, and removes them after the test. It never uses your study database.

```bash
uv run python tests/browser_smoke.py
```

It exercises setup, login, worked-example reveal, incorrect and corrected assumption checks, practice gating, final teach-back, draft saving, notebook linking, progression, and mobile overflow checks. Screenshots go to ignored `artifacts/`.

## Data, backup, and updates

```bash
sudo bash scripts/lab.sh backup
sudo bash scripts/lab.sh stop
sudo bash scripts/lab.sh resume
sudo bash scripts/lab.sh rebuild
```

`backup` uses SQLite’s online backup API, so the output includes committed WAL data. It creates a private `lab-backup-<timestamp>.sqlite3` in the repository. The UI’s JSON export contains research records but not account hashes or session secrets; it is a readable export, not a full authentication backup or an implemented import workflow.

`rebuild` replaces the container while retaining `private-lab-data`. It does not delete your volume. Do not use `docker compose down -v` unless you intend to delete your data. Keep a tested SQLite backup before changing curriculum schema or restoring data. The initial schema is created automatically; no future migration policy is implied.

For a full database restore, stop the application, copy the backup into a **fresh** named volume as `/data/lab.sqlite3` owned by `10001:10001`, and point a new deployment at that volume. Do not overwrite an actively used SQLite database or mix an old database with another run’s WAL/SHM files. Preserve the original volume until the restored deployment has been checked.

## Extending the curriculum

- `lab/catalog.py`: original subject numbers, all requested topic labels, and ordered prerequisite path.
- `lab/lessons.py`: authored explanations, case artifacts, accepted result forms, and three reasoning probes per case. The first option is the server-side correct claim; the UI randomizes order and uses opaque choice IDs.
- `lab/teaching.py`: authored purpose, model, mechanism, worked example, failure, correction, and prediction for each module.
- `lab/resources.py`: primary-source reading paths.
- `lab/grading.py`: transparent structured rubric.
- `lab/reviewer.py`: optional local semantic rubric and response validation.
- `lab/simulations.py`: pure bounded experiments.

Bump a module’s curriculum version when changing the meaning of an assessment. Completion is matched to the current version. Broad fields such as C mastery, RF analysis, and firmware research require many further experiments beyond their introductory checkpoint; the topic map makes that remaining scope explicit.
