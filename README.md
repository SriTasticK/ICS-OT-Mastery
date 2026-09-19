# FIELDNOTES — private research lab

**FIELDNOTES** is a Python/Flask learning and practice app with 42 introductory modules, reasoning-aware checkpoints, notebooks, offline simulations, and private Docker deployment. Dependencies are managed with **uv**.

See **[LAB.md](LAB.md)** for installation, grading limits, GPU review, isolation, testing, and backups.

```bash
sudo bash scripts/lab.sh start
```

Then open `http://127.0.0.1:8080`. Retrieve the first-run token with:

```bash
sudo docker exec private-research-lab cat /data/setup-token
```
