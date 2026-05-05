# envguard

> Lightweight utility to validate and audit `.env` files against a defined schema before app startup.

---

## Installation

```bash
pip install envguard
```

Or with Poetry:

```bash
poetry add envguard
```

---

## Usage

Define a schema and validate your `.env` file before your application starts.

**`.env`**
```env
DATABASE_URL=postgres://localhost/mydb
PORT=8080
DEBUG=true
```

**`main.py`**
```python
from envguard import EnvGuard

guard = EnvGuard(schema={
    "DATABASE_URL": {"type": str, "required": True},
    "PORT": {"type": int, "required": True},
    "DEBUG": {"type": bool, "default": False},
    "SECRET_KEY": {"type": str, "required": True},
})

guard.validate()  # Raises EnvValidationError if validation fails
```

**Output on failure:**
```
EnvValidationError: Missing required variable(s): SECRET_KEY
```

You can also audit without raising an error:

```python
report = guard.audit()
print(report.summary())
```

---

## Features

- ✅ Required field enforcement
- 🔍 Type checking and coercion
- 🛡️ Default value support
- 📋 Audit mode for non-blocking reports

---

## License

This project is licensed under the [MIT License](LICENSE).