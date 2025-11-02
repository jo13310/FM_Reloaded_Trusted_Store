#!/usr/bin/env python3
"""
Validation script for FM Reloaded Trusted Store
Checks mods.json for errors before accepting submissions.
"""

import json
import sys
import re
from pathlib import Path
from urllib.parse import urlparse

# Validation rules
REQUIRED_FIELDS = ["name", "version", "type", "author", "description", "homepage", "download_url"]
VALID_TYPES = ["ui", "graphics", "tactics", "database", "misc"]
VERSION_PATTERN = r'^\d+\.\d+\.\d+$'  # Semantic versioning
MAX_DESCRIPTION_LENGTH = 200


def validate_json_syntax(file_path):
    """Validate JSON syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data, None
    except json.JSONDecodeError as e:
        return False, None, f"JSON syntax error: {e}"


def validate_url(url):
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def validate_version(version):
    """Validate semantic versioning format."""
    return bool(re.match(VERSION_PATTERN, version))


def validate_mod_entry(mod, index):
    """Validate a single mod entry."""
    errors = []
    warnings = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in mod:
            errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Missing required field '{field}'")

    # Validate type
    if 'type' in mod and mod['type'] not in VALID_TYPES:
        errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Invalid type '{mod['type']}'. Must be one of: {', '.join(VALID_TYPES)}")

    # Validate version format
    if 'version' in mod and not validate_version(mod['version']):
        errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Invalid version format '{mod['version']}'. Must be semantic versioning (X.Y.Z)")

    # Validate URLs
    if 'homepage' in mod and not validate_url(mod['homepage']):
        errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Invalid homepage URL '{mod['homepage']}'")

    if 'download_url' in mod and not validate_url(mod['download_url']):
        errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Invalid download_url '{mod['download_url']}'")

    if 'changelog_url' in mod and mod['changelog_url'] and not validate_url(mod['changelog_url']):
        warnings.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Invalid changelog_url '{mod['changelog_url']}'")

    # Validate description length
    if 'description' in mod and len(mod['description']) > MAX_DESCRIPTION_LENGTH:
        warnings.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Description too long ({len(mod['description'])} chars, max {MAX_DESCRIPTION_LENGTH})")

    # Check for empty strings
    for field in REQUIRED_FIELDS:
        if field in mod and isinstance(mod[field], str) and not mod[field].strip():
            errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): Field '{field}' cannot be empty")

    # Validate dependencies and conflicts are arrays
    if 'dependencies' in mod and not isinstance(mod['dependencies'], list):
        errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): 'dependencies' must be an array")

    if 'conflicts' in mod and not isinstance(mod['conflicts'], list):
        errors.append(f"Mod #{index} ({mod.get('name', 'Unknown')}): 'conflicts' must be an array")

    return errors, warnings


def check_duplicates(mods):
    """Check for duplicate mod names."""
    errors = []
    names = {}

    for i, mod in enumerate(mods):
        name = mod.get('name', '')
        if name in names:
            errors.append(f"Duplicate mod name '{name}' found at indices {names[name]} and {i}")
        else:
            names[name] = i

    return errors


def validate_store_structure(data):
    """Validate overall store structure."""
    errors = []
    warnings = []

    # Check top-level fields
    if 'version' not in data:
        warnings.append("Missing 'version' field in store metadata")

    if 'mods' not in data:
        errors.append("Missing 'mods' array in store")
        return errors, warnings

    if not isinstance(data['mods'], list):
        errors.append("'mods' must be an array")
        return errors, warnings

    # Check mod_count matches
    if 'mod_count' in data and len(data['mods']) != data['mod_count']:
        warnings.append(f"mod_count ({data['mod_count']}) doesn't match actual count ({len(data['mods'])})")

    return errors, warnings


def main():
    """Main validation function."""
    print("FM Reloaded Trusted Store Validator")
    print("=" * 50)

    # Find mods.json
    file_path = Path(__file__).parent / "mods.json"

    if not file_path.exists():
        print(f"❌ Error: mods.json not found at {file_path}")
        return 1

    print(f"Validating: {file_path}")
    print()

    # Validate JSON syntax
    valid, data, error = validate_json_syntax(file_path)
    if not valid:
        print(f"❌ {error}")
        return 1

    print("✓ JSON syntax valid")

    # Validate store structure
    errors, warnings = validate_store_structure(data)

    # Validate each mod
    for i, mod in enumerate(data.get('mods', []), 1):
        mod_errors, mod_warnings = validate_mod_entry(mod, i)
        errors.extend(mod_errors)
        warnings.extend(mod_warnings)

    # Check for duplicates
    duplicate_errors = check_duplicates(data.get('mods', []))
    errors.extend(duplicate_errors)

    # Print results
    print()
    print("Validation Results:")
    print("-" * 50)

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")

    if not errors and not warnings:
        print("\n✅ All validations passed!")
        print(f"\nMods in store: {len(data.get('mods', []))}")
        return 0
    elif not errors:
        print("\n✅ No errors found (warnings can be ignored)")
        print(f"\nMods in store: {len(data.get('mods', []))}")
        return 0
    else:
        print(f"\n❌ Validation failed with {len(errors)} error(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
