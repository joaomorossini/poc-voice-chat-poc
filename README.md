# Fullstack Chat Agent Template

A template for building production-ready agentic chat applications. Overlays customizations on [LibreChat](https://github.com/danny-avila/LibreChat) without modifying its source code.

## What You Get

- **Branded chat UI** — your colors, fonts, logo on top of LibreChat
- **Domain-specific MCP tools** — 4 example patterns (database, API wrapper, knowledge retrieval, agent delegation)
- **Multi-agent orchestration** — Agent Chain, Handoffs, and hub-and-spoke via agent-as-tool
- **RAG** (optional) — file indexing and semantic search via PGVector
- **Cross-session memory** (optional) — key/value store that persists across conversations
- **Voice** (optional) — real-time voice via Pipecat + WebRTC
- **Feature toggles** — enable/disable capabilities via `project.yaml`
- **Multi-cloud deploy** — configs for Railway, DigitalOcean, Render, and local Docker

## Quick Start

```bash
# 1. Clone (use "Use this template" on GitHub, or clone directly)
git clone --recursive https://github.com/YOUR_ORG/YOUR_PROJECT.git
cd YOUR_PROJECT

# 2. Configure
#    Edit project.yaml — set your project name, theme, features, and providers
nano project.yaml

# 3. Bootstrap
#    Generates .env, librechat.yaml, docker-compose.override.yml, and theme CSS
make bootstrap

# 4. Add secrets
#    Replace all CHANGE_ME values in .env with real API keys
nano .env

# 5. Run
make up
# Open http://localhost:3080
```

## Prerequisites

- Docker & Docker Compose v2
- [yq](https://github.com/mikefarah/yq) (YAML processor — `brew install yq`)
- Git (with submodule support)
- An API key for at least one LLM provider (Anthropic, OpenAI, Google, or custom)

## Project Structure

```
├── project.yaml              ← Single config surface (edit this)
├── app/
│   ├── Dockerfile            ← Builds LibreChat + overlay
│   ├── styles/theme.css      ← Generated theme (from project.yaml)
│   ├── prompts/              ← Agent system prompts
│   ├── public/images/        ← Logos and branding assets
│   ├── components/           ← Custom React components (optional)
│   └── LIBRECHAT_CHANGES.md  ← Overlay tracking / rebase checklist
├── mcp-servers/
│   ├── database/             ← Pattern: SQL query tool
│   ├── api-wrapper/          ← Pattern: external API integration
│   ├── knowledge/            ← Pattern: knowledge base search
│   └── agent-delegate/       ← Pattern: hub-and-spoke orchestration
├── pipecat-server/           ← Voice sidecar (optional)
├── scripts/
│   ├── bootstrap.sh          ← Config generator
│   └── validate-overlay.sh   ← Post-upgrade overlay checker
├── deploy/
│   ├── railway/              ← Railway deploy config
│   ├── digitalocean/         ← DO droplet setup
│   ├── render/               ← Render blueprint
│   └── docker-compose/       ← Base compose for local
├── librechat/                ← Git submodule (upstream, never modify)
├── pipecat/                  ← Git submodule (upstream, optional)
├── Makefile                  ← Build/deploy automation
└── .env                      ← Generated secrets (git-ignored)
```

## Configuration

All configuration flows through `project.yaml`. After editing, run `make bootstrap` to regenerate derived files.

### Feature Toggles

| Feature | Default | Config Key | Infra Impact |
|---------|---------|-----------|-------------|
| RAG | off | `features.rag` | Adds vectordb + rag_api containers |
| Search | on | `features.search` | Adds meilisearch container |
| Voice | off | `features.voice` | Adds pipecat-voice container |
| Memory | on | `features.memory` | No extra containers (uses MongoDB) |
| Code Interpreter | off | `features.code_interpreter` | No extra containers |
| Agent Chain | off | `features.agent_chain` | No extra containers |
| Agent Handoffs | on | `features.agent_handoffs` | No extra containers |
| ARDEN Fleet CI | on | `arden_fleet.enabled` | Generates GitHub Actions workflows |

### MCP Server Patterns

Each example demonstrates a different integration pattern:

| Pattern | Directory | Use Case |
|---------|-----------|----------|
| **Database** | `mcp-servers/database/` | Safe read-only SQL queries against domain data |
| **API Wrapper** | `mcp-servers/api-wrapper/` | External API integration with auth and normalization |
| **Knowledge** | `mcp-servers/knowledge/` | File-based knowledge search with citations |
| **Agent Delegate** | `mcp-servers/agent-delegate/` | Hub-and-spoke multi-agent orchestration |

## Deployment

### Local (Docker Compose)
```bash
make bootstrap && make up
```

### Railway
See `deploy/railway/README.md` for one-click deploy instructions.

### DigitalOcean
```bash
ssh root@your-droplet
git clone --recursive https://github.com/you/your-project.git
cd your-project && bash deploy/digitalocean/setup.sh
```

### Render
Connect your GitHub repo to Render — it reads `deploy/render/render.yaml` automatically.

## Upgrading LibreChat

```bash
cd librechat
git fetch --tags
git checkout v1.X.Y          # New release tag
cd ..
make validate                 # Check overlay targets
make build                    # Rebuild with new version
```

Review `app/LIBRECHAT_CHANGES.md` for the overlay rebase checklist.

## Versions

Built and verified against:
- **LibreChat**: v0.8.4
- **Pipecat**: v0.0.108
- **Docker Compose**: v2
- **Node.js**: 20 (Alpine)
- **Python**: 3.12 (for MCP servers and Pipecat)
