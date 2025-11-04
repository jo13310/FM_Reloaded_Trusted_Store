#!/usr/bin/env python3
"""Validation script for FM Reloaded Trusted Store."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# Validation rules
REQUIRED_FIELDS = ["name", "version", "type", "author", "description", "homepage", "download"]
VALID_TYPES = [
    "ui",
    "bundle",
    "camera",
    "skins",
    "graphics",
    "tactics",
    "database",
    "ruleset",
    "editor-data",
    "audio",
    "misc",
]
VERSION_PATTERN = r"^\d+\.\d+\.\d+$"  # Semantic versioning
MAX_DESCRIPTION_LENGTH = 200
GITHUB_REPO_PATTERN = r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
DEFAULT_TAG_PREFIX = "v"
USER_AGENT = "FMReloadedTrustedStoreValidator/1.0"


def load_json(file_path: Path) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Load JSON content from file."""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            return True, json.load(handle), None
    except json.JSONDecodeError as exc:
        return False, None, f"JSON syntax error: {exc}"
    except OSError as exc:
        return False, None, f"Unable to read file: {exc}"


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return bool(result.scheme and result.netloc)
    except ValueError:
        return False


def validate_version(version: str) -> bool:
    """Validate semantic versioning format."""
    return bool(re.match(VERSION_PATTERN, version))


def validate_download_block(mod: Dict[str, Any], index: int) -> Tuple[List[str], List[str]]:
    """Validate the download configuration for a mod."""
    errors: List[str] = []
    warnings: List[str] = []
    download = mod.get("download")

    if not isinstance(download, dict):
        errors.append(
            f"Mod #{index} ({mod.get('name', 'Unknown')}): 'download' must be an object"
        )
        return errors, warnings

    download_type = download.get("type")
    if download_type not in {"github_release", "direct"}:
        errors.append(
            f"Mod #{index} ({mod.get('name', 'Unknown')}): Unsupported download type "
            f"'{download_type}'. Supported types: github_release, direct"
        )
        return errors, warnings

    if download_type == "github_release":
        repo = download.get("repo")
        if not repo or not re.match(GITHUB_REPO_PATTERN, repo):
            errors.append(
                f"Mod #{index} ({mod.get('name', 'Unknown')}): download.repo must look like "
                "owner/repository"
            )

        asset = download.get("asset")
        if not asset or not isinstance(asset, str):
            errors.append(
                f"Mod #{index} ({mod.get('name', 'Unknown')}): download.asset is required "
                "for github_release downloads"
            )

        latest_flag = download.get("latest")
        if latest_flag not in (None, False, True):
            errors.append(
                f"Mod #{index} ({mod.get('name', 'Unknown')}): download.latest must be boolean when provided"
            )

        if not latest_flag:
            tag_override = download.get("tag")
            if tag_override and not isinstance(tag_override, str):
                errors.append(
                    f"Mod #{index} ({mod.get('name', 'Unknown')}): download.tag must be a string"
                )

            tag_prefix = download.get("tag_prefix", DEFAULT_TAG_PREFIX)
            if not isinstance(tag_prefix, str):
                errors.append(
                    f"Mod #{index} ({mod.get('name', 'Unknown')}): download.tag_prefix must be a string"
                )

    if download_type == "direct":
        url = download.get("url")
        if not url or not isinstance(url, str):
            errors.append(
                f"Mod #{index} ({mod.get('name', 'Unknown')}): download.url is required for direct downloads"
            )
        elif not validate_url(url):
            errors.append(
                f"Mod #{index} ({mod.get('name', 'Unknown')}): download.url must be a valid URL"
            )

    return errors, warnings


def validate_mod_entry(mod: Dict[str, Any], index: int) -> Tuple[List[str], List[str]]:
    """Validate a single mod entry."""
    errors: List[str] = []
    warnings: List[str] = []
    mod_name = mod.get("name", "Unknown")

    for field in REQUIRED_FIELDS:
        if field not in mod:
            errors.append(f"Mod #{index} ({mod_name}): Missing required field '{field}'")

    if "type" in mod:
        mod_type = mod["type"]
        if not isinstance(mod_type, str):
            errors.append(
                f"Mod #{index} ({mod_name}): Invalid type '{mod_type}'. Must be a string"
            )
        elif mod_type.lower() not in VALID_TYPES:
            errors.append(
                f"Mod #{index} ({mod_name}): Invalid type '{mod_type}'. "
                f"Must be one of: {', '.join(VALID_TYPES)}"
            )

    if "version" in mod and not validate_version(mod["version"]):
        errors.append(
            f"Mod #{index} ({mod_name}): Invalid version format '{mod['version']}'. "
            "Must be semantic versioning (X.Y.Z)"
        )

    if "homepage" in mod and not validate_url(mod["homepage"]):
        errors.append(
            f"Mod #{index} ({mod_name}): Invalid homepage URL '{mod['homepage']}'"
        )

    if "changelog_url" in mod and mod["changelog_url"]:
        if not validate_url(mod["changelog_url"]):
            warnings.append(
                f"Mod #{index} ({mod_name}): Invalid changelog_url '{mod['changelog_url']}'"
            )

    if "download_url" in mod:
        errors.append(
            f"Mod #{index} ({mod_name}): download_url is deprecated; "
            "use the 'download' object instead"
        )

    if "description" in mod and len(mod["description"]) > MAX_DESCRIPTION_LENGTH:
        warnings.append(
            f"Mod #{index} ({mod_name}): Description too long "
            f"({len(mod['description'])} characters, max {MAX_DESCRIPTION_LENGTH})"
        )

    for field in REQUIRED_FIELDS:
        value = mod.get(field)
        if isinstance(value, str) and not value.strip():
            errors.append(
                f"Mod #{index} ({mod_name}): Field '{field}' cannot be empty"
            )

    if "dependencies" in mod and not isinstance(mod["dependencies"], list):
        errors.append(
            f"Mod #{index} ({mod_name}): 'dependencies' must be an array"
        )

    if "conflicts" in mod and not isinstance(mod["conflicts"], list):
        errors.append(
            f"Mod #{index} ({mod_name}): 'conflicts' must be an array"
        )

    if "install_notes" in mod and not isinstance(mod["install_notes"], str):
        errors.append(
            f"Mod #{index} ({mod_name}): 'install_notes' must be a string"
        )

    download_errors, download_warnings = validate_download_block(mod, index)
    errors.extend(download_errors)
    warnings.extend(download_warnings)

    download_info = mod.get("download") if isinstance(mod.get("download"), dict) else None
    asset_name = ""
    if download_info:
        asset_name = str(download_info.get("asset") or "")

    manifest_url = mod.get("manifest_url")
    if manifest_url:
        if not validate_url(manifest_url):
            errors.append(
                f"Mod #{index} ({mod_name}): Invalid manifest_url '{manifest_url}'"
            )
    if asset_name and not asset_name.lower().endswith(".zip") and not manifest_url:
        errors.append(
            f"Mod #{index} ({mod_name}): Non-zip release assets require a valid manifest_url"
        )

    return errors, warnings


def check_duplicates(mods: Iterable[Dict[str, Any]]) -> List[str]:
    """Check for duplicate mod names."""
    errors: List[str] = []
    names: Dict[str, int] = {}

    for index, mod in enumerate(mods):
        name = mod.get("name", "")
        if name in names:
            errors.append(
                f"Duplicate mod name '{name}' found at indices {names[name]} and {index}"
            )
        else:
            names[name] = index

    return errors


def validate_store_structure(data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Validate overall store structure."""
    errors: List[str] = []
    warnings: List[str] = []

    if "mods" not in data:
        errors.append("Missing 'mods' array in store")
        return errors, warnings

    if not isinstance(data["mods"], list):
        errors.append("'mods' must be an array")
        return errors, warnings

    if "version" not in data:
        warnings.append("Missing 'version' field in store metadata")

    if "mod_count" in data and len(data["mods"]) != data["mod_count"]:
        warnings.append(
            f"mod_count ({data['mod_count']}) does not match actual count "
            f"({len(data['mods'])})"
        )

    return errors, warnings


def github_api_get(url: str, token: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Call the GitHub REST API and return the JSON payload."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=10) as response:
            return json.load(response), None
    except HTTPError as exc:
        payload = exc.read().decode("utf-8", "replace")
        if exc.code == 404:
            return None, "Not found"
        return None, f"HTTP {exc.code}: {payload or exc.reason}"
    except URLError as exc:
        return None, f"Network error: {exc.reason}"


def normalise_tag(tag: str, prefix: str) -> str:
    """Remove a prefix from a tag if present."""
    if prefix and tag.startswith(prefix):
        return tag[len(prefix) :]
    return tag


def verify_github_release(
    mod: Dict[str, Any],
    download: Dict[str, Any],
    index: int,
    token: Optional[str],
) -> Tuple[List[str], List[str]]:
    """Verify GitHub release information for a mod."""
    errors: List[str] = []
    warnings: List[str] = []

    repo = download["repo"]
    asset_name = download["asset"]
    tag_prefix = download.get("tag_prefix", DEFAULT_TAG_PREFIX)
    store_version = mod["version"]
    use_latest = bool(download.get("latest"))
    tag_name = download.get("tag") or f"{tag_prefix}{store_version}"

    if use_latest:
        release_url = f"https://api.github.com/repos/{repo}/releases/latest"
        release, error = github_api_get(release_url, token)
        if error:
            errors.append(
                f"Mod #{index} ({mod['name']}): unable to fetch latest release for {repo} "
                f"({error})"
            )
            return errors, warnings
        # For messaging/version comparison
        tag_name = release.get("tag_name", tag_name)
    else:
        release_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag_name}"
        release, error = github_api_get(release_url, token)
        if error:
            errors.append(
                f"Mod #{index} ({mod['name']}): unable to fetch release '{tag_name}' for {repo} "
                f"({error})"
            )
            return errors, warnings

    assets = release.get("assets", [])
    asset_names = {asset.get("name") for asset in assets}
    if asset_name not in asset_names:
        errors.append(
            f"Mod #{index} ({mod['name']}): asset '{asset_name}' not found in release {tag_name}"
        )
    else:
        asset = next(asset for asset in assets if asset.get("name") == asset_name)
        if not asset.get("browser_download_url"):
            warnings.append(
                f"Mod #{index} ({mod['name']}): asset '{asset_name}' is missing download URL"
            )

    if use_latest:
        latest_release = release
        latest_error = None
    else:
        latest_url = f"https://api.github.com/repos/{repo}/releases/latest"
        latest_release, latest_error = github_api_get(latest_url, token)
        if latest_error:
            warnings.append(
                f"Mod #{index} ({mod['name']}): unable to determine latest release "
                f"({latest_error})"
            )
            return errors, warnings

    latest_tag = latest_release.get("tag_name", "")
    latest_version = normalise_tag(latest_tag, tag_prefix)

    if latest_version and latest_version != store_version:
        warnings.append(
            f"Mod #{index} ({mod['name']}): store version {store_version} does not match "
            f"latest release tag {latest_tag}"
        )

    return errors, warnings


def verify_downloads(mods: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """Verify remote download metadata."""
    errors: List[str] = []
    warnings: List[str] = []
    token = os.getenv("GITHUB_TOKEN")

    for index, mod in enumerate(mods, start=1):
        download = mod.get("download")
        if not isinstance(download, dict):
            continue
        download_type = download.get("type")
        if download_type == "github_release":
            mod_errors, mod_warnings = verify_github_release(mod, download, index, token)
            errors.extend(mod_errors)
            warnings.extend(mod_warnings)

    return errors, warnings


def format_results(label: str, messages: Iterable[str]) -> None:
    """Display a list of messages with a heading."""
    messages = list(messages)
    if not messages:
        return
    print(f"\n{label} ({len(messages)}):")
    for message in messages:
        print(f"  - {message}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate FM Reloaded Trusted Store metadata."
    )
    parser.add_argument(
        "--mods-file",
        type=Path,
        default=Path("mods.json"),
        help="Path to mods.json (default: mods.json in the same directory)",
    )
    parser.add_argument(
        "--verify-downloads",
        action="store_true",
        help="Verify remote release metadata (requires network access)",
    )
    args = parser.parse_args()

    mods_path = args.mods_file
    if not mods_path.is_absolute():
        mods_path = Path(__file__).parent / mods_path

    print("FM Reloaded Trusted Store Validator")
    print("=" * 50)
    print(f"Validating: {mods_path}\n")

    if not mods_path.exists():
        print(f"ERROR: mods.json not found at {mods_path}")
        return 1

    success, data, error = load_json(mods_path)
    if not success or data is None:
        print(f"ERROR: {error}")
        return 1

    print("JSON syntax: OK")

    errors, warnings = validate_store_structure(data)

    for index, mod in enumerate(data.get("mods", []), start=1):
        mod_errors, mod_warnings = validate_mod_entry(mod, index)
        errors.extend(mod_errors)
        warnings.extend(mod_warnings)

    errors.extend(check_duplicates(data.get("mods", [])))

    if args.verify_downloads:
        remote_errors, remote_warnings = verify_downloads(data.get("mods", []))
        errors.extend(remote_errors)
        warnings.extend(remote_warnings)

    print("\nValidation Results")
    print("-" * 50)

    format_results("ERRORS", errors)
    format_results("WARNINGS", warnings)

    if errors:
        print(f"\nValidation failed with {len(errors)} error(s)")
        return 1

    if warnings:
        print("\nNo errors found (warnings can be reviewed)")
    else:
        print("\nAll validations passed")

    print(f"\nMods in store: {len(data.get('mods', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
