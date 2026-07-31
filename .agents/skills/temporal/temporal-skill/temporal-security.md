# Temporal Security

> **mTLS, Data Encryption, RBAC, and Secrets Management**  
> Enterprise security patterns for production Temporal deployments.

## Overview

Temporal security covers four key areas:

| Area | Description |
|------|-------------|
| **Transport Security** | mTLS between clients, workers, and server |
| **Data Encryption** | Encrypt workflow inputs, outputs, and history |
| **Access Control** | Namespace-level RBAC and API restrictions |
| **Secrets Management** | Secure handling of credentials and API keys |

---

## Transport Security (mTLS)

### Generate Certificates

```bash
# Create CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.pem \
  -subj "/CN=Temporal CA"

# Create server certificate
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr \
  -subj "/CN=temporal-server"
openssl x509 -req -days 365 -in server.csr -CA ca.pem -CAkey ca.key \
  -CAcreateserial -out server.pem

# Create client certificate
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr \
  -subj "/CN=temporal-client"
openssl x509 -req -days 365 -in client.csr -CA ca.pem -CAkey ca.key \
  -CAcreateserial -out client.pem

# Verify certificates
openssl verify -CAfile ca.pem server.pem
openssl verify -CAfile ca.pem client.pem
```

### Server Configuration with mTLS

```bash
# Start Temporal server with TLS
temporal server start-dev \
  --tls-cert-file server.pem \
  --tls-key-file server.key \
  --tls-ca-file ca.pem \
  --tls-require-client-cert
```

### Python Client with mTLS

```python
# client.py
import asyncio
from temporalio.client import Client, TLSConfig

async def create_secure_client() -> Client:
    """Create client with mTLS authentication."""
    
    # Load certificates
    with open("client.pem", "rb") as f:
        client_cert = f.read()
    with open("client.key", "rb") as f:
        client_key = f.read()
    with open("ca.pem", "rb") as f:
        ca_cert = f.read()
    
    tls_config = TLSConfig(
        client_cert=client_cert,
        client_private_key=client_key,
        server_root_ca_cert=ca_cert,
    )
    
    return await Client.connect(
        "localhost:7233",
        namespace="default",
        tls=tls_config,
    )

async def main():
    client = await create_secure_client()
    # Use client...

if __name__ == "__main__":
    asyncio.run(main())
```

### Worker with mTLS

```python
# worker.py
import asyncio
from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker

async def run_secure_worker():
    """Run worker with mTLS."""
    
    with open("client.pem", "rb") as f:
        client_cert = f.read()
    with open("client.key", "rb") as f:
        client_key = f.read()
    with open("ca.pem", "rb") as f:
        ca_cert = f.read()
    
    tls_config = TLSConfig(
        client_cert=client_cert,
        client_private_key=client_key,
        server_root_ca_cert=ca_cert,
    )
    
    client = await Client.connect(
        "localhost:7233",
        namespace="default",
        tls=tls_config,
    )
    
    worker = Worker(
        client,
        task_queue="secure-queue",
        workflows=[...],
        activities=[...],
    )
    
    await worker.run()
```

### Configuration via Environment

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class SecureSettings(BaseSettings):
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    
    # TLS paths
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    tls_ca_path: Optional[str] = None
    
    def get_tls_config(self) -> Optional[TLSConfig]:
        if not all([self.tls_cert_path, self.tls_key_path]):
            return None
        
        with open(self.tls_cert_path, "rb") as f:
            client_cert = f.read()
        with open(self.tls_key_path, "rb") as f:
            client_key = f.read()
        
        ca_cert = None
        if self.tls_ca_path:
            with open(self.tls_ca_path, "rb") as f:
                ca_cert = f.read()
        
        return TLSConfig(
            client_cert=client_cert,
            client_private_key=client_key,
            server_root_ca_cert=ca_cert,
        )
    
    class Config:
        env_prefix = "TEMPORAL_"
```

```bash
# .env
TEMPORAL_ADDRESS=temporal.example.com:7233
TEMPORAL_NAMESPACE=production
TEMPORAL_TLS_CERT_PATH=/etc/temporal/client.pem
TEMPORAL_TLS_KEY_PATH=/etc/temporal/client.key
TEMPORAL_TLS_CA_PATH=/etc/temporal/ca.pem
```

---

## Data Encryption

Encrypt sensitive workflow data at rest and in transit using custom payload codecs.

### Custom Encryption Codec

```python
# encryption.py
from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec
from cryptography.fernet import Fernet
from typing import List
import base64

class EncryptionCodec(PayloadCodec):
    """Encrypt/decrypt workflow payloads using Fernet."""
    
    def __init__(self, key: bytes):
        self._fernet = Fernet(key)
    
    async def encode(self, payloads: List[Payload]) -> List[Payload]:
        """Encrypt payloads before sending to server."""
        return [
            Payload(
                metadata={
                    "encoding": b"binary/encrypted",
                    "encryption-key-id": b"default",
                },
                data=self._fernet.encrypt(p.SerializeToString()),
            )
            for p in payloads
        ]
    
    async def decode(self, payloads: List[Payload]) -> List[Payload]:
        """Decrypt payloads received from server."""
        result = []
        for p in payloads:
            if p.metadata.get("encoding") == b"binary/encrypted":
                decrypted = self._fernet.decrypt(p.data)
                new_payload = Payload()
                new_payload.ParseFromString(decrypted)
                result.append(new_payload)
            else:
                result.append(p)
        return result


def generate_encryption_key() -> bytes:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key()
```

### Using Encryption Codec

```python
# client_encrypted.py
import asyncio
from temporalio.client import Client
from temporalio.converter import DataConverter
from encryption import EncryptionCodec
import os

async def create_encrypted_client() -> Client:
    """Create client with payload encryption."""
    
    # Load encryption key from secure source
    encryption_key = os.environ["TEMPORAL_ENCRYPTION_KEY"].encode()
    
    return await Client.connect(
        "localhost:7233",
        data_converter=DataConverter(
            payload_codec=EncryptionCodec(encryption_key)
        ),
    )

async def main():
    client = await create_encrypted_client()
    
    # All workflow inputs/outputs are now encrypted
    result = await client.execute_workflow(
        SensitiveWorkflow.run,
        {"ssn": "123-45-6789", "credit_card": "4111111111111111"},
        id="encrypted-workflow",
        task_queue="secure-queue",
    )
```

### Worker with Encryption

```python
# worker_encrypted.py
from temporalio.worker import Worker
from temporalio.converter import DataConverter
from encryption import EncryptionCodec

async def run_encrypted_worker():
    encryption_key = os.environ["TEMPORAL_ENCRYPTION_KEY"].encode()
    
    client = await Client.connect(
        "localhost:7233",
        data_converter=DataConverter(
            payload_codec=EncryptionCodec(encryption_key)
        ),
    )
    
    worker = Worker(
        client,
        task_queue="secure-queue",
        workflows=[SensitiveWorkflow],
        activities=[process_sensitive_data],
    )
    
    await worker.run()
```

### Key Rotation

```python
# key_rotation.py
from temporalio.converter import PayloadCodec
from cryptography.fernet import Fernet, MultiFernet
from typing import List, Dict

class RotatingEncryptionCodec(PayloadCodec):
    """Support multiple encryption keys for rotation."""
    
    def __init__(self, keys: Dict[str, bytes], current_key_id: str):
        self._keys = {k: Fernet(v) for k, v in keys.items()}
        self._current_key_id = current_key_id
        self._multi_fernet = MultiFernet([
            self._keys[current_key_id],
            *[f for k, f in self._keys.items() if k != current_key_id]
        ])
    
    async def encode(self, payloads: List[Payload]) -> List[Payload]:
        """Encrypt with current key."""
        current_fernet = self._keys[self._current_key_id]
        return [
            Payload(
                metadata={
                    "encoding": b"binary/encrypted",
                    "encryption-key-id": self._current_key_id.encode(),
                },
                data=current_fernet.encrypt(p.SerializeToString()),
            )
            for p in payloads
        ]
    
    async def decode(self, payloads: List[Payload]) -> List[Payload]:
        """Decrypt with any known key."""
        result = []
        for p in payloads:
            if p.metadata.get("encoding") == b"binary/encrypted":
                # MultiFernet tries all keys
                decrypted = self._multi_fernet.decrypt(p.data)
                new_payload = Payload()
                new_payload.ParseFromString(decrypted)
                result.append(new_payload)
            else:
                result.append(p)
        return result
```

---

## Access Control

### Namespace Isolation

```bash
# Create namespaces for different environments/teams
temporal operator namespace create --namespace development
temporal operator namespace create --namespace staging
temporal operator namespace create --namespace production

# List namespaces
temporal operator namespace list

# Describe namespace
temporal operator namespace describe --namespace production
```

### Namespace-Specific Workers

```python
# production_worker.py
async def run_production_worker():
    """Worker that only processes production workloads."""
    client = await Client.connect(
        "localhost:7233",
        namespace="production",
        tls=get_tls_config(),
    )
    
    worker = Worker(
        client,
        task_queue="production-queue",
        workflows=[ProductionWorkflow],
        activities=[production_activity],
    )
    
    await worker.run()

# development_worker.py
async def run_dev_worker():
    """Worker for development workloads."""
    client = await Client.connect(
        "localhost:7233",
        namespace="development",
    )
    
    worker = Worker(
        client,
        task_queue="dev-queue",
        workflows=[DevWorkflow],
        activities=[dev_activity],
    )
    
    await worker.run()
```

### API Key Authentication (Temporal Cloud)

```python
# cloud_client.py
from temporalio.client import Client

async def create_cloud_client() -> Client:
    """Connect to Temporal Cloud with API key."""
    
    return await Client.connect(
        "your-namespace.your-account.tmprl.cloud:7233",
        namespace="your-namespace",
        api_key=os.environ["TEMPORAL_API_KEY"],
    )
```

---

## Secrets Management

### Environment-Based Secrets

```python
# activities.py
from temporalio import activity
import os

@activity.defn
async def call_external_api(data: dict) -> dict:
    """Activity that uses secrets from environment."""
    api_key = os.environ["EXTERNAL_API_KEY"]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/endpoint",
            headers={"Authorization": f"Bearer {api_key}"},
            json=data,
        )
        return response.json()
```

### Secrets via Activity Context

```python
# worker.py
from dataclasses import dataclass

@dataclass
class ActivityContext:
    """Shared context for activities."""
    db_connection_string: str
    api_keys: dict
    encryption_key: bytes

async def run_worker_with_context():
    # Load secrets at worker startup
    context = ActivityContext(
        db_connection_string=os.environ["DATABASE_URL"],
        api_keys={
            "stripe": os.environ["STRIPE_API_KEY"],
            "sendgrid": os.environ["SENDGRID_API_KEY"],
        },
        encryption_key=os.environ["ENCRYPTION_KEY"].encode(),
    )
    
    # Create activities with context
    @activity.defn
    async def process_payment(amount: float) -> dict:
        # Access context via closure
        stripe_key = context.api_keys["stripe"]
        # Use stripe_key...
    
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="payments",
        workflows=[PaymentWorkflow],
        activities=[process_payment],
    )
    
    await worker.run()
```

### HashiCorp Vault Integration

```python
# vault_secrets.py
import hvac
from functools import lru_cache

class VaultSecrets:
    """Load secrets from HashiCorp Vault."""
    
    def __init__(self, vault_addr: str, vault_token: str):
        self._client = hvac.Client(url=vault_addr, token=vault_token)
    
    @lru_cache(maxsize=100)
    def get_secret(self, path: str, key: str) -> str:
        """Get a secret from Vault (cached)."""
        secret = self._client.secrets.kv.v2.read_secret_version(path=path)
        return secret["data"]["data"][key]
    
    def get_database_url(self) -> str:
        return self.get_secret("temporal/database", "connection_string")
    
    def get_api_key(self, service: str) -> str:
        return self.get_secret(f"temporal/api-keys", service)

# Usage in worker
vault = VaultSecrets(
    vault_addr=os.environ["VAULT_ADDR"],
    vault_token=os.environ["VAULT_TOKEN"],
)

@activity.defn
async def call_service(data: dict) -> dict:
    api_key = vault.get_api_key("external-service")
    # Use api_key...
```

### AWS Secrets Manager Integration

```python
# aws_secrets.py
import boto3
import json
from functools import lru_cache

class AWSSecrets:
    """Load secrets from AWS Secrets Manager."""
    
    def __init__(self, region: str = "us-east-1"):
        self._client = boto3.client("secretsmanager", region_name=region)
    
    @lru_cache(maxsize=100)
    def get_secret(self, secret_name: str) -> dict:
        """Get secret from AWS Secrets Manager (cached)."""
        response = self._client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    
    def get_temporal_config(self) -> dict:
        return self.get_secret("temporal/config")
    
    def get_encryption_key(self) -> bytes:
        secrets = self.get_secret("temporal/encryption")
        return secrets["key"].encode()

# Usage
aws_secrets = AWSSecrets()

async def create_client():
    config = aws_secrets.get_temporal_config()
    encryption_key = aws_secrets.get_encryption_key()
    
    return await Client.connect(
        config["address"],
        namespace=config["namespace"],
        data_converter=DataConverter(
            payload_codec=EncryptionCodec(encryption_key)
        ),
    )
```

---

## Security Best Practices

### 1. Never Store Secrets in Workflow State

```python
# BAD - Secrets stored in workflow history
@workflow.defn
class BadWorkflow:
    @workflow.run
    async def run(self, api_key: str):  # DON'T pass secrets as input
        await workflow.execute_activity(call_api, api_key, ...)

# GOOD - Secrets loaded in activity
@workflow.defn
class GoodWorkflow:
    @workflow.run
    async def run(self, request_id: str):
        await workflow.execute_activity(call_api, request_id, ...)

@activity.defn
async def call_api(request_id: str) -> dict:
    api_key = os.environ["API_KEY"]  # Load in activity
    # Use api_key...
```

### 2. Use Encryption for Sensitive Data

```python
# Encrypt PII and financial data
@workflow.defn
class SecureWorkflow:
    @workflow.run
    async def run(self, encrypted_input: dict) -> dict:
        # Data is automatically encrypted via codec
        return await workflow.execute_activity(
            process_sensitive,
            encrypted_input,
            start_to_close_timeout=timedelta(minutes=5),
        )
```

### 3. Rotate Certificates and Keys

```bash
# Certificate rotation script
#!/bin/bash
# run monthly via cron

# Generate new certificates
./generate-certs.sh

# Reload workers (they'll pick up new certs)
sudo systemctl reload temporal-worker

# Update server
sudo systemctl reload temporal-server
```

### 4. Audit Workflow Access

```python
# Add audit logging to activities
import structlog

logger = structlog.get_logger()

@activity.defn
async def sensitive_operation(user_id: str, action: str) -> dict:
    logger.info(
        "sensitive_operation_executed",
        user_id=user_id,
        action=action,
        activity_id=activity.info().activity_id,
        workflow_id=activity.info().workflow_id,
    )
    # Perform operation...
```

---

## Security Checklist

- [ ] mTLS enabled between all components
- [ ] Payload encryption for sensitive data
- [ ] Secrets loaded from secure source (Vault, AWS Secrets Manager)
- [ ] Namespace isolation for environments
- [ ] Certificate rotation scheduled
- [ ] Audit logging enabled
- [ ] No secrets in workflow inputs/outputs
- [ ] Encryption keys rotated regularly
- [ ] Access logs monitored

---

**Next:** See **temporal-operations.md** for backup, restore, and cluster management.
