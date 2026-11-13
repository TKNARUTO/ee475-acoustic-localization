"""Read-only audit of the selected local release; never package, flash or publish.

Checks catalog/SHA coverage, the sole legacy template and matching ZIP, portable
Markdown destinations, known private paths/secrets, and firmware BUILD identities.
Optional JSON output must be outside the project. Supplied reference PDF/DOCX/PPTX
remain original-language artifacts; this is not a translation or accuracy check.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from urllib.parse import unquote, urlsplit
import zipfile

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("release_catalog_policy", Path(__file__).with_name("refresh_catalog.py"))
catalog = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(catalog)
ROOT = Path(__file__).resolve().parents[1]
HASH = re.compile(r"^[0-9a-fA-F]{64}$")
PRIVATE_PATH = re.compile(rb"(?i)[a-z]:[\\/]+Users[\\/]+33296(?:[\\/]|$)")
SECRET_CONTENT = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b"),
)
SECRET_NAMES = {"credentials.json", "service-account.json", "secrets.json", "token.json", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"}
REQUIRED_BUILDS = ("pico-standalone/firmware/BUILD.json", "esp32-link/gap_receiver/firmware/BUILD.json")


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value or any(c in value for c in "\x00\r\n"):
        return False
    p = PurePosixPath(value)
    return not p.is_absolute() and ".." not in p.parts and p.as_posix() == value and value != "."


def digest(path):
    return catalog.stable_hash(path)[0]


def without_code(text):
    """Remove fenced/inline code before Markdown-link inspection."""
    lines = []; fence = None
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1]:
                fence = None
            lines.append("")
        elif match:
            fence = (match[1][0], len(match[1])); lines.append("")
        else:
            lines.append(re.sub(r"(`+).*?\1", "", line))
    return "\n".join(lines)


def markdown_destinations(text):
    text = without_code(text)
    found = []
    # Walk balanced parentheses, including angle-wrapped paths and optional titles.
    # This handles ordinary filenames containing parentheses without a regex cutoff.
    for match in re.finditer(r"!?\[[^\]]*\]\(", text):
        begin = cursor = match.end(); depth = 1; angle = False; quote = None
        while cursor < len(text):
            char = text[cursor]
            if char == "\\":
                cursor += 2; continue
            if quote:
                if char == quote:
                    quote = None
            elif angle:
                if char == ">":
                    angle = False
            elif char == "<":
                angle = True
            elif char in {"\"", "'"} and cursor > begin and text[cursor - 1].isspace():
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    found.append(text[begin:cursor]); break
            cursor += 1
    found += re.findall(r"^ {0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", text, re.M)
    found += re.findall(r"\b(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", text, re.I)
    for raw in found:
        raw = raw.strip()
        if raw.startswith("<"):
            yield raw[1:raw.index(">")]
        else:
            # Optional Markdown link title, not part of the filesystem path.
            raw = re.sub(r"\s+[\"'][^\"']*[\"']\s*$", "", raw)
            yield re.sub(r"\\([ ()])", r"\1", raw)


def verify(root=ROOT):
    root = Path(root).resolve()
    errors = []; checks = {}; notes = []
    def fail(code, path, detail):
        errors.append({"code": code, "path": str(path), "detail": str(detail)})
    def scan(data, relative):
        if PRIVATE_PATH.search(data) or PRIVATE_PATH.search(data.replace(b"\x00", b"")):
            fail("private_path", relative, "Personal absolute Windows path detected; content omitted from report")
        if any(pattern.search(data) for pattern in SECRET_CONTENT):
            fail("secret_content", relative, "Credential/private-key pattern detected; value omitted from report")
        if PurePosixPath(relative).name.casefold() in SECRET_NAMES:
            fail("secret_filename", relative, "Credential filename is not a shareable release artifact")

    selected, skipped = catalog.selected_files(root)
    expected = set(selected) - {catalog.SUMS}
    actual = {}; sums = root / catalog.SUMS
    if not sums.is_file():
        fail("missing_checksums", catalog.SUMS, "Refresh catalog after all files are stable")
    else:
        for number, line in enumerate(sums.read_text(encoding="utf-8-sig").splitlines(), 1):
            match = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line)
            if not match or not safe_relative(match[2]):
                fail("invalid_checksum_line", catalog.SUMS, f"Line {number} is malformed or unsafe")
                continue
            name = match[2]
            if name in actual:
                fail("duplicate_checksum", name, "Duplicate entry")
            actual[name] = match[1].lower()
    for name in sorted(expected - set(actual)):
        fail("checksum_missing", name, "Selected file is not covered")
    for name in sorted(set(actual) - expected):
        fail("checksum_unselected", name, "Checksum includes an unselected file or itself")
    hashed = 0
    for relative in selected:
        path = root / relative
        if not path.is_file():
            fail("missing_selected", relative, "Expected selected/generated file is absent")
            continue
        if catalog.linked(path):
            fail("linked_file", relative, "Symlink/junction cannot be published")
            continue
        if relative != catalog.SUMS and relative in actual:
            try:
                if digest(path) != actual[relative]:
                    fail("hash_mismatch", relative, "Bytes differ from SHA256SUMS")
                hashed += 1
            except (OSError, RuntimeError) as exc:
                fail("hash_read_error", relative, type(exc).__name__)
        scan(path.read_bytes(), relative)
    checks["selected_files"] = len(selected)
    checks["hash_entries"] = len(actual)
    checks["files_hashed"] = hashed
    checks["excluded_counts"] = skipped

    # Ensure generator outputs are fresh as well as internally hashed. A stale
    # catalog and a freshly computed checksum must not pass together.
    try:
        plan = catalog.prepare(root)
        stale = [name for name, data in plan["content"].items()
                 if not (root / name).is_file() or (root / name).read_bytes() != data]
        checks["stale_generated_files"] = stale
        for name in stale:
            fail("stale_generated", name, "Run refresh_catalog.py after completing edits")
    except (OSError, RuntimeError, ValueError) as exc:
        fail("catalog_prepare_error", "tools/refresh_catalog.py", type(exc).__name__)

    legacy = root / "legacy"
    allowed = {PurePosixPath(catalog.FROZEN_DIR).name, PurePosixPath(catalog.FROZEN_ZIP).name}
    entries = {p.name for p in legacy.iterdir()} if legacy.is_dir() else set()
    if entries != allowed:
        fail("legacy_layout", "legacy", {"missing": sorted(allowed - entries), "unexpected": sorted(entries - allowed)})
    template = root / catalog.FROZEN_DIR
    archive = root / catalog.FROZEN_ZIP
    zip_checked = 0
    if template.is_dir() and archive.is_file() and not catalog.linked(template) and not catalog.linked(archive):
        template_files = {}
        for path in template.rglob("*"):
            rel = path.relative_to(template).as_posix()
            if catalog.linked(path):
                fail("legacy_link", rel, "Template must not contain links")
            elif path.is_file():
                template_files[rel] = path
        seen = set(); folded = set()
        try:
            with zipfile.ZipFile(archive) as z:
                prefix = template.name + "/"
                for item in z.infolist():
                    member = item.filename
                    if not member.startswith(prefix) or not safe_relative(member.rstrip("/")):
                        fail("zip_unsafe_member", catalog.FROZEN_ZIP, member); continue
                    if stat.S_ISLNK(item.external_attr >> 16):
                        fail("zip_symlink", catalog.FROZEN_ZIP, member); continue
                    tail = member[len(prefix):].rstrip("/")
                    if item.is_dir():
                        if tail and not (template / tail).is_dir():
                            fail("zip_extra_directory", catalog.FROZEN_ZIP, member)
                        continue
                    if tail in seen or tail.casefold() in folded:
                        fail("zip_duplicate_member", catalog.FROZEN_ZIP, member); continue
                    seen.add(tail); folded.add(tail.casefold())
                    if tail not in template_files:
                        fail("zip_extra_member", catalog.FROZEN_ZIP, member); continue
                    rel = catalog.FROZEN_DIR + "/" + tail
                    policy = catalog.exclude_reason(rel)
                    if policy:
                        fail("zip_unselected_private_member", member, policy)
                    target = template_files[tail]
                    if item.file_size != target.stat().st_size:
                        fail("zip_size_mismatch", member, "Template and ZIP size differ"); continue
                    # Never extract members. Reading only expected-size members
                    # avoids arbitrary path writes and unknown oversized payloads.
                    data = z.read(item)
                    if hashlib.sha256(data).hexdigest() != digest(target):
                        fail("zip_byte_mismatch", member, "Template and ZIP bytes differ")
                    scan(data, "ZIP:" + member)
                    zip_checked += 1
                for tail in sorted(set(template_files) - seen):
                    fail("zip_missing_member", tail, "Template file absent from ZIP")
        except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
            fail("zip_read_error", catalog.FROZEN_ZIP, type(exc).__name__)
    else:
        fail("missing_final_combo", "legacy", "Need the real final template directory and matching ZIP")
    checks["zip_files_compared"] = zip_checked

    link_count = 0
    for relative in selected:
        path = root / relative
        if path.suffix.casefold() != ".md" or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError:
            fail("markdown_encoding", relative, "Expected UTF-8 Markdown"); continue
        for destination in markdown_destinations(text):
            try:
                parts = urlsplit(destination)
            except ValueError:
                fail("markdown_url", relative, destination); continue
            if parts.scheme in {"http", "https", "mailto", "data"} or destination.startswith("//"):
                continue
            if parts.scheme or destination.startswith(("/", "\\")):
                fail("nonportable_link", relative, destination); continue
            raw = unquote(parts.path)
            if not raw:
                continue  # Fragment-only anchors are outside this path audit.
            target = (path.parent / raw).resolve()
            if not target.is_relative_to(root):
                fail("link_outside_release", relative, destination); continue
            name = target.relative_to(root).as_posix()
            link_count += 1
            if not target.exists():
                fail("broken_markdown_link", relative, destination)
            elif target.is_file() and name not in expected and name != catalog.SUMS:
                fail("link_to_unselected", relative, destination)
            elif target.is_dir() and not any(x.startswith(name + "/") for x in selected):
                fail("link_to_empty_unselected_directory", relative, destination)
    checks["relative_markdown_destinations_checked"] = link_count

    builds = []
    for relative in REQUIRED_BUILDS:
        path = root / relative
        result = {"path": relative, "source_files_checked": 0, "artifact_files_checked": 0}
        builds.append(result)
        if not path.is_file():
            fail("missing_build_identity", relative, "Current firmware needs BUILD.json"); continue
        try:
            record = json.loads(path.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError):
            fail("invalid_build_identity", relative, "Cannot parse JSON"); continue
        def verify_mapping(mapping, base, label):
            if not isinstance(mapping, dict):
                fail("invalid_build_mapping", relative, label); return
            for name, expected_hash in mapping.items():
                if not safe_relative(name) or not isinstance(expected_hash, str) or not HASH.fullmatch(expected_hash):
                    fail("invalid_build_entry", relative, label); continue
                file = base / name
                full = file.relative_to(root).as_posix()
                if full not in expected or not file.is_file():
                    fail("build_file_missing", relative, full); continue
                if digest(file) != expected_hash.lower():
                    fail("build_hash_mismatch", relative, full)
                result[label + "_files_checked"] += 1
        sources = record.get("source_sha256")
        if not sources:
            fail("missing_build_sources", relative, "Source hashes are required")
        verify_mapping(sources, path.parent.parent, "source")
        if "files" in record:
            verify_mapping(record["files"], path.parent, "artifact")
        distributed = record.get("image_distributed", "image" in record)
        if distributed:
            verify_mapping({record.get("image", ""): record.get("image_sha256", "")}, path.parent, "artifact")
        elif record.get("image_distributed") is False:
            if not isinstance(record.get("image_sha256"), str) or not HASH.fullmatch(record["image_sha256"]):
                fail("invalid_private_image_identity", relative, "Retained deployment SHA256 is required")
            result["deployment_image_distributed"] = False
            result["private_image_bytes_verified"] = False
            notes.append("Undistributed deployment image: source hashes checked; private binary not present or reverified by this release audit.")
    checks["firmware_builds"] = builds
    return {"schema": "ee475.release-verification.v1", "passed": not errors,
            "read_only": True, "hardware_access": False, "network_access": False,
            "checks": checks, "errors": errors, "notes": notes,
            "limitations": ["Markdown destination paths are checked; fragment IDs and external URLs are not fetched.",
                            "Known path/credential patterns are checked; this is not an exhaustive secret detector.",
                            "Source/artifact identity does not establish physical accuracy, realtime deadlines or build reproducibility.",
                            "Supplied PDF/DOCX/PPTX references retain their original language."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Project root (defaults to this script's parent project)")
    parser.add_argument("--output", type=Path, help="Optional JSON output outside the project; stdout always receives JSON")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.output and args.output.resolve().is_relative_to(root):
        parser.error("--output must be outside the project")
    try:
        result = verify(root)
    except (OSError, ValueError, RuntimeError) as exc:
        result = {"schema": "ee475.release-verification.v1", "passed": False, "read_only": True,
                  "errors": [{"code": "audit_error", "detail": type(exc).__name__}]}
    serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target = args.output.resolve(); target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
