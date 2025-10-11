"""mTLS (Mutual TLS) certificate validation."""

import os
import logging
from typing import Optional
from datetime import datetime, UTC
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID

from .models import User, Role

logger = logging.getLogger(__name__)

# Configuration
MTLS_ENABLED = os.getenv("MTLS_ENABLED", "false").lower() == "true"
CA_CERT_PATH = os.getenv("MTLS_CA_CERT", "/etc/finopsguard/certs/ca.crt")
VERIFY_CLIENT_CERT = os.getenv("MTLS_VERIFY_CLIENT", "true").lower() == "true"


def load_ca_certificate() -> Optional[x509.Certificate]:
    """
    Load CA certificate for client verification.
    
    Returns:
        CA certificate or None if not available
    """
    if not MTLS_ENABLED or not os.path.exists(CA_CERT_PATH):
        return None
    
    try:
        with open(CA_CERT_PATH, "rb") as f:
            cert_data = f.read()
        return x509.load_pem_x509_certificate(cert_data, default_backend())
    except Exception as e:
        logger.error(f"Failed to load CA certificate: {e}")
        return None


def verify_client_cert(cert_pem: str) -> Optional[dict]:
    """
    Verify client certificate.
    
    Args:
        cert_pem: PEM-encoded client certificate
        
    Returns:
        Certificate information if valid, None otherwise
    """
    if not MTLS_ENABLED:
        return None
    
    try:
        # Load client certificate
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        
        # Extract information
        subject = cert.subject
        common_name = subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        organization = None
        org_attrs = subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
        if org_attrs:
            organization = org_attrs[0].value
        
        # Check expiration
        # Note: cert dates are naive UTC, so we use replace(tzinfo=None) for comparison
        current_time = datetime.now(UTC).replace(tzinfo=None)
        if current_time > cert.not_valid_after:
            logger.warning(f"Client certificate expired for {common_name}")
            return None
        
        if current_time < cert.not_valid_before:
            logger.warning(f"Client certificate not yet valid for {common_name}")
            return None
        
        # In production, you would verify against CA and check CRLs
        # For now, just extract information
        
        return {
            "common_name": common_name,
            "organization": organization,
            "serial_number": str(cert.serial_number),
            "not_valid_before": cert.not_valid_before.isoformat(),
            "not_valid_after": cert.not_valid_after.isoformat(),
            "issuer": cert.issuer.rfc4514_string()
        }
    except Exception as e:
        logger.error(f"Client certificate verification failed: {e}")
        return None


def get_cert_user(cert_pem: str) -> Optional[User]:
    """
    Get user from client certificate.
    
    Args:
        cert_pem: PEM-encoded client certificate
        
    Returns:
        User object if valid, None otherwise
    """
    cert_info = verify_client_cert(cert_pem)
    if cert_info is None:
        return None
    
    # Determine roles based on organization or common name
    # In production, this would be stored in a database
    roles = [Role.USER]
    if cert_info.get("organization") == "FinOpsGuard Admins":
        roles = [Role.ADMIN]
    
    return User(
        username=f"cert_{cert_info['common_name'].replace(' ', '_').lower()}",
        full_name=cert_info['common_name'],
        roles=roles,
        disabled=False
    )


def extract_cert_from_request(headers: dict) -> Optional[str]:
    """
    Extract client certificate from request headers.
    
    Args:
        headers: Request headers
        
    Returns:
        PEM-encoded certificate or None
    """
    # Different proxies use different headers
    cert_headers = [
        "X-SSL-Client-Cert",
        "X-Client-Cert",
        "SSL_CLIENT_CERT"
    ]
    
    for header in cert_headers:
        if header in headers:
            cert_pem = headers[header]
            # Nginx format (spaces replaced with tabs)
            cert_pem = cert_pem.replace('\t', '\n')
            return cert_pem
    
    return None

