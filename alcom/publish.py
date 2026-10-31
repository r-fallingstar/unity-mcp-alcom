"""Publish only complete, tested releases, then rebuild the VPM listing."""
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from build import build, PACKAGE, HERE


def gh(*args):
    return subprocess.check_output(["gh", *map(str, args)], text=True)


def releases(repository):
    return json.loads(gh("release", "list", "--repo", repository, "--limit", "1000", "--json", "tagName,isDraft"))


def main():
    repository = os.environ["GITHUB_REPOSITORY"]
    if repository != "r-fallingstar/unity-mcp-alcom":
        raise RuntimeError("Set the repository identity and site URL before publishing another fork")
    known = {r["tagName"]: r for r in releases(repository)}
    for channel in ("stable", "beta"):
        source = Path("_upstream") / channel
        version = json.loads((source / "MCPForUnity/package.json").read_text())["version"]
        tag = f"vpm-{version}"
        if tag in known and not known[tag]["isDraft"]:
            continue
        output = Path("dist") / version
        archive, manifest = build(source, output, repository)
        with tempfile.TemporaryDirectory() as temp:
            with zipfile.ZipFile(archive) as package:
                package.extractall(temp)
            server = Path(temp) / "Server~" / version
            subprocess.run(["uvx", "--from", str(server), "mcp-for-unity", "--help"], check=True,
                           env={**os.environ, "DISABLE_TELEMETRY": "true"})
        if tag not in known:
            args = ["release", "create", tag, "--repo", repository, "--target", os.environ["GITHUB_SHA"],
                    "--draft", "--title", f"Unity MCP {version} for ALCOM", "--notes",
                    f"VPM distribution of CoplayDev/unity-mcp {version}. Includes the matching local Python server.\n"
                    "Upstream commit is recorded in provenance.json. MIT license.\n"
                    "Requires Python >=3.10 and uv. This release does not install these prerequisites."]
            if "-" in version:
                args.append("--prerelease")
            gh(*args)
        gh("release", "upload", tag, archive, output / "vpm-manifest.json", output / "provenance.json",
           "--repo", repository, "--clobber")  # Only unpublished drafts reach this point.
        gh("release", "edit", tag, "--repo", repository, "--draft=false")
        known[tag] = {"tagName": tag, "isDraft": False}

    versions = {}
    for release in releases(repository):
        if release["isDraft"] or not release["tagName"].startswith("vpm-"):
            continue
        with tempfile.TemporaryDirectory() as temp:
            gh("release", "download", release["tagName"], "--repo", repository,
               "--pattern", "vpm-manifest.json", "--dir", temp)
            manifest = json.loads((Path(temp) / "vpm-manifest.json").read_text())
            versions[manifest["version"]] = manifest
    if not versions:
        raise RuntimeError("Refusing to deploy an empty repository")
    site = Path("site")
    site.mkdir(exist_ok=True)
    listing = {"name": "Unity MCP for ALCOM", "id": "io.github.r-fallingstar.unity-mcp-alcom",
               "url": "https://r-fallingstar.github.io/unity-mcp-alcom/index.json", "author": "r-fallingstar",
               "packages": {PACKAGE: {"versions": versions}}}
    (site / "index.json").write_text(json.dumps(listing, indent=2) + "\n", encoding="utf-8")
    (site / "index.html").write_text((HERE / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    (site / ".nojekyll").touch()


if __name__ == "__main__":
    main()
