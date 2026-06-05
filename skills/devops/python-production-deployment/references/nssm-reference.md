# NSSM — Non-Sucking Service Manager Reference

> Download: https://nssm.cc/download
> Extract, copy `win64\nssm.exe` to `C:\Windows\System32\`

## Quick Reference

```batch
:: Install a service
nssm install <ServiceName> "<path\to\python.exe>"

:: Set working directory
nssm set <ServiceName> AppDirectory "<path\to\project>"

:: Set command-line arguments
nssm set <ServiceName> AppParameters "main.py"

:: Set environment variables
nssm set <ServiceName> AppEnvironmentExtra "KEY=value"
nssm set <ServiceName> AppEnvironmentExtra+ "KEY2=value2"

:: Set startup type (auto/manual/disabled)
nssm set <ServiceName> Start SERVICE_AUTO_START

:: Set description
nssm set <ServiceName> Description "Service description text"

:: Set display name
nssm set <ServiceName> DisplayName "Friendly Name"

:: Set stdout/stderr log files
nssm set <ServiceName> AppStdout "C:\path\to\logs\stdout.log"
nssm set <ServiceName> AppStderr "C:\path\to\logs\stderr.log"

:: Rotate logs (optional)
nssm set <ServiceName> AppStdoutCreationDisposition 4
nssm set <ServiceName> AppRotateFiles 1
nssm set <ServiceName> AppRotateSeconds 86400
nssm set <ServiceName> AppRotateBytes 10485760

:: View current configuration
nssm get <ServiceName> Application

:: Edit in GUI
nssm edit <ServiceName>

:: Remove service
nssm remove <ServiceName> confirm
```

## Common Commands

```batch
:: Start/stop service
net start <ServiceName>
net stop <ServiceName>

:: Check status
sc query <ServiceName>

:: List all services
sc query state= all
```

## Python Flask Example

```batch
nssm install FlaskApp "C:\project\venv\Scripts\python.exe"
nssm set FlaskApp AppDirectory "C:\project"
nssm set FlaskApp AppParameters "api_server.py"
nssm set FlaskApp AppEnvironmentExtra "PORT=5000"
nssm set FlaskApp AppEnvironmentExtra+ "FLASK_ENV=production"
nssm set FlaskApp Start SERVICE_AUTO_START
nssm set FlaskApp AppStdout "C:\project\logs\stdout.log"
nssm set FlaskApp AppStderr "C:\project\logs\stderr.log"
nssm set FlaskApp AppRotateFiles 1
net start FlaskApp
```

## Troubleshooting

### Service won't start
- Check Python path exists: `dir "C:\path\to\python.exe"`
- Check AppDirectory exists: `dir "C:\path\to\project"`
- View GUI for errors: `nssm edit <ServiceName>`
- Check Windows Event Viewer for NSSM errors

### Environment variables not loading
- Use `AppEnvironmentExtra` (not `AppEnvironment`)
- One variable per `set` command, or use `+` to append

### Log files not created
- Ensure log directory exists
- Check file permissions
- Use absolute paths
