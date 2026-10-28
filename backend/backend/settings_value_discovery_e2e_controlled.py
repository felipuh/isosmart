"""Local-only settings for the controlled Value Discovery browser E2E.

The controlled principal and inference fixture require an explicit opt-in and
are rejected for production or non-local databases.  QMS mutation roles remain
at their normal default values.
"""

import os

from .settings_postgres_integration import *  # noqa: F401,F403


if os.getenv("VALUE_DISCOVERY_E2E_CONTROLLED_INTEGRATION") != "1":
    raise RuntimeError("VALUE_DISCOVERY_E2E_CONTROLLED_INTEGRATION=1 is required")
if IS_PRODUCTION or DATABASES["default"]["HOST"] not in ("127.0.0.1", "localhost"):  # noqa: F405
    raise RuntimeError("controlled E2E settings refuse non-local or production environments")

REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_AUTHENTICATION_CLASSES": ["foundation.controlled_e2e_auth.ControlledPrincipalAuthentication"],
    "DEFAULT_THROTTLE_CLASSES": [],
}
VALUE_DISCOVERY_PROVIDER = "e2e-controlled"
VALUE_DISCOVERY_ALLOW_CONTROLLED_PROVIDER = True
VALUE_DISCOVERY_E2E_CONTROLLED_INTEGRATION = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
