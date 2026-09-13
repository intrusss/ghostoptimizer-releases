"""Publish only the checksum-verified installer from a tested build artifact."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

request = json.loads(Path("release-request.json").read_text(encoding="utf-8"))
url = request["artifact_url"]
assert url.startswith("https://sdmntprwestus3.oaiusercontent.com/"), "Unexpected artifact origin"
with urllib.request.urlopen(url, timeout=60) as response:
    archive = response.read(100 * 1024 * 1024 + 1)
assert len(archive) <= 100 * 1024 * 1024
assert hashlib.sha256(archive).hexdigest() == request["archive_sha256"]
manifest = request["manifest"]
assert manifest["latest_version"] == "1.6.1"
with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
    data = bundle.read("release/GhostOptimizer-1.6.1-Setup.exe")
    smoke = json.loads(bundle.read("release/windows-smoke.json"))
    frozen = json.loads(bundle.read("dist/self-test.json"))
assert data[:2] == b"MZ"
assert hashlib.sha256(data).hexdigest() == manifest["sha256"]
assert all(smoke.get(key) is True for key in ("fresh_install", "upgrade", "license_preserved", "automatic_restart"))
assert smoke["version"] == frozen["version"] == manifest["latest_version"]
assert frozen["ok"] is True and frozen["frozen"] is True
out = Path("release")
out.mkdir(exist_ok=True)
(out / "GhostOptimizer-1.6.1-Setup.exe").write_bytes(data)
(out / "version.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Installer checksum and Windows installation tests verified.")
