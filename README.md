# eazyBI CLI Automation Module

A Python wrapper designed to automate interactions with the official **eazyBI CLI** tool. This module allows you to programmatically manage, filter, and extract eazyBI accounts, source applications, reports, and dashboard definitions into structured Python dictionaries (JSON compatible).

It runs seamlessly in the background and suppresses terminal pop-up windows on Windows environments.

## 📋 Features

- **Automated Authentication:** Handles the OAuth2 login workflow on initialization.
- **Background Execution:** Commands run silently without annoying console pop-ups on Windows (`CREATE_NO_WINDOW`).
- **Data Parsing:** Converts raw text tables output by the eazyBI CLI into clean, manageable `list[dict]` formats.
- **Bulk Extraction:** Fetch all entity definitions (Sources, Reports, Dashboards) grouped by account with a single method call.
- **Progress Tracking:** Built-in console percentage indicator for long-running extractions.

## 🛠️ Prerequisites

Before using this module, ensure you have the official **eazyBI CLI** installed and accessible in your system's PATH.

- **macOS / Linux:**
  ```bash
  curl -fsSL https://eazybi.com | bash
  ```
- **Windows (PowerShell):**
  ```powershell
  irm https://eazybi.com-ps1 | iex
  ```

*For more setup details, refer to the official [eazyBI CLI Documentation](https://eazybi.com).*

## 🚀 Installation

Since this module relies entirely on the Python Standard Library, no external dependencies are needed. Simply copy `eazybi_cli.py` into your project directory.

```bash
git clone https://github.com
```

## 💻 Usage Example

Here is a quick guide on how to initialize the class and backup all definitions from your accounts:

```python
from eazybi_cli import EazyBiCLI

# 1. Initialize and authenticate (opens browser on first run if needed)
# Leave blank for default profile, or specify your Private eazyBI / Jira URL
instance = EazyBiCLI(eazybi_url="https://example.com")

# 2. Get all accounts filtered by a specific keyword
my_accounts = instance.get_accounts(keyword="Production")
print(f"Found {len(my_accounts)} matching accounts.")

# 3. Download every single definition (Sources, Reports, Dashboards) 
# This returns a full JSON-structured list
all_data = instance.get_all_def(keyword="Production")

# 4. Save your definitions to a local backup file
import json
with open("eazybi_backup.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print("Backup completed successfully!")
```

## 🔧 Available Methods

| Method | Description |
| :--- | :--- |
| `get_accounts(keyword="")` | Lists available eazyBI accounts, optionally filtered by name. |
| `get_sources(account_id)` | Lists all source applications tied to a specific account. |
| `get_source_def(account_id, source_id)` | Exports the full JSON definition layout of a source. |
| `get_reports(account_id)` | Lists all reports inside an account. |
| `get_report_def(account_id, report_id)` | Exports the MDX and layout schema definition of a report. |
| `get_dashboards(account_id)` | Lists all dashboards inside an account. |
| `get_all_def(keyword="")` | High-level wrapper that pulls every definition from matching accounts automatically. |

## 🤝 Contributing

Contributions are welcome! If you find a bug or have a feature request, please submit a pull request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
