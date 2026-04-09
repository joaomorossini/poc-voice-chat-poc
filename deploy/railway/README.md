# Railway Deployment

## One-Click Deploy

1. Push your configured template to GitHub
2. Go to [railway.app](https://railway.app) and create a new project from your repo
3. Railway auto-detects `railway.toml` and configures services
4. Set environment variables in Railway dashboard (copy from `.env`)
5. Deploy

## Services

Railway deploys each service as a separate container with private networking.

| Service | Port | Notes |
|---------|------|-------|
| api | 3080 | LibreChat + overlay |
| mongodb | 27017 | Primary datastore |
| meilisearch | 7700 | Only if search enabled |
| vectordb | 5432 | Only if RAG enabled |
| rag_api | 8000 | Only if RAG enabled |
| MCP servers | 8001-8004 | As configured in project.yaml |

## Environment Variables

Set these in Railway's dashboard (Variables tab):
- All `CHANGE_ME` values from `.env`
- `MONGO_URI` — Railway provides MongoDB connection string
- `MEILI_MASTER_KEY` — generate a strong key
- LLM provider API keys

## Cost Estimate

- **Minimal** (app + mongodb): ~$5/month on Railway Hobby plan
- **Standard** (+ meilisearch): ~$8/month
- **Full** (+ RAG + MCP servers): ~$15-20/month
