## CI/CD Pipeline

Every push to GitHub is automatically tested. Every push to `main` that passes is built into a Docker image, published to Docker Hub, deployed to Render, and verified with a live health check. No manual step exists between `git push` and the running service.

**Live service:** https://image-processing-service-wob4.onrender.com/health
**Docker Hub image:** `shail712/image-processing-service`

### Pipeline flow

```mermaid
flowchart LR
    A[git push] --> B[test<br/>pytest]
    B --> C[build-and-push<br/>Docker Hub]
    C --> D[deploy<br/>Render deploy hook]
    D --> E[verify<br/>curl /health]
```

The workflow is defined in `.github/workflows/cicd.yml`.

### Jobs

| Job | Runs on | What it does |
|---|---|---|
| `test` | every push, and pull requests to `main` | Checks out the code, sets up Python 3.12 with pip caching, installs `requirements.txt`, runs `pytest`. A failing test stops the pipeline. |
| `build-and-push` | push to `main` only, after `test` passes | Logs in to Docker Hub, builds the image with Buildx, and pushes it with two tags: `latest` and the full commit SHA. |
| `deploy` | push to `main` only, after `build-and-push` passes | Calls the Render deploy hook with the SHA-tagged image, then polls `/health` until the service reports healthy. |

Feature branches and pull requests run only `test`. They never build images or deploy.

### Image tagging

Each build is pushed twice:

- `shail712/image-processing-service:latest` is a moving label that always points at the newest build.
- `shail712/image-processing-service:<commit-sha>` identifies exactly one build.

The deploy job uses the SHA tag, so the version running in production can be traced to a specific commit and rolled back precisely. The same SHA appears in GitHub, on Docker Hub, and in Render's deploy events.

### Render deployment

The service is an image-backed Render web service. Render does not build anything. It pulls the image the pipeline already tested and pushed.

| Setting | Value |
|---|---|
| Service type | Web Service (deploy an existing image from a registry) |
| Image | `docker.io/shail712/image-processing-service:latest` (public) |
| Instance type | Free |
| Environment variable | `PORT=5000` |
| Health check path | `/health` |

Render does not redeploy automatically when a new image is pushed to a registry, so the pipeline triggers it with a **deploy hook**. The workflow appends an `imgURL` parameter to the hook so Render deploys the SHA-tagged image instead of `latest`.

`PORT=5000` tells Render which port to route traffic to. The container already listens on `0.0.0.0:5000` through gunicorn, so the Dockerfile did not need to change.

### Deployment verification

A successful call to the deploy hook only means Render accepted the request. The final step of the `deploy` job therefore waits 30 seconds, then calls `/health` up to 20 times, 15 seconds apart, and checks that the response body contains `"status":"healthy"`. If it never does, the job fails and the pipeline shows red. The retries cover Render's free-tier cold starts, which can take about a minute.

### GitHub secrets

Stored under Settings > Secrets and variables > Actions. Values are never committed to the repository.

| Secret | Purpose |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub login and image namespace |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Read & Write) |
| `RENDER_DEPLOY_HOOK` | Render deploy hook URL, which acts as a trigger and a password |

### Running the demo

1. Make a small change, for example add `LABEL demo.version="2"` to the `Dockerfile`.
2. Commit and push to `main`:

```powershell
git add Dockerfile
git commit -m "Demo: bump demo.version label to 2"
git push origin main
```

3. In the GitHub **Actions** tab, watch `test`, `build-and-push` and `deploy` run in order.
4. On Docker Hub, a new tag matching the commit SHA appears.
5. In the Render dashboard under **Events**, a new deploy appears, triggered via Deploy Hook, referencing the same SHA.
6. Verify the deployed image:

```powershell
$sha = git rev-parse HEAD
docker pull shail712/image-processing-service:$sha
docker inspect --format '{{json .Config.Labels}}' shail712/image-processing-service:$sha
curl.exe -i https://image-processing-service-wob4.onrender.com/health
```

To show the safety gate, push a branch with a deliberately failing test. The `test` job fails and nothing is built or deployed.

### Known limitations

- The health check proves the service is up and healthy, not that the new version is the one answering. During a deploy Render keeps the old instance serving until the new one is ready, so an early check could reach the old version. A stricter check would make `/health` return the commit SHA.
- The Render free tier spins down after inactivity, so the first request after idle can take 50 seconds or more.
- Auto-deploy is off by design. An image-backed service deploys only when the deploy hook fires.
- The service's configured image stays `latest`, so a manual "Deploy latest reference" in the dashboard deploys `latest`. The pipeline always deploys the SHA.

### Screenshots

Add these under `docs/screenshots/` and link them here:

1. Green GitHub Actions run with all three jobs
2. Red run from a failing test, showing the pipeline stops
3. Docker Hub Tags page showing `latest` and the SHA tag
4. Render Events showing a deploy triggered via Deploy Hook with the SHA
5. Render Settings showing the image, `PORT`, and health check path
6. `/health` response from the live URL