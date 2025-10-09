

# FinOpsGuard Authentication Guide

This guide covers authentication and authorization in FinOpsGuard.

## Table of Contents

- [Overview](#overview)
- [Authentication Methods](#authentication-methods)
- [Quick Start](#quick-start)
- [API Key Authentication](#api-key-authentication)
- [JWT Bearer Tokens](#jwt-bearer-tokens)
- [OAuth2 Integration](#oauth2-integration)
- [mTLS (Mutual TLS)](#mtls-mutual-tls)
- [Role-Based Access Control](#role-based-access-control)
- [Configuration](#configuration)
- [Integration Examples](#integration-examples)

---

## Overview

FinOpsGuard supports multiple authentication methods:

| Method | Use Case | Security Level |
|--------|----------|----------------|
| **API Key** | CI/CD, automation | Medium |
| **JWT Tokens** | Web UI, CLI | Medium-High |
| **OAuth2** | SSO, enterprise | High |
| **mTLS** | Service-to-service | Highest |

**Features:**
- ✅ Multiple authentication methods
- ✅ Role-based access control (RBAC)
- ✅ API key management
- ✅ OAuth2 SSO support (GitHub, Google, Azure)
- ✅ mTLS for service authentication
- ✅ Automatic token refresh
- ✅ Configurable expiration

---

## Authentication Methods

### 1. API Key Authentication

**Best for:** CI/CD pipelines, automated tools, service accounts

**How it works:**
1. Admin generates API key via `/auth/api-keys` endpoint
2. Client includes key in `X-API-Key` header
3. Server validates key and determines user roles

**Example:**
```bash
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -H 'X-API-Key: fops_xxxxxxxxxxxxxxxxxxxxx' \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

### 2. JWT Bearer Tokens

**Best for:** Web applications, CLI tools, interactive sessions

**How it works:**
1. Client authenticates with username/password
2. Server returns JWT token
3. Client includes token in `Authorization: Bearer <token>` header
4. Server validates token and extracts user info

**Example:**
```bash
# Login
TOKEN=$(curl -X POST http://finopsguard:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Use token
curl -X POST http://finopsguard:8080/mcp/checkCostImpact \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

### 3. OAuth2

**Best for:** Enterprise SSO, GitHub/Google/Azure login

**How it works:**
1. Client redirects to OAuth2 provider
2. User authenticates with provider
3. Provider redirects back with authorization code
4. Server exchanges code for user info and issues JWT

**Supported Providers:**
- GitHub
- Google
- Azure AD

### 4. mTLS (Mutual TLS)

**Best for:** Service-to-service communication, high security environments

**How it works:**
1. Client presents X.509 certificate
2. Server verifies certificate against CA
3. Server extracts user info from certificate
4. Access granted based on certificate CN/organization

---

## Quick Start

### Enable Authentication

```bash
# In .env or environment
AUTH_ENABLED=true
AUTH_MODE=api_key  # or jwt, mtls, oauth2, all

# Generate JWT secret
JWT_SECRET=$(openssl rand -base64 32)

# Set admin password
ADMIN_PASSWORD=<secure-password>
```

### Create API Key (for CI/CD)

```bash
# Login as admin
TOKEN=$(curl -X POST http://finopsguard:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Create API key
API_KEY=$(curl -X POST http://finopsguard:8080/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "CI/CD Pipeline",
    "description": "GitHub Actions automation",
    "roles": ["api"],
    "expires_days": 365
  }' | jq -r '.api_key')

echo "API Key: $API_KEY"
# Save this key securely!
```

### Use in CI/CD

```yaml
# GitHub Actions
env:
  FINOPSGUARD_API_KEY: ${{ secrets.FINOPSGUARD_API_KEY }}

steps:
  - name: Cost Check
    run: |
      curl -X POST $FINOPSGUARD_URL/mcp/checkCostImpact \
        -H "X-API-Key: $FINOPSGUARD_API_KEY" \
        -H 'Content-Type: application/json' \
        -d '{ ... }'
```

---

## API Key Authentication

### Generate API Key

```bash
POST /auth/api-keys
Authorization: Bearer <admin-token>

{
  "name": "Production API Key",
  "description": "For prod deployments",
  "roles": ["api"],
  "expires_days": 365
}
```

**Response:**
```json
{
  "api_key": "fops_xxxxxxxxxxxxxxxxxxxxx",
  "name": "Production API Key",
  "created_at": "2025-10-09T13:00:00",
  "expires_at": "2026-10-09T13:00:00"
}
```

### Use API Key

```bash
# In requests
curl -H 'X-API-Key: fops_xxxxx' http://finopsguard:8080/mcp/...

# In Python
headers = {"X-API-Key": "fops_xxxxx"}
response = requests.post(url, headers=headers, json=payload)

# In JavaScript
const headers = {"X-API-Key": "fops_xxxxx"};
const response = await fetch(url, {headers, ...});
```

### List API Keys

```bash
GET /auth/api-keys
Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "api_keys": [
    {
      "name": "CI/CD Pipeline",
      "roles": ["api"],
      "created_at": "2025-10-09T13:00:00",
      "expires_at": "2026-10-09T13:00:00",
      "last_used": "2025-10-09T14:30:00"
    }
  ]
}
```

### Revoke API Key

```bash
DELETE /auth/api-keys/{api_key}
Authorization: Bearer <admin-token>
```

---

## JWT Bearer Tokens

### Login

```bash
POST /auth/login

{
  "username": "admin",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Use Token

```bash
# HTTP header
Authorization: Bearer <token>

# cURL example
curl -H 'Authorization: Bearer eyJhbG...' http://finopsguard:8080/mcp/...
```

### Refresh Token

```bash
POST /auth/refresh
Authorization: Bearer <old-token>
```

**Response:**
```json
{
  "access_token": "<new-token>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Get Current User

```bash
GET /auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "Administrator",
  "roles": ["admin"],
  "disabled": false
}
```

---

## OAuth2 Integration

### Supported Providers

- **GitHub**: Enterprise and public GitHub
- **Google**: Google Workspace and Gmail
- **Azure AD**: Microsoft 365 and Azure AD

### Configuration

```bash
# Enable OAuth2
OAUTH2_ENABLED=true
OAUTH2_PROVIDER=github  # or google, azure

# GitHub OAuth2
OAUTH2_CLIENT_ID=<your-client-id>
OAUTH2_CLIENT_SECRET=<your-client-secret>
OAUTH2_REDIRECT_URI=http://finopsguard:8080/auth/oauth2/callback

# Google OAuth2
OAUTH2_CLIENT_ID=<client-id>.apps.googleusercontent.com
OAUTH2_CLIENT_SECRET=<client-secret>
OAUTH2_REDIRECT_URI=http://finopsguard:8080/auth/oauth2/callback

# Azure AD OAuth2
OAUTH2_CLIENT_ID=<application-id>
OAUTH2_CLIENT_SECRET=<client-secret>
OAUTH2_ISSUER=<tenant-id>
OAUTH2_REDIRECT_URI=http://finopsguard:8080/auth/oauth2/callback
```

### OAuth2 Flow

**1. Initiate Login:**
```bash
GET /auth/oauth2/login
```

**Response:**
```json
{
  "authorization_url": "https://github.com/login/oauth/authorize?client_id=..."
}
```

**2. Redirect user to authorization_url**

**3. Provider redirects to callback:**
```
GET /auth/oauth2/callback?code=xxxxx
```

**4. Server returns JWT token:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### GitHub OAuth App Setup

1. Go to https://github.com/settings/developers
2. Create New OAuth App
3. Set Authorization callback URL: `http://your-domain/auth/oauth2/callback`
4. Copy Client ID and Client Secret
5. Configure FinOpsGuard with credentials

### Google OAuth Setup

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Add authorized redirect URI: `http://your-domain/auth/oauth2/callback`
4. Copy Client ID and Client Secret
5. Configure FinOpsGuard with credentials

---

## mTLS (Mutual TLS)

### Configuration

```bash
# Enable mTLS
MTLS_ENABLED=true
MTLS_CA_CERT=/etc/finopsguard/certs/ca.crt
MTLS_VERIFY_CLIENT=true
```

### Generate Certificates

**1. Create CA:**
```bash
# Generate CA private key
openssl genrsa -out ca.key 4096

# Generate CA certificate
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
  -out ca.crt -subj "/CN=FinOpsGuard CA/O=FinOpsGuard"
```

**2. Create Client Certificate:**
```bash
# Generate client private key
openssl genrsa -out client.key 4096

# Generate CSR
openssl req -new -key client.key -out client.csr \
  -subj "/CN=ci-pipeline/O=FinOpsGuard Users"

# Sign with CA
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt -days 365 -sha256
```

**3. Use in Requests:**
```bash
curl --cert client.crt --key client.key --cacert ca.crt \
  https://finopsguard:8080/mcp/checkCostImpact \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name finopsguard.example.com;
    
    # Server certificate
    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    
    # Client certificate verification
    ssl_client_certificate /etc/nginx/certs/ca.crt;
    ssl_verify_client on;
    ssl_verify_depth 2;
    
    location / {
        proxy_pass http://finopsguard:8080;
        proxy_set_header X-SSL-Client-Cert $ssl_client_cert;
        proxy_set_header X-SSL-Client-S-DN $ssl_client_s_dn;
    }
}
```

---

## Role-Based Access Control

### Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access (all operations) |
| **user** | Read/write policies, run analyses |
| **viewer** | Read-only access |
| **api** | API access (for service accounts) |

### Permission Matrix

| Operation | Admin | User | Viewer | API |
|-----------|-------|------|--------|-----|
| Check Cost Impact | ✅ | ✅ | ✅ | ✅ |
| List Policies | ✅ | ✅ | ✅ | ✅ |
| Create Policy | ✅ | ✅ | ❌ | ❌ |
| Update Policy | ✅ | ✅ | ❌ | ❌ |
| Delete Policy | ✅ | ❌ | ❌ | ❌ |
| Manage API Keys | ✅ | ❌ | ❌ | ❌ |
| Flush Cache | ✅ | ❌ | ❌ | ❌ |
| View Metrics | ✅ | ✅ | ✅ | ✅ |

### Enforce Role in Code

```python
from fastapi import Depends
from finopsguard.auth.middleware import require_role, require_admin
from finopsguard.auth.models import Role, User

# Require specific role
@app.post("/admin/operation")
async def admin_operation(user: User = Depends(require_admin)):
    # Only admins can access
    pass

# Require any authenticated user
@app.get("/data")
async def get_data(user: User = Depends(require_auth)):
    # Any authenticated user
    pass
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_ENABLED` | false | Enable authentication |
| `AUTH_MODE` | api_key | Auth method (api_key, jwt, mtls, oauth2, all) |
| `JWT_SECRET` | (required) | Secret key for JWT signing |
| `JWT_EXPIRE_MINUTES` | 60 | JWT token expiration time |
| `ADMIN_PASSWORD` | admin | Default admin password |
| `API_KEY` | (none) | Environment-based API key |
| `OAUTH2_ENABLED` | false | Enable OAuth2 |
| `OAUTH2_PROVIDER` | (none) | OAuth2 provider (github/google/azure) |
| `OAUTH2_CLIENT_ID` | (none) | OAuth2 client ID |
| `OAUTH2_CLIENT_SECRET` | (none) | OAuth2 client secret |
| `OAUTH2_ISSUER` | (none) | OAuth2 issuer (for Azure) |
| `OAUTH2_REDIRECT_URI` | (none) | OAuth2 callback URL |
| `MTLS_ENABLED` | false | Enable mTLS |
| `MTLS_CA_CERT` | /etc/finopsguard/certs/ca.crt | CA certificate path |
| `MTLS_VERIFY_CLIENT` | true | Verify client certificates |

### Docker Compose

```yaml
services:
  finopsguard:
    environment:
      # Enable authentication
      - AUTH_ENABLED=true
      - AUTH_MODE=api_key
      - JWT_SECRET=${JWT_SECRET}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      
      # Optional: OAuth2
      - OAUTH2_ENABLED=true
      - OAUTH2_PROVIDER=github
      - OAUTH2_CLIENT_ID=${OAUTH2_CLIENT_ID}
      - OAUTH2_CLIENT_SECRET=${OAUTH2_CLIENT_SECRET}
      
      # Optional: mTLS
      - MTLS_ENABLED=true
      - MTLS_CA_CERT=/etc/finopsguard/certs/ca.crt
    
    volumes:
      # Mount certificates for mTLS
      - ./certs:/etc/finopsguard/certs:ro
```

### Kubernetes

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: finopsguard-auth-secret
  namespace: finopsguard
type: Opaque
stringData:
  JWT_SECRET: "<base64-random-string>"
  ADMIN_PASSWORD: "<secure-password>"
  OAUTH2_CLIENT_SECRET: "<oauth2-secret>"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: finopsguard-auth-config
  namespace: finopsguard
data:
  AUTH_ENABLED: "true"
  AUTH_MODE: "api_key"
  JWT_EXPIRE_MINUTES: "60"
  OAUTH2_ENABLED: "true"
  OAUTH2_PROVIDER: "github"
  OAUTH2_CLIENT_ID: "<client-id>"
```

---

## Integration Examples

### Python Client

```python
import httpx

class AuthenticatedClient:
    def __init__(self, base_url: str, api_key: str = None, token: str = None):
        self.client = httpx.Client(base_url=base_url)
        self.api_key = api_key
        self.token = token
    
    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def check_cost(self, payload):
        return self.client.post(
            "/mcp/checkCostImpact",
            json=payload,
            headers=self._get_headers()
        ).json()

# Using API key
client = AuthenticatedClient(
    "http://finopsguard:8080",
    api_key="fops_xxxxx"
)

# Using JWT
client = AuthenticatedClient(
    "http://finopsguard:8080",
    token="eyJhbGc..."
)
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class FinOpsClient {
    constructor(baseURL, apiKey) {
        this.client = axios.create({
            baseURL,
            headers: {
                'X-API-Key': apiKey,
                'Content-Type': 'application/json'
            }
        });
    }
    
    async checkCost(payload) {
        const response = await this.client.post('/mcp/checkCostImpact', payload);
        return response.data;
    }
}

const client = new FinOpsClient('http://finopsguard:8080', 'fops_xxxxx');
```

### cURL

```bash
# API Key
curl -H 'X-API-Key: fops_xxxxx' http://finopsguard:8080/mcp/checkCostImpact ...

# JWT
curl -H 'Authorization: Bearer eyJhbGc...' http://finopsguard:8080/mcp/checkCostImpact ...

# mTLS
curl --cert client.crt --key client.key --cacert ca.crt https://finopsguard:8080/mcp/checkCostImpact ...
```

---

## Security Best Practices

### 1. Use Strong Secrets

```bash
# Generate secure JWT secret
openssl rand -base64 32

# Generate secure password
openssl rand -base64 24
```

### 2. Rotate API Keys

```bash
# Create new key
NEW_KEY=$(curl -X POST .../auth/api-keys ...)

# Update CI/CD secrets
# ...

# Revoke old key
curl -X DELETE .../auth/api-keys/$OLD_KEY
```

### 3. Use HTTPS in Production

```bash
# Always use HTTPS
FINOPSGUARD_URL=https://finopsguard.company.com

# Verify certificates
curl --cacert ca.crt https://...
```

### 4. Limit Token Expiration

```bash
# Short-lived tokens for interactive use
JWT_EXPIRE_MINUTES=30

# Longer-lived for automation
JWT_EXPIRE_MINUTES=1440  # 24 hours
```

### 5. Monitor Authentication

```promql
# Failed authentication attempts
rate(finops_auth_failures_total[5m]) > 10

# Active sessions
finops_active_sessions

# API key usage
finops_api_key_requests_total{key_name="ci-pipeline"}
```

---

## Troubleshooting

### Authentication Fails

**Error: `authentication_required`**

```bash
# Check if auth is enabled
curl http://finopsguard:8080/healthz

# Verify API key
curl -H 'X-API-Key: fops_xxxxx' http://finopsguard:8080/auth/me

# Verify JWT token
curl -H 'Authorization: Bearer eyJ...' http://finopsguard:8080/auth/me
```

**Error: `invalid_credentials`**

```bash
# Check username/password
curl -X POST http://finopsguard:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}'
```

**Error: `insufficient_permissions`**

```bash
# Check user roles
curl -H 'Authorization: Bearer ...' http://finopsguard:8080/auth/me

# Verify role requirements
curl http://finopsguard:8080/auth/roles
```

### OAuth2 Issues

**Error: `oauth2_not_configured`**

```bash
# Check OAuth2 configuration
echo $OAUTH2_ENABLED
echo $OAUTH2_PROVIDER
echo $OAUTH2_CLIENT_ID
```

**Error: `oauth2_authentication_failed`**

```bash
# Check OAuth2 app settings
# Verify redirect URI matches
# Check client ID/secret are correct
```

### mTLS Issues

**Error: Certificate verification failed**

```bash
# Verify certificate is valid
openssl x509 -in client.crt -text -noout

# Check expiration
openssl x509 -in client.crt -noout -dates

# Verify against CA
openssl verify -CAfile ca.crt client.crt
```

---

## Migration Guide

### Enabling Auth on Existing Deployment

**1. Generate secrets:**
```bash
export JWT_SECRET=$(openssl rand -base64 32)
export ADMIN_PASSWORD=$(openssl rand -base64 16)
```

**2. Update configuration:**
```bash
# Add to .env
echo "AUTH_ENABLED=true" >> .env
echo "AUTH_MODE=api_key" >> .env
echo "JWT_SECRET=$JWT_SECRET" >> .env
echo "ADMIN_PASSWORD=$ADMIN_PASSWORD" >> .env
```

**3. Restart services:**
```bash
docker-compose restart finopsguard
```

**4. Create API keys for existing integrations:**
```bash
# Login
TOKEN=$(curl -X POST http://finopsguard:8080/auth/login \
  -d '{"username":"admin","password":"'$ADMIN_PASSWORD'"}' | jq -r '.access_token')

# Create API key for CI/CD
API_KEY=$(curl -X POST http://finopsguard:8080/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"GitHub Actions","roles":["api"]}' | jq -r '.api_key')

# Update CI/CD secrets
gh secret set FINOPSGUARD_API_KEY --body "$API_KEY"
```

**5. Update clients to use API keys**

---

## API Reference

### Authentication Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/auth/login` | POST | No | Login with username/password |
| `/auth/me` | GET | Yes | Get current user info |
| `/auth/refresh` | POST | Yes | Refresh access token |
| `/auth/api-keys` | POST | Admin | Create API key |
| `/auth/api-keys` | GET | Admin | List API keys |
| `/auth/api-keys/{key}` | DELETE | Admin | Revoke API key |
| `/auth/oauth2/login` | GET | No | Initiate OAuth2 flow |
| `/auth/oauth2/callback` | GET | No | OAuth2 callback |
| `/auth/roles` | GET | Yes | List available roles |

---

## See Also

- [Deployment Guide](./deployment.md)
- [Integration Examples](./integrations.md)
- [Security Best Practices](./security.md)
- [API Documentation](http://localhost:8080/docs)

