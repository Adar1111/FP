# Development setup

This scaffold has no runnable server or correction pipeline yet.

Open the repository root in VS Code. Create a local virtual environment and select it as the interpreter.

WSL/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Do not share a virtual environment between Windows and WSL or between developers.

requirements.txt is currently empty; add dependencies when components are implemented. The existing src/ai/client.py separately needs openai and python-dotenv if used. Do not import or call it during ordinary skeleton checks. Credentials stay in local environment configuration.

No database, cloud account, or API key is required for the skeleton.
