#!/usr/bin/env python3
"""
Validate ExtensionAllowlist.yaml file.

Checks for:
- Duplicate keys in ExtensionAllowlist
- Conflicts between top-level keys and dotted keys (e.g., 'microsoft' vs 'microsoft.subapp')
"""
import re
import sys
from pathlib import Path


def parse_extension_allowlist(file_path: Path) -> tuple[dict[str, bool], list[str]]:
    """
    Parse ExtensionAllowlist.yaml file manually without external dependencies.

    Args:
        file_path: Path to the ExtensionAllowlist.yaml file

    Returns:
        Tuple of (dictionary of extension keys and their values, list of duplicate keys)

    Raises:
        ValueError: If file structure is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError("ExtensionAllowlist.yaml not found")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    extensions: dict[str, bool] = {}
    seen_keys: dict[str, int] = {}
    duplicates: list[str] = []
    in_extension_allowlist = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue

        # Check if we're entering ExtensionAllowlist section
        if stripped == 'ExtensionAllowlist:':
            in_extension_allowlist = True
            continue

        # If we're in the ExtensionAllowlist section, parse key-value pairs
        if in_extension_allowlist:
            # Match indented lines (4 spaces) with key: value pattern
            match = re.match(r'^    ([^:]+):\s*(.+)$', line)
            if match:
                key = match.group(1).strip()
                value_str = match.group(2).strip()
                # Convert string to boolean
                value = value_str.lower() in ('true', 'yes', '1')
                
                # Track duplicates during parsing
                if key in seen_keys:
                    if key not in duplicates:
                        duplicates.append(key)
                    seen_keys[key] += 1
                else:
                    seen_keys[key] = 1
                    extensions[key] = value
            elif line.strip() and not line.startswith(' '):
                # If we encounter a non-indented line that's not empty/comment,
                # we've left the ExtensionAllowlist section
                break

    if not extensions and not duplicates:
        raise ValueError("ExtensionAllowlist section not found or empty")

    return extensions, duplicates


def validate_extension_allowlist(yaml_path: Path) -> int:
    """
    Validate the ExtensionAllowlist.yaml file.

    Args:
        yaml_path: Path to the ExtensionAllowlist.yaml file

    Returns:
        0 if validation passes, 1 if validation fails
    """
    try:
        extensions, duplicates = parse_extension_allowlist(yaml_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Check for duplicates (detected during parsing)
    if duplicates:
        print("Error: Duplicate keys found in ExtensionAllowlist:")
        for dup in duplicates:
            print(f"  - {dup}")
        return 1

    # Get all keys without dots (top-level)
    top_level_keys = [key for key in extensions.keys() if '.' not in key]

    # Check if any key with a dot starts with a top-level key
    conflicts: list[str] = []
    for key in extensions.keys():
        if '.' in key:
            prefix = key.split('.')[0]
            if prefix in top_level_keys:
                conflicts.append(f"{key} conflicts with top-level key {prefix}")

    if conflicts:
        print("Error: Keys with dots conflict with existing top-level keys:")
        for conflict in conflicts:
            print(f"  - {conflict}")
        return 1

    print("ExtensionAllowlist.yaml validation passed")
    return 0


if __name__ == '__main__':
    yaml_path = Path("ExtensionAllowlist.yaml")
    sys.exit(validate_extension_allowlist(yaml_path))

