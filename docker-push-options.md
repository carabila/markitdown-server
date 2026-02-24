# Docker Push Options for MarkItDown Server

The canonical Docker Hub publish workflow is:

```bash
docker login
./scripts/push-docker-variants.sh --namespace yourusername
```

What it publishes:
- `yourusername/markitdown-server:latest` (multi-arch: amd64 + arm64)
- `yourusername/markitdown-server:cpu` (multi-arch: amd64 + arm64)
- `yourusername/markitdown-server:cpu-amd64`
- `yourusername/markitdown-server:cpu-arm64`

Optional:

```bash
./scripts/push-docker-variants.sh --namespace yourusername --builder <buildx-builder>
./scripts/push-docker-variants.sh --namespace yourusername --image markitdown-server
```

Verify the published manifest:

```bash
docker buildx imagetools inspect yourusername/markitdown-server:latest
```
