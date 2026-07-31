"""HTTP Basic Auth pour les routes admin."""
import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if not ADMIN_PASSWORD:
        return credentials.username
    is_user = secrets.compare_digest(credentials.username.encode(), ADMIN_USER.encode())
    is_pass = secrets.compare_digest(credentials.password.encode(), ADMIN_PASSWORD.encode())
    if not (is_user and is_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acces refuse",
            headers={"WWW-Authenticate": "Basic realm=\"CyberScan Admin\""},
        )
    return credentials.username
