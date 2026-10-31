"""Build a deterministic VPM archive from an unmodified upstream checkout."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

PACKAGE = "com.coplaydev.unity-mcp"
HERE = Path(__file__).resolve().parent


def python_version(version):
    match = re.fullmatch(r"(\d+\.\d+\.\d+)(?:-(alpha|beta|rc)\.(\d+))?", version)
    if not match:
        raise ValueError(f"Unsupported upstream version: {version!r}")
    base, label, number = match.groups()
    return base + ({"alpha": "a", "beta": "b", "rc": "rc"}[label] + number if label else "")


def build(source, output, repository):
    source, output = Path(source).resolve(), Path(output).resolve()
    manifest = json.loads((source / "MCPForUnity/package.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    pep440 = python_version(version)
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        shutil.copytree(source / "MCPForUnity", stage / "MCPForUnity")
        subprocess.run(["git", "apply", "--check", str(HERE / "bundled-server.patch")], cwd=stage, check=True)
        subprocess.run(["git", "apply", str(HERE / "bundled-server.patch")], cwd=stage, check=True)
        root = stage / "MCPForUnity"
        server = root / "Server~" / version
        shutil.copytree(source / "Server/src", server / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
        for name in ("pyproject.toml", "README.md"):
            shutil.copy2(source / "Server" / name, server / name)
        shutil.copy2(source / "LICENSE", server / "LICENSE")
        project = (server / "pyproject.toml").read_text(encoding="utf-8")
        project, count = re.subn(r'(?m)^version = "[^"\n]+"$', f'version = "{pep440}"', project, count=1)
        if count != 1:
            raise ValueError("Upstream Python version field changed")
        (server / "pyproject.toml").write_text(project, encoding="utf-8")
        shutil.copy2(source / "LICENSE", root / "LICENSE")
        manifest["displayName"] += " (ALCOM)"
        manifest["vpmDependencies"] = {}
        manifest["documentationUrl"] = f"https://github.com/{repository}#readme"
        provenance = {"upstream": "CoplayDev/unity-mcp", "commit": revision, "version": version,
                      "serverVersion": pep440, "overlay": repository}
        (root / "alcom-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        (root / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        archive = output / f"{PACKAGE}-{version}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as package:
            for path in sorted(root.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    info = zipfile.ZipInfo(path.relative_to(root).as_posix(), (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    package.writestr(info, path.read_bytes(), compresslevel=9)
        manifest["url"] = f"https://github.com/{repository}/releases/download/vpm-{version}/{archive.name}"
        manifest["zipSHA256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        (output / "vpm-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return archive, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repository", default="r-fallingstar/unity-mcp-alcom")
    args = parser.parse_args()
    archive, manifest = build(args.source, args.output, args.repository)
    print(f"Built {archive}: {manifest['zipSHA256']}")
