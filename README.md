# FM Reloaded Trusted Store

Official curated mod repository for [FM Reloaded Mod Manager](https://github.com/jo13310/FM_Reloaded).

## Overview

This repository contains the `mods.json` index file that powers the mod store browser in FM Reloaded Mod Manager. Users can browse, search, and install mods directly from the app.

**Store URL**: `https://raw.githubusercontent.com/jo13310/FM_Reloaded_Trusted_Store/main/mods.json`

## For Users

### Browsing the Store

1. Open FM Reloaded Mod Manager
2. Go to the **Mod Store** tab
3. Browse available mods or use the search function
4. Click "Install Selected" to download and install

### Automatic Updates

The mod manager automatically checks for updates when you refresh your mod list. Mods with updates available show a "⬆" icon.

## For Mod Authors

### Submitting Your Mod

See the main repository's [STORE_SUBMISSION.md](https://github.com/jo13310/FM_Reloaded/blob/main/STORE_SUBMISSION.md) for detailed submission instructions.

**Quick submission**:
1. Open FM Reloaded Mod Manager
2. Click "Submit Mod" button (bottom right)
3. Fill in the form and submit

Your mod will be reviewed and added within 3-7 days.

### Requirements

- Public GitHub repository
- Valid `manifest.json` following FM Reloaded format
- At least one tagged release with `.zip` file
- Clear README with installation instructions
- Appropriate open-source license

## Store Format

### mods.json Structure

```json
{
  "version": "1.0.0",
  "last_updated": "2025-01-15T12:00:00Z",
  "mod_count": 42,
  "store_info": {
    "name": "FM Reloaded Trusted Store",
    "maintainer": "Your Name",
    "description": "Official curated mod repository",
    "url": "https://github.com/jo13310/FM_Reloaded_Trusted_Store"
  },
  "mods": [
    {
      "name": "Mod Name",
      "version": "1.0.0",
      "type": "ui|graphics|tactics|database|misc",
      "author": "Author Name",
      "description": "Brief description",
      "homepage": "https://github.com/author/mod",
      "download_url": "https://github.com/author/mod/releases/download/v1.0.0/mod.zip",
      "changelog_url": "https://github.com/author/mod/blob/main/CHANGELOG.md",
      "downloads": 0,
      "date_added": "2025-01-15",
      "last_updated": "2025-01-15",
      "dependencies": [],
      "conflicts": [],
      "compatibility": {
        "fm_version": "26.0.0",
        "min_loader_version": "0.5.0"
      }
    }
  ]
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Mod display name |
| `version` | string | Latest version (semantic versioning) |
| `type` | string | ui, graphics, tactics, database, or misc |
| `author` | string | Mod creator |
| `description` | string | 1-2 sentence summary (max 200 chars) |
| `homepage` | string | GitHub repository URL |
| `download_url` | string | Direct link to .zip release |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `changelog_url` | string | Link to changelog/release notes |
| `downloads` | number | Download count (maintained by admin) |
| `date_added` | string | Date added to store (YYYY-MM-DD) |
| `last_updated` | string | Last update date (YYYY-MM-DD) |
| `dependencies` | array | Required mods |
| `conflicts` | array | Incompatible mods |
| `compatibility` | object | Version requirements |

## Validation

Before submitting a PR, validate your changes:

```bash
python validate_mods.py
```

This checks:
- JSON syntax
- Required fields
- URL validity
- Version format
- Duplicate detection

## Maintenance

### Adding a Mod

1. Fork this repository
2. Add your mod entry to `mods.json` in the `mods` array
3. Increment `mod_count`
4. Update `last_updated` timestamp
5. Run `python validate_mods.py`
6. Submit a pull request

### Updating a Mod

1. Find your mod entry in `mods.json`
2. Update the `version` field
3. Update the `download_url` to the new release
4. Update `last_updated` timestamp
5. Optionally update `description` or other fields
6. Submit a PR

### Removing a Mod

Mods are rarely removed, but may be if:
- Author requests removal
- License violation discovered
- Mod becomes incompatible and unmaintained

## Statistics

- **Total Mods**: 2 (example entries)
- **Last Updated**: 2025-01-15
- **Store Version**: 1.0.0

## Support

- **Submissions**: Use the "Submit Mod" button in FM Reloaded
- **Issues**: [GitHub Issues](https://github.com/jo13310/FM_Reloaded_Trusted_Store/issues)
- **Discord**: [Join our server](#)

## License

The store index (`mods.json`) is licensed under CC0 1.0 Universal (Public Domain).

Individual mods retain their own licenses as specified in their repositories.

---

Maintained by **GerKo** for the FM Reloaded project.
