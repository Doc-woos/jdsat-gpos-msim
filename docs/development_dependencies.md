# Development Dependencies

## Preferred GamePlanOS Consumption Path

This standalone repo should prefer an editable install of the GamePlanOS reference repo during development and CI.

Current reality:

- the editable install is still useful for shared substrate packages such as `gameplan.engine` and `gameplan.graph`
- the previously referenced shared manpower package path, `gameplan.domains.manpower`, is not present in the current checkout at `C:\dev\jdsat-gameplan-os`
- the repo therefore currently runs with app-local manpower logic in `backend/domain/*`

Preferred bootstrap command:

```powershell
npm run deps:bootstrap
```

Direct install command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_gameplan_editable.ps1
```

That installs `C:\dev\jdsat-gameplan-os` into the current Python environment in editable mode for the shared GamePlanOS packages that are actually present.

## Fallback Path

If an editable install is not available, set:

```text
GAMEPLAN_SRC=C:\dev\jdsat-gameplan-os
```

The source-path shim remains a fallback for local development, not the primary dependency strategy.

## Why This Split Exists

Editable install is preferred because it:

- exercises the shared substrate boundary more honestly
- reduces dependence on ad hoc `sys.path` mutation
- is a closer match for CI and future packaging

The fallback shim remains useful when:

- the external repo is present locally but not installed yet
- a contributor needs a quick local bootstrap
- package installation is temporarily blocked

## Verification

This environment was validated with the fallback path disabled. Preferred verification command:

```powershell
npm run deps:verify-gameplan
```

Contributor validation command:

```powershell
npm run validate
```

Equivalent raw command:

```powershell
Remove-Item Env:GAMEPLAN_SRC -ErrorAction SilentlyContinue
python -m pytest tests -q
```

Result in the current stabilized environment: `87 passed`
