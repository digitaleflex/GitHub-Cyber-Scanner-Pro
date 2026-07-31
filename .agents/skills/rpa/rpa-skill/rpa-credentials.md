# RPA Credentials and Secrets Management Module

Enterprise-grade credential management including HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, environment variables, and encrypted local storage.

## Credential Management Patterns

### Environment Variables (Basic)

```python
#!/usr/bin/env python3
"""Environment-based credentials - run with: uv run script.py"""

import os
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings


class Credentials(BaseModel):
    """Secure credential model."""
    username: str
    password: SecretStr
    api_key: Optional[SecretStr] = None
    totp_secret: Optional[SecretStr] = None
    
    def get_password(self) -> str:
        """Get password value."""
        return self.password.get_secret_value()
    
    def get_api_key(self) -> Optional[str]:
        """Get API key value."""
        return self.api_key.get_secret_value() if self.api_key else None


class AppSettings(BaseSettings):
    """Application settings from environment."""
    
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_username: str = Field(alias="DB_USER")
    db_password: SecretStr = Field(alias="DB_PASSWORD")
    
    # API
    api_base_url: str = Field(alias="API_URL")
    api_key: SecretStr = Field(alias="API_KEY")
    
    # RPA Target
    target_username: str = Field(alias="RPA_USERNAME")
    target_password: SecretStr = Field(alias="RPA_PASSWORD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def load_from_env(prefix: str = "") -> Credentials:
    """Load credentials from environment variables."""
    return Credentials(
        username=os.environ[f"{prefix}USERNAME"],
        password=SecretStr(os.environ[f"{prefix}PASSWORD"]),
        api_key=SecretStr(os.environ.get(f"{prefix}API_KEY", "")) or None,
        totp_secret=SecretStr(os.environ.get(f"{prefix}TOTP_SECRET", "")) or None,
    )


# Example .env file
ENV_TEMPLATE = """
# RPA Credentials
RPA_USERNAME=automation_user
RPA_PASSWORD=your_secure_password
RPA_API_KEY=your_api_key
RPA_TOTP_SECRET=JBSWY3DPEHPK3PXP

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=rpa_user
DB_PASSWORD=db_password

# API
API_URL=https://api.example.com
API_KEY=your_api_key
"""


if __name__ == "__main__":
    # Load from .env
    settings = AppSettings()
    print(f"API URL: {settings.api_base_url}")
    print(f"Username: {settings.target_username}")
    # Password is masked
    print(f"Password: {settings.target_password}")
```

---

## HashiCorp Vault Integration

```python
#!/usr/bin/env python3
"""HashiCorp Vault integration - run with: uv run script.py"""

import httpx
from dataclasses import dataclass
from typing import Optional, Any
from pydantic import SecretStr
import os


@dataclass
class VaultConfig:
    """Vault configuration."""
    url: str = "http://localhost:8200"
    token: Optional[str] = None
    namespace: Optional[str] = None
    mount_point: str = "secret"
    
    def __post_init__(self):
        if self.token is None:
            self.token = os.environ.get("VAULT_TOKEN")


class VaultClient:
    """HashiCorp Vault client."""
    
    def __init__(self, config: VaultConfig = None):
        self.config = config or VaultConfig()
        self._client = httpx.Client(
            base_url=self.config.url,
            headers=self._get_headers(),
            timeout=30
        )
    
    def _get_headers(self) -> dict:
        headers = {"X-Vault-Token": self.config.token}
        if self.config.namespace:
            headers["X-Vault-Namespace"] = self.config.namespace
        return headers
    
    def read_secret(self, path: str) -> dict[str, Any]:
        """Read secret from KV v2 engine."""
        url = f"/v1/{self.config.mount_point}/data/{path}"
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()["data"]["data"]
    
    def write_secret(self, path: str, data: dict[str, Any]):
        """Write secret to KV v2 engine."""
        url = f"/v1/{self.config.mount_point}/data/{path}"
        response = self._client.post(url, json={"data": data})
        response.raise_for_status()
    
    def delete_secret(self, path: str):
        """Delete secret."""
        url = f"/v1/{self.config.mount_point}/data/{path}"
        response = self._client.delete(url)
        response.raise_for_status()
    
    def list_secrets(self, path: str = "") -> list[str]:
        """List secrets at path."""
        url = f"/v1/{self.config.mount_point}/metadata/{path}"
        response = self._client.request("LIST", url)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()["data"]["keys"]
    
    def get_credentials(self, path: str) -> dict:
        """Get credentials from Vault."""
        secret = self.read_secret(path)
        return {
            "username": secret.get("username"),
            "password": SecretStr(secret.get("password", "")),
            "api_key": SecretStr(secret.get("api_key", "")) if secret.get("api_key") else None,
        }


class VaultCredentialProvider:
    """Credential provider using Vault."""
    
    def __init__(self, vault_client: VaultClient = None):
        self.vault = vault_client or VaultClient()
        self._cache: dict[str, dict] = {}
    
    def get(self, path: str, use_cache: bool = True) -> dict:
        """Get credentials, optionally from cache."""
        if use_cache and path in self._cache:
            return self._cache[path]
        
        creds = self.vault.get_credentials(path)
        self._cache[path] = creds
        return creds
    
    def clear_cache(self):
        """Clear credential cache."""
        self._cache.clear()
    
    def rotate(self, path: str, new_password: str):
        """Rotate password in Vault."""
        current = self.vault.read_secret(path)
        current["password"] = new_password
        self.vault.write_secret(path, current)
        
        # Clear cache
        if path in self._cache:
            del self._cache[path]


def example_vault():
    """Example Vault usage."""
    # Initialize client
    vault = VaultClient(VaultConfig(
        url="http://localhost:8200",
        token=os.environ.get("VAULT_TOKEN"),
        mount_point="secret"
    ))
    
    # Store credentials
    vault.write_secret("rpa/salesforce", {
        "username": "automation@company.com",
        "password": "secure_password_123",
        "api_key": "sf_api_key_xyz"
    })
    
    # Read credentials
    creds = vault.get_credentials("rpa/salesforce")
    print(f"Username: {creds['username']}")
    
    # Use with provider
    provider = VaultCredentialProvider(vault)
    sf_creds = provider.get("rpa/salesforce")


if __name__ == "__main__":
    example_vault()
```

---

## AWS Secrets Manager Integration

```python
#!/usr/bin/env python3
"""AWS Secrets Manager integration - run with: uv run script.py"""

import json
from typing import Optional, Any
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError
from pydantic import SecretStr


@dataclass
class AWSSecretsConfig:
    """AWS Secrets Manager configuration."""
    region_name: str = "us-east-1"
    profile_name: Optional[str] = None
    endpoint_url: Optional[str] = None  # For LocalStack testing


class AWSSecretsClient:
    """AWS Secrets Manager client."""
    
    def __init__(self, config: AWSSecretsConfig = None):
        self.config = config or AWSSecretsConfig()
        
        session_kwargs = {"region_name": self.config.region_name}
        if self.config.profile_name:
            session_kwargs["profile_name"] = self.config.profile_name
        
        session = boto3.Session(**session_kwargs)
        
        client_kwargs = {}
        if self.config.endpoint_url:
            client_kwargs["endpoint_url"] = self.config.endpoint_url
        
        self._client = session.client("secretsmanager", **client_kwargs)
    
    def get_secret(self, secret_name: str) -> dict[str, Any]:
        """Get secret value."""
        try:
            response = self._client.get_secret_value(SecretId=secret_name)
            
            if "SecretString" in response:
                return json.loads(response["SecretString"])
            else:
                # Binary secret
                import base64
                return {"binary": base64.b64decode(response["SecretBinary"])}
                
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise KeyError(f"Secret not found: {secret_name}")
            raise
    
    def create_secret(self, secret_name: str, secret_value: dict[str, Any], description: str = ""):
        """Create new secret."""
        self._client.create_secret(
            Name=secret_name,
            Description=description,
            SecretString=json.dumps(secret_value)
        )
    
    def update_secret(self, secret_name: str, secret_value: dict[str, Any]):
        """Update existing secret."""
        self._client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secret_value)
        )
    
    def delete_secret(self, secret_name: str, force: bool = False):
        """Delete secret."""
        kwargs = {"SecretId": secret_name}
        if force:
            kwargs["ForceDeleteWithoutRecovery"] = True
        else:
            kwargs["RecoveryWindowInDays"] = 7
        
        self._client.delete_secret(**kwargs)
    
    def list_secrets(self, prefix: str = "") -> list[dict]:
        """List secrets with optional prefix filter."""
        secrets = []
        paginator = self._client.get_paginator("list_secrets")
        
        for page in paginator.paginate():
            for secret in page["SecretList"]:
                if prefix and not secret["Name"].startswith(prefix):
                    continue
                secrets.append({
                    "name": secret["Name"],
                    "arn": secret["ARN"],
                    "description": secret.get("Description", ""),
                    "last_changed": secret.get("LastChangedDate"),
                })
        
        return secrets
    
    def rotate_secret(self, secret_name: str):
        """Trigger secret rotation."""
        self._client.rotate_secret(SecretId=secret_name)
    
    def get_credentials(self, secret_name: str) -> dict:
        """Get credentials in standard format."""
        secret = self.get_secret(secret_name)
        return {
            "username": secret.get("username"),
            "password": SecretStr(secret.get("password", "")),
            "api_key": SecretStr(secret.get("api_key", "")) if secret.get("api_key") else None,
        }


class AWSCredentialProvider:
    """Credential provider using AWS Secrets Manager."""
    
    def __init__(self, client: AWSSecretsClient = None, prefix: str = "rpa/"):
        self.client = client or AWSSecretsClient()
        self.prefix = prefix
        self._cache: dict[str, dict] = {}
    
    def get(self, name: str, use_cache: bool = True) -> dict:
        """Get credentials by name."""
        secret_name = f"{self.prefix}{name}"
        
        if use_cache and secret_name in self._cache:
            return self._cache[secret_name]
        
        creds = self.client.get_credentials(secret_name)
        self._cache[secret_name] = creds
        return creds
    
    def list_available(self) -> list[str]:
        """List available credential names."""
        secrets = self.client.list_secrets(self.prefix)
        return [s["name"].replace(self.prefix, "") for s in secrets]


def example_aws_secrets():
    """Example AWS Secrets Manager usage."""
    client = AWSSecretsClient(AWSSecretsConfig(region_name="us-east-1"))
    
    # Store credentials
    client.create_secret(
        "rpa/salesforce",
        {
            "username": "automation@company.com",
            "password": "secure_password",
            "api_key": "api_key_123"
        },
        description="Salesforce automation credentials"
    )
    
    # Use provider
    provider = AWSCredentialProvider(client)
    creds = provider.get("salesforce")
    print(f"Username: {creds['username']}")


if __name__ == "__main__":
    example_aws_secrets()
```

---

## Azure Key Vault Integration

```python
#!/usr/bin/env python3
"""Azure Key Vault integration - run with: uv run script.py"""

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from dataclasses import dataclass
from typing import Optional
from pydantic import SecretStr
import json


@dataclass
class AzureKeyVaultConfig:
    """Azure Key Vault configuration."""
    vault_url: str  # https://<vault-name>.vault.azure.net/
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class AzureKeyVaultClient:
    """Azure Key Vault client."""
    
    def __init__(self, config: AzureKeyVaultConfig):
        self.config = config
        
        if config.client_id and config.client_secret and config.tenant_id:
            credential = ClientSecretCredential(
                tenant_id=config.tenant_id,
                client_id=config.client_id,
                client_secret=config.client_secret
            )
        else:
            credential = DefaultAzureCredential()
        
        self._client = SecretClient(
            vault_url=config.vault_url,
            credential=credential
        )
    
    def get_secret(self, name: str) -> str:
        """Get secret value."""
        secret = self._client.get_secret(name)
        return secret.value
    
    def get_secret_json(self, name: str) -> dict:
        """Get secret as JSON."""
        value = self.get_secret(name)
        return json.loads(value)
    
    def set_secret(self, name: str, value: str, content_type: str = None):
        """Set secret value."""
        self._client.set_secret(name, value, content_type=content_type)
    
    def set_secret_json(self, name: str, value: dict):
        """Set secret as JSON."""
        self.set_secret(name, json.dumps(value), content_type="application/json")
    
    def delete_secret(self, name: str):
        """Delete secret."""
        poller = self._client.begin_delete_secret(name)
        poller.wait()
    
    def list_secrets(self) -> list[dict]:
        """List all secrets."""
        secrets = []
        for secret_properties in self._client.list_properties_of_secrets():
            secrets.append({
                "name": secret_properties.name,
                "enabled": secret_properties.enabled,
                "created_on": secret_properties.created_on,
                "updated_on": secret_properties.updated_on,
            })
        return secrets
    
    def get_credentials(self, name: str) -> dict:
        """Get credentials in standard format."""
        secret = self.get_secret_json(name)
        return {
            "username": secret.get("username"),
            "password": SecretStr(secret.get("password", "")),
            "api_key": SecretStr(secret.get("api_key", "")) if secret.get("api_key") else None,
        }


def example_azure_keyvault():
    """Example Azure Key Vault usage."""
    client = AzureKeyVaultClient(AzureKeyVaultConfig(
        vault_url="https://my-vault.vault.azure.net/",
        tenant_id="your-tenant-id",
        client_id="your-client-id",
        client_secret="your-client-secret"
    ))
    
    # Store credentials
    client.set_secret_json("rpa-salesforce", {
        "username": "automation@company.com",
        "password": "secure_password"
    })
    
    # Read credentials
    creds = client.get_credentials("rpa-salesforce")
    print(f"Username: {creds['username']}")


if __name__ == "__main__":
    example_azure_keyvault()
```

---

## Encrypted Local Storage

```python
#!/usr/bin/env python3
"""Encrypted local credential storage - run with: uv run script.py"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path
from typing import Optional
from pydantic import SecretStr
import base64
import json
import os


class EncryptedCredentialStore:
    """Encrypted local credential storage."""
    
    def __init__(
        self,
        storage_path: str = "~/.rpa/credentials.enc",
        master_password: str = None
    ):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._master_password = master_password or os.environ.get("RPA_MASTER_PASSWORD")
        if not self._master_password:
            raise ValueError("Master password required (RPA_MASTER_PASSWORD env var or parameter)")
        
        self._fernet = self._create_fernet()
        self._credentials: dict = self._load()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet cipher from master password."""
        salt_path = self.storage_path.with_suffix(".salt")
        
        if salt_path.exists():
            salt = salt_path.read_bytes()
        else:
            salt = os.urandom(16)
            salt_path.write_bytes(salt)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self._master_password.encode()))
        return Fernet(key)
    
    def _load(self) -> dict:
        """Load and decrypt credentials."""
        if not self.storage_path.exists():
            return {}
        
        encrypted = self.storage_path.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted)
    
    def _save(self):
        """Encrypt and save credentials."""
        data = json.dumps(self._credentials).encode()
        encrypted = self._fernet.encrypt(data)
        self.storage_path.write_bytes(encrypted)
    
    def set(self, name: str, credentials: dict):
        """Store credentials."""
        self._credentials[name] = credentials
        self._save()
    
    def get(self, name: str) -> Optional[dict]:
        """Get credentials."""
        cred = self._credentials.get(name)
        if cred:
            return {
                "username": cred.get("username"),
                "password": SecretStr(cred.get("password", "")),
                "api_key": SecretStr(cred.get("api_key", "")) if cred.get("api_key") else None,
            }
        return None
    
    def delete(self, name: str):
        """Delete credentials."""
        if name in self._credentials:
            del self._credentials[name]
            self._save()
    
    def list(self) -> list[str]:
        """List credential names."""
        return list(self._credentials.keys())
    
    def export(self, path: str, export_password: str):
        """Export credentials with different password."""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(export_password.encode()))
        fernet = Fernet(key)
        
        data = json.dumps(self._credentials).encode()
        encrypted = fernet.encrypt(data)
        
        export_path = Path(path)
        export_path.write_bytes(salt + encrypted)
    
    def import_from(self, path: str, import_password: str):
        """Import credentials from export file."""
        content = Path(path).read_bytes()
        salt = content[:16]
        encrypted = content[16:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(import_password.encode()))
        fernet = Fernet(key)
        
        decrypted = fernet.decrypt(encrypted)
        imported = json.loads(decrypted)
        
        self._credentials.update(imported)
        self._save()


def example_encrypted_store():
    """Example encrypted storage usage."""
    os.environ["RPA_MASTER_PASSWORD"] = "my_secure_master_password"
    
    store = EncryptedCredentialStore()
    
    # Store credentials
    store.set("salesforce", {
        "username": "automation@company.com",
        "password": "secure_password",
        "api_key": "api_key_123"
    })
    
    # Read credentials
    creds = store.get("salesforce")
    print(f"Username: {creds['username']}")
    print(f"Password: {creds['password']}")  # Masked
    
    # List stored
    print(f"Stored credentials: {store.list()}")


if __name__ == "__main__":
    example_encrypted_store()
```

---

## Unified Credential Provider

```python
#!/usr/bin/env python3
"""Unified credential provider - run with: uv run script.py"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol
from pydantic import SecretStr
import os


class CredentialBackend(Enum):
    ENV = "env"
    VAULT = "vault"
    AWS = "aws"
    AZURE = "azure"
    LOCAL = "local"


class CredentialProvider(Protocol):
    """Credential provider protocol."""
    
    def get(self, name: str) -> dict:
        """Get credentials by name."""
        ...


@dataclass
class UnifiedCredentialConfig:
    """Unified credential configuration."""
    backend: CredentialBackend = CredentialBackend.ENV
    vault_url: Optional[str] = None
    vault_token: Optional[str] = None
    aws_region: Optional[str] = None
    azure_vault_url: Optional[str] = None
    local_storage_path: Optional[str] = None
    prefix: str = "rpa/"
    cache_enabled: bool = True


class UnifiedCredentialProvider:
    """Unified credential provider supporting multiple backends."""
    
    def __init__(self, config: UnifiedCredentialConfig = None):
        self.config = config or UnifiedCredentialConfig()
        self._cache: dict[str, dict] = {}
        self._backend = self._init_backend()
    
    def _init_backend(self) -> CredentialProvider:
        """Initialize appropriate backend."""
        match self.config.backend:
            case CredentialBackend.ENV:
                return EnvCredentialProvider(self.config.prefix)
            
            case CredentialBackend.VAULT:
                from rpa_credentials import VaultClient, VaultConfig, VaultCredentialProvider
                vault = VaultClient(VaultConfig(
                    url=self.config.vault_url,
                    token=self.config.vault_token
                ))
                return VaultCredentialProvider(vault)
            
            case CredentialBackend.AWS:
                from rpa_credentials import AWSSecretsClient, AWSCredentialProvider
                return AWSCredentialProvider(
                    AWSSecretsClient(),
                    prefix=self.config.prefix
                )
            
            case CredentialBackend.AZURE:
                from rpa_credentials import AzureKeyVaultClient, AzureKeyVaultConfig
                client = AzureKeyVaultClient(AzureKeyVaultConfig(
                    vault_url=self.config.azure_vault_url
                ))
                return AzureCredentialProvider(client)
            
            case CredentialBackend.LOCAL:
                from rpa_credentials import EncryptedCredentialStore
                return EncryptedCredentialStore(self.config.local_storage_path)
        
        raise ValueError(f"Unknown backend: {self.config.backend}")
    
    def get(self, name: str) -> dict:
        """Get credentials."""
        if self.config.cache_enabled and name in self._cache:
            return self._cache[name]
        
        creds = self._backend.get(name)
        
        if self.config.cache_enabled:
            self._cache[name] = creds
        
        return creds
    
    def clear_cache(self):
        """Clear credential cache."""
        self._cache.clear()


class EnvCredentialProvider:
    """Simple environment-based provider."""
    
    def __init__(self, prefix: str = ""):
        self.prefix = prefix.upper().replace("/", "_").replace("-", "_")
    
    def get(self, name: str) -> dict:
        name_upper = name.upper().replace("/", "_").replace("-", "_")
        prefix = f"{self.prefix}{name_upper}_"
        
        return {
            "username": os.environ.get(f"{prefix}USERNAME"),
            "password": SecretStr(os.environ.get(f"{prefix}PASSWORD", "")),
            "api_key": SecretStr(os.environ.get(f"{prefix}API_KEY", "")) 
                      if os.environ.get(f"{prefix}API_KEY") else None,
        }


# Convenience function
def get_credentials(
    name: str,
    backend: CredentialBackend = None
) -> dict:
    """Get credentials using configured backend."""
    if backend is None:
        backend_str = os.environ.get("RPA_CREDENTIAL_BACKEND", "env")
        backend = CredentialBackend(backend_str)
    
    config = UnifiedCredentialConfig(backend=backend)
    provider = UnifiedCredentialProvider(config)
    return provider.get(name)


if __name__ == "__main__":
    # Set test env vars
    os.environ["RPA_SALESFORCE_USERNAME"] = "user@example.com"
    os.environ["RPA_SALESFORCE_PASSWORD"] = "password123"
    
    creds = get_credentials("salesforce")
    print(f"Username: {creds['username']}")
```

---

## Credential Rotation

```python
#!/usr/bin/env python3
"""Credential rotation patterns - run with: uv run script.py"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Callable, Optional
import secrets
import string
import structlog

log = structlog.get_logger()


@dataclass
class RotationPolicy:
    """Credential rotation policy."""
    max_age_days: int = 90
    min_password_length: int = 16
    require_special_chars: bool = True
    require_numbers: bool = True
    require_uppercase: bool = True


class CredentialRotator:
    """Handle credential rotation."""
    
    def __init__(
        self,
        credential_provider,
        policy: RotationPolicy = None
    ):
        self.provider = credential_provider
        self.policy = policy or RotationPolicy()
    
    def generate_password(self) -> str:
        """Generate secure password."""
        chars = string.ascii_lowercase
        
        if self.policy.require_uppercase:
            chars += string.ascii_uppercase
        if self.policy.require_numbers:
            chars += string.digits
        if self.policy.require_special_chars:
            chars += "!@#$%^&*"
        
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(self.policy.min_password_length))
            
            # Validate
            if self.policy.require_uppercase and not any(c.isupper() for c in password):
                continue
            if self.policy.require_numbers and not any(c.isdigit() for c in password):
                continue
            if self.policy.require_special_chars and not any(c in "!@#$%^&*" for c in password):
                continue
            
            return password
    
    def needs_rotation(self, name: str, last_rotated: datetime) -> bool:
        """Check if credential needs rotation."""
        age = datetime.now() - last_rotated
        return age.days >= self.policy.max_age_days
    
    def rotate(
        self,
        name: str,
        update_target: Callable[[str, str], bool]
    ) -> bool:
        """Rotate credential.
        
        Args:
            name: Credential name
            update_target: Function to update password on target system
                          Takes (username, new_password), returns success
        """
        current = self.provider.get(name)
        new_password = self.generate_password()
        
        log.info("rotating_credential", name=name)
        
        # Update target system first
        if not update_target(current["username"], new_password):
            log.error("rotation_failed", name=name, reason="target update failed")
            return False
        
        # Update credential store
        self.provider.rotate(name, new_password)
        
        log.info("rotation_complete", name=name)
        return True


def example_rotation():
    """Example credential rotation."""
    # This would integrate with your credential provider
    rotator = CredentialRotator(
        credential_provider=None,  # Your provider
        policy=RotationPolicy(max_age_days=90)
    )
    
    # Generate new password
    new_pass = rotator.generate_password()
    print(f"Generated password: {new_pass}")


if __name__ == "__main__":
    example_rotation()
```

---

## Best Practices

1. **Never hardcode credentials** - Always use environment or secret managers
2. **Use secret masking** - Pydantic SecretStr prevents accidental logging
3. **Rotate regularly** - Implement automatic rotation policies
4. **Audit access** - Log credential access (not values)
5. **Use least privilege** - Separate credentials per service
6. **Cache wisely** - Balance security and performance
7. **Encrypt at rest** - Use encrypted storage for local credentials

---

**Next Module:** See **rpa-cicd.md** for CI/CD integration.
