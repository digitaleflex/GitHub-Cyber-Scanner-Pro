# RPA CI/CD Integration Module

Enterprise CI/CD integration including GitHub Actions, GitLab CI, Docker containerization, Kubernetes deployment, and automated testing.

## GitHub Actions

### Complete RPA Workflow

```yaml
# .github/workflows/rpa-automation.yml
name: RPA Automation Pipeline

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:
    inputs:
      workflow_name:
        description: 'Workflow to run'
        required: true
        default: 'daily_report'
        type: choice
        options:
          - daily_report
          - data_extraction
          - form_submission

env:
  PYTHON_VERSION: '3.12'

jobs:
  run-automation:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
      
      - name: Install dependencies
        run: |
          uv sync
          uv run playwright install chromium --with-deps
      
      - name: Run RPA workflow
        env:
          RPA_USERNAME: ${{ secrets.RPA_USERNAME }}
          RPA_PASSWORD: ${{ secrets.RPA_PASSWORD }}
          RPA_API_KEY: ${{ secrets.RPA_API_KEY }}
        run: |
          uv run python workflows/${{ github.event.inputs.workflow_name || 'daily_report' }}.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: rpa-results-${{ github.run_id }}
          path: |
            output/
            screenshots/
            logs/
          retention-days: 30
      
      - name: Upload to S3 (optional)
        if: success()
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws s3 sync output/ s3://rpa-results/$(date +%Y-%m-%d)/
      
      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          channel-id: 'rpa-alerts'
          slack-message: 'RPA workflow failed: ${{ github.workflow }}'
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}

  test-automation:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install dependencies
        run: |
          uv sync
          uv run playwright install chromium --with-deps
      
      - name: Run tests
        run: |
          uv run pytest tests/ -v --html=reports/test-report.html
      
      - name: Upload test report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-report
          path: reports/
```

### Reusable Workflow

```yaml
# .github/workflows/rpa-reusable.yml
name: Reusable RPA Workflow

on:
  workflow_call:
    inputs:
      script_path:
        required: true
        type: string
      headless:
        required: false
        type: boolean
        default: true
    secrets:
      RPA_CREDENTIALS:
        required: true

jobs:
  execute:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python and uv
        uses: astral-sh/setup-uv@v4
      
      - name: Install dependencies
        run: |
          uv sync
          uv run playwright install chromium --with-deps
      
      - name: Run automation
        env:
          RPA_CREDENTIALS: ${{ secrets.RPA_CREDENTIALS }}
          HEADLESS: ${{ inputs.headless }}
        run: |
          uv run python ${{ inputs.script_path }}
```

---

## Docker

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY workflows/ ./workflows/

# Install dependencies
RUN uv sync --frozen

# Install Playwright browsers
RUN uv run playwright install chromium --with-deps

# Create non-root user
RUN useradd -m -u 1000 rpa
RUN chown -R rpa:rpa /app
USER rpa

# Default command
CMD ["uv", "run", "python", "-m", "rpa.main"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  rpa-worker:
    build: .
    environment:
      - RPA_USERNAME=${RPA_USERNAME}
      - RPA_PASSWORD=${RPA_PASSWORD}
      - RPA_CREDENTIAL_BACKEND=vault
      - VAULT_ADDR=http://vault:8200
      - VAULT_TOKEN=${VAULT_TOKEN}
      - LOG_LEVEL=INFO
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    depends_on:
      - vault
      - redis
    networks:
      - rpa-network
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1'

  rpa-scheduler:
    build: .
    command: ["uv", "run", "python", "-m", "rpa.scheduler"]
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    networks:
      - rpa-network

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    networks:
      - rpa-network

  vault:
    image: hashicorp/vault:latest
    cap_add:
      - IPC_LOCK
    environment:
      - VAULT_DEV_ROOT_TOKEN_ID=${VAULT_TOKEN}
    ports:
      - "8200:8200"
    networks:
      - rpa-network

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - rpa-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - rpa-network

networks:
  rpa-network:

volumes:
  redis-data:
  grafana-data:
```

### Multi-Stage Build

```dockerfile
# Dockerfile.production
# Stage 1: Build
FROM python:3.12-slim AS builder

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.12-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy uv and dependencies
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/root/.local/bin:/app/.venv/bin:$PATH"

WORKDIR /app
COPY src/ ./src/
COPY workflows/ ./workflows/

# Install browsers
RUN playwright install chromium

# Create non-root user
RUN useradd -m -u 1000 rpa && chown -R rpa:rpa /app
USER rpa

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import playwright; print('OK')"

CMD ["python", "-m", "rpa.main"]
```

---

## Kubernetes

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rpa-worker
  labels:
    app: rpa-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rpa-worker
  template:
    metadata:
      labels:
        app: rpa-worker
    spec:
      containers:
        - name: rpa-worker
          image: your-registry/rpa-worker:latest
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          env:
            - name: RPA_CREDENTIAL_BACKEND
              value: "vault"
            - name: VAULT_ADDR
              value: "http://vault:8200"
            - name: VAULT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: vault-credentials
                  key: token
            - name: LOG_LEVEL
              value: "INFO"
          volumeMounts:
            - name: output
              mountPath: /app/output
            - name: logs
              mountPath: /app/logs
          livenessProbe:
            exec:
              command:
                - python
                - -c
                - "import playwright; print('OK')"
            initialDelaySeconds: 30
            periodSeconds: 60
          readinessProbe:
            exec:
              command:
                - python
                - -c
                - "import httpx; httpx.get('https://example.com')"
            initialDelaySeconds: 10
            periodSeconds: 30
      volumes:
        - name: output
          persistentVolumeClaim:
            claimName: rpa-output-pvc
        - name: logs
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: rpa-worker
spec:
  selector:
    app: rpa-worker
  ports:
    - port: 8080
      targetPort: 8080
```

### CronJob

```yaml
# k8s/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: rpa-daily-report
spec:
  schedule: "0 6 * * *"  # Daily at 6 AM
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 3600
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: rpa-job
              image: your-registry/rpa-worker:latest
              command: ["python", "-m", "rpa.workflows.daily_report"]
              env:
                - name: VAULT_ADDR
                  value: "http://vault:8200"
                - name: VAULT_TOKEN
                  valueFrom:
                    secretKeyRef:
                      name: vault-credentials
                      key: token
              resources:
                requests:
                  memory: "1Gi"
                  cpu: "500m"
                limits:
                  memory: "2Gi"
                  cpu: "1000m"
```

### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rpa-config
data:
  config.yaml: |
    browser:
      headless: true
      timeout: 30000
      viewport:
        width: 1920
        height: 1080
    
    retry:
      max_attempts: 3
      base_delay: 1.0
      max_delay: 60.0
    
    logging:
      level: INFO
      format: json
    
    monitoring:
      prometheus_port: 8080
      health_check_port: 8081
```

---

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy
  - run

variables:
  PYTHON_VERSION: "3.12"
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE/rpa-worker

.uv-setup: &uv-setup
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.local/bin:$PATH"
    - uv sync
    - uv run playwright install chromium --with-deps

test:
  stage: test
  image: python:3.12-slim
  <<: *uv-setup
  script:
    - uv run pytest tests/ -v --junitxml=report.xml
  artifacts:
    reports:
      junit: report.xml

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA -t $DOCKER_IMAGE:latest .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA
    - docker push $DOCKER_IMAGE:latest
  only:
    - main

deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/rpa-worker rpa-worker=$DOCKER_IMAGE:$CI_COMMIT_SHA
  environment:
    name: staging
  only:
    - main

run-daily:
  stage: run
  image: $DOCKER_IMAGE:latest
  script:
    - python -m rpa.workflows.daily_report
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

---

## Testing

### Pytest Configuration

```python
# conftest.py
import pytest
from playwright.sync_api import sync_playwright, Page, Browser


@pytest.fixture(scope="session")
def browser():
    """Browser fixture for tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser):
    """Page fixture for tests."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def mock_server():
    """Start mock server for testing."""
    import subprocess
    import time
    
    proc = subprocess.Popen(
        ["python", "-m", "http.server", "8888"],
        cwd="tests/fixtures"
    )
    time.sleep(1)
    yield "http://localhost:8888"
    proc.terminate()
```

### Test Examples

```python
# tests/test_workflows.py
import pytest
from playwright.sync_api import Page


class TestLoginWorkflow:
    """Test login workflow."""
    
    def test_successful_login(self, page: Page, mock_server: str):
        """Test successful login flow."""
        page.goto(f"{mock_server}/login.html")
        
        page.fill("#username", "testuser")
        page.fill("#password", "testpass")
        page.click("button[type=submit]")
        
        assert page.url.endswith("/dashboard")
    
    def test_invalid_credentials(self, page: Page, mock_server: str):
        """Test login with invalid credentials."""
        page.goto(f"{mock_server}/login.html")
        
        page.fill("#username", "invalid")
        page.fill("#password", "invalid")
        page.click("button[type=submit]")
        
        error = page.locator(".error-message")
        assert error.is_visible()


class TestDataExtraction:
    """Test data extraction."""
    
    def test_table_extraction(self, page: Page, mock_server: str):
        """Test extracting table data."""
        page.goto(f"{mock_server}/table.html")
        
        rows = page.locator("table tbody tr").all()
        assert len(rows) > 0
        
        data = []
        for row in rows:
            cells = row.locator("td").all_text_contents()
            data.append(cells)
        
        assert len(data) > 0
```

---

## Secrets Management in CI

### GitHub Secrets

```yaml
# Store these in GitHub Secrets:
# - RPA_USERNAME
# - RPA_PASSWORD
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - VAULT_TOKEN

- name: Load secrets
  env:
    RPA_USERNAME: ${{ secrets.RPA_USERNAME }}
    RPA_PASSWORD: ${{ secrets.RPA_PASSWORD }}
  run: |
    uv run python workflow.py
```

### Vault Integration in CI

```yaml
- name: Import Secrets from Vault
  uses: hashicorp/vault-action@v2
  with:
    url: https://vault.company.com
    token: ${{ secrets.VAULT_TOKEN }}
    secrets: |
      secret/data/rpa/salesforce username | SF_USERNAME ;
      secret/data/rpa/salesforce password | SF_PASSWORD
```

---

## Best Practices

1. **Use secrets managers** - Never commit credentials
2. **Run in containers** - Reproducible environments
3. **Implement health checks** - Kubernetes liveness/readiness
4. **Set resource limits** - Prevent runaway processes
5. **Use multi-stage builds** - Smaller production images
6. **Implement retries** - Handle transient failures
7. **Archive artifacts** - Keep results for debugging
8. **Monitor and alert** - Prometheus + Grafana

---

**Next Module:** See **rpa-observability.md** for logging and metrics.
