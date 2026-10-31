import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import build, python_version


class PackagingTests(unittest.TestCase):
    def test_version_conversion_and_rejection(self):
        self.assertEqual(python_version("10.3.1-beta.11"), "10.3.1b11")
        self.assertEqual(python_version("10.3.0"), "10.3.0")
        with self.assertRaises(ValueError):
            python_version("../../escape")

    def test_real_archive_and_determinism(self):
        source = Path("_upstream/beta")
        if not source.is_dir():
            self.skipTest("Provide a clean upstream checkout at _upstream/beta")
        before = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"])
        with tempfile.TemporaryDirectory() as temp:
            archive, manifest = build(source, Path(temp) / "one", "r-fallingstar/unity-mcp-alcom")
            second, _ = build(source, Path(temp) / "two", "r-fallingstar/unity-mcp-alcom")
            self.assertEqual(archive.read_bytes(), second.read_bytes())
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), manifest["zipSHA256"])
            with zipfile.ZipFile(archive) as package:
                names = package.namelist()
                self.assertIn("package.json", names)
                server = f"Server~/{manifest['version']}/"
                self.assertIn(server + "src/main.py", names)
                self.assertIn(f'version = "{python_version(manifest["version"])}"', package.read(server + "pyproject.toml").decode())
                meta = "Editor/Helpers/AssetPathUtility.cs.meta"
                self.assertEqual(package.read(meta), (source / "MCPForUnity" / meta).read_bytes())
                self.assertEqual(json.loads(package.read("package.json"))["name"], manifest["name"])
        self.assertEqual(before, subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"]))


if __name__ == "__main__":
    unittest.main()
