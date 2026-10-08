# RUN.md: Commands for testing and demoing the project

Windows PowerShell. Copy the block you need.

Live service: https://image-processing-service-wob4.onrender.com

---

## 0. Setup (do this in EVERY new terminal window)

`$BASE` is forgotten whenever you close or open a terminal. If it is not set, curl gets a broken URL and prints `HTTP status: 000`.

```powershell
# Work outside the repo so test files never get committed
mkdir C:\demo -ErrorAction SilentlyContinue
Set-Location C:\demo

# Pick ONE target
$BASE = "https://image-processing-service-wob4.onrender.com"   # deployed on Render
# $BASE = "http://localhost:5000"                              # local Docker container

# Create test images (only needed once)
python -c "from PIL import Image; Image.new('RGB',(400,300),'red').save('test.jpg')"
python -c "from PIL import Image; Image.new('RGBA',(400,300),(255,0,0,128)).save('test.png')"
```

Check the variable is set:

```powershell
$BASE
```

Wake the Render service before a demo (the free tier sleeps when idle, first request can take about a minute):

```powershell
curl.exe --max-time 90 $BASE/health
```

---

## 1. API calls

Always `curl.exe`, never plain `curl`. Each command prints the HTTP status and saves the result as a file.

```powershell
# Health
curl.exe $BASE/health

# Resize
curl.exe -sS -o resized.jpg -w "HTTP status: %{http_code}`n" -X POST -F "image=@test.jpg" -F "width=200" -F "height=200" $BASE/resize

# Compress
curl.exe -sS -o compressed.jpg -w "HTTP status: %{http_code}`n" -X POST -F "image=@test.jpg" -F "quality=50" -F "format=jpeg" $BASE/compress

# Convert JPEG to WebP
curl.exe -sS -o converted.webp -w "HTTP status: %{http_code}`n" -X POST -F "image=@test.jpg" -F "format=webp" $BASE/convert

# Convert transparent PNG to JPEG
curl.exe -sS -o from_png.jpg -w "HTTP status: %{http_code}`n" -X POST -F "image=@test.png" -F "format=jpeg" $BASE/convert

# Grayscale
curl.exe -sS -o grayscale.jpg -w "HTTP status: %{http_code}`n" -X POST -F "image=@test.jpg" $BASE/grayscale
```

Every command should print `HTTP status: 200`.

## 2. Check the results

```powershell
python -c "from PIL import Image; [print(f, Image.open(f).size, Image.open(f).format, Image.open(f).mode) for f in ['test.jpg','resized.jpg','compressed.jpg','converted.webp','grayscale.jpg','from_png.jpg']]"
```

Expected:

| File | Size | Format | Mode |
|---|---|---|---|
| `resized.jpg` | 200x200 | JPEG | RGB |
| `compressed.jpg` | 400x300 | JPEG | RGB |
| `converted.webp` | 400x300 | WEBP | RGB |
| `grayscale.jpg` | 400x300 | JPEG | L |
| `from_png.jpg` | 400x300 | JPEG | RGB |

## 3. Error handling (expect HTTP 400 and a JSON error)

```powershell
curl.exe -i -X POST $BASE/resize
curl.exe -i -X POST -F "image=@test.jpg" -F "width=abc" -F "height=200" $BASE/resize
```

Do not combine `-i` with `-o`; the headers would be written into the image file.

---

## 4. Run locally with Docker

Docker Desktop must be running. Run these from the repo folder.

```powershell
Set-Location C:\Shail\Somaiya\LY\DevOps\IA\image-processing-cicd
docker build -t image-processing-local .
docker run --rm -p 5000:5000 image-processing-local
```

Leave that window open. In a SECOND window run section 0 with `$BASE = "http://localhost:5000"`, then section 1. Stop the container with `Ctrl+C` in the first window.

Run the unit tests (repo folder):

```powershell
pip install -r requirements.txt
pytest
```

---

## 5. Pipeline demo: change one line, push, deployed

Run in the repo folder. Use a NEW number each take, otherwise git says "nothing to commit" and no pipeline starts. Wait for the previous run to finish before pushing again.

```powershell
Set-Location C:\Shail\Somaiya\LY\DevOps\IA\image-processing-cicd
git checkout main
git pull origin main
git status
```

Edit the `Dockerfile` and add this line after the `ENV` line (change the number each take):

```dockerfile
LABEL demo.version="5"
```

Then:

```powershell
git add Dockerfile
git commit -m "Demo: bump demo.version label to 5"
git push origin main
```

Watch, in order:

1. GitHub **Actions**: `test`, `build-and-push`, `deploy` go green (about 1.5 to 2 minutes).
2. **Docker Hub** Tags: a new tag equal to the commit SHA.
3. **Render** Events: a deploy "Triggered via Deploy Hook" with the same SHA. Do not open Render Settings on video; the deploy hook URL is shown there.

Prove the deployed image contains the change:

```powershell
$sha = git rev-parse HEAD
$sha
docker pull shail712/image-processing-service:$sha
docker inspect --format '{{json .Config.Labels}}' shail712/image-processing-service:$sha
```

Expected output: `{"demo.version":"5"}`. If the pull says "not found", the `build-and-push` job has not finished yet; wait and retry.

Safety gate: show the earlier red-X run in the Actions history (a failing test stops the pipeline, nothing is built or deployed).

---

## 6. Cleanup

```powershell
Set-Location C:\demo
Remove-Item test.jpg, test.png, resized.jpg, compressed.jpg, converted.webp, grayscale.jpg, from_png.jpg -ErrorAction SilentlyContinue
```

In the repo folder, make sure no test images are sitting there:

```powershell
Set-Location C:\Shail\Somaiya\LY\DevOps\IA\image-processing-cicd
git status
```

It should say the working tree is clean (except your intended change).

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `HTTP status: 000` | `$BASE` is not set in this terminal, or nothing is listening | Run section 0 again, check `$BASE`. For localhost, start the container. |
| `curl: (26) Failed to open/read local data` | The image file is not in the current folder | Run `dir`, `Set-Location C:\demo`, or use the right filename |
| `A parameter cannot be found that matches parameter name 'X'` | You typed `curl` | Use `curl.exe` |
| `Unable to connect to the remote server` on localhost | No local container running (`--rm` deletes it after Ctrl+C) | Start it again (section 4) |
| Empty reply from the Render URL | You used `http://` | Use `https://` |
| `HTTP status: 404` on an endpoint | Deployed image lacks the new code | Check the latest Actions run is green and merged to `main` |
| `HTTP status: 400` | Missing or invalid input | Check the field names: `image`, `width`, `height`, `quality`, `format` |
| First request hangs for a minute | Render free tier is waking up | Wait, or wake it earlier with `/health` |
| `docker pull` says not found | Tag not pushed yet | Wait for `build-and-push` to finish |
| Template parsing error from `docker inspect` | PowerShell quoting | Use the `{{json .Config.Labels}}` form from section 5 |