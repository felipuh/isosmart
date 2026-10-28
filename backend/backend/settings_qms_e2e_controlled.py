"""Settings for the CONTROLLED_INTEGRATION_E2E of the QMS slice (local, disposable PostgreSQL).

Never usable outside an explicitly opted-in local run; not an AdminApps integration.
"""

import os

from .settings_postgres_integration import *  # noqa: F401,F403

if os.getenv("QMS_E2E_CONTROLLED_INTEGRATION") != "1":
    raise RuntimeError("QMS_E2E_CONTROLLED_INTEGRATION=1 is required for the controlled E2E settings")
if IS_PRODUCTION or DATABASES["default"]["HOST"] not in ("127.0.0.1", "localhost"):  # noqa: F405
    raise RuntimeError("controlled E2E settings refuse non-local or production environments")

REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_AUTHENTICATION_CLASSES": ["foundation.qms_e2e_controlled_auth.ControlledPrincipalAuthentication"],
    "DEFAULT_THROTTLE_CLASSES": [],
}
QMS_WRITE_ROLES = ("quality_manager",)
QMS_CAPA_CREATE_ENABLED = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
