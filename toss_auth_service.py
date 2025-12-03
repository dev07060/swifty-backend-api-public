"""
Toss Cert Authentication Service.
Handles OAuth token management, authentication requests, and user data retrieval.
"""
import httpx
import logging
import base64
import uuid
import os
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as padding_sym
from cryptography.hazmat.primitives.asymmetric import padding as padding_asym
from cryptography.hazmat.primitives import serialization
import json

from toss_auth_models import (
    TossAccessTokenResponse,
    TossAuthRequestResponse,
    TossAuthStatusResponse,
    TossAuthResultResponse,
    DecryptedUserData,
)

logger = logging.getLogger(__name__)


class TossAuthError(Exception):
    """Custom exception for Toss authentication errors."""
    def __init__(self, message: str, error_code: Optional[str] = None, status_code: Optional[int] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class TossAuthService:
    """Service for handling Toss Cert authentication flow."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        oauth_base_url: str = "https://oauth2.cert.toss.im",
        cert_base_url: str = "https://cert.toss.im",
        timeout: int = 30,
    ):
        """
        Initialize Toss Auth Service.
        
        Args:
            client_id: Toss Cert client ID
            client_secret: Toss Cert client secret
            oauth_base_url: Base URL for OAuth API
            cert_base_url: Base URL for Cert API
            timeout: Request timeout in seconds
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_base_url = oauth_base_url.rstrip("/")
        self.cert_base_url = cert_base_url.rstrip("/")
        self.timeout = timeout
        
        # Token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[int] = None
        
        logger.info("TossAuthService initialized")
    
    def _generate_session_key(self):
        """
        Generate a session key for AES encryption.
        
        Returns:
            Tuple of (formatted_session_key, aes_key, iv)
        """
        # Generate a random AES-256 key (32 bytes) and IV (16 bytes)
        aes_key = os.urandom(32)
        iv = os.urandom(16)
        
        # Load Toss Public Key
        # In production, this should be loaded from a file or env var
        public_key_pem_b64 = os.getenv("TEST_BASE64_PUBLIC_KEY")
        if not public_key_pem_b64:
             # Fallback or error
             logger.error("TEST_BASE64_PUBLIC_KEY not found in env")
             raise TossAuthError("Missing Toss Public Key configuration")

        try:
            # Add headers if missing (though user provided base64 body)
            # The key provided is a base64 encoded DER/PEM body.
            # We need to format it as PEM.
            public_key_pem = (
                "-----BEGIN PUBLIC KEY-----\n" + 
                public_key_pem_b64 + 
                "\n-----END PUBLIC KEY-----"
            ).encode("utf-8")
            
            public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())
            
            # Encrypt AES Key + IV using RSA
            # Toss uses PKCS1v15 padding
            encrypted_data = public_key.encrypt(
                aes_key + iv,
                padding_asym.PKCS1v15()
            )
            
            session_uuid = str(uuid.uuid4())
            encrypted_b64 = base64.b64encode(encrypted_data).decode("utf-8")
            
            formatted_key = f"v1${session_uuid}${encrypted_b64}"
            return formatted_key, aes_key, iv
            
        except Exception as e:
            logger.error(f"Session key generation error: {e}")
            raise TossAuthError(f"Failed to generate session key: {str(e)}")
    
    def _decrypt_value(self, encrypted_value: str, aes_key: bytes, iv: bytes) -> str:
        """
        Decrypt a value from Toss API response.
        
        Args:
            encrypted_value: Encrypted value in format v1${uuid}${encrypted_data}
            aes_key: AES key used for session
            iv: IV used for session
            
        Returns:
            Decrypted plain text value
        """
        try:
            # Parse session key to get encrypted data
            parts = encrypted_value.split("$")
            if len(parts) != 3 or parts[0] != "v1":
                # If it's not in v1 format, maybe it's plain text or error?
                # But Toss spec says it's v1 format.
                raise ValueError("Invalid encrypted value format")
            
            encrypted_data = base64.b64decode(parts[2])
            
            # Decrypt using AES-CBC
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Update and finalize
            padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Unpad (PKCS7)
            # AES block size is 128 bits (16 bytes)
            unpadder = padding_sym.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            
            return data.decode("utf-8")
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise TossAuthError(f"Failed to decrypt value: {str(e)}")

    async def get_auth_result_with_decryption(self, tx_id: str) -> Dict[str, Any]:
        """
        Get authentication result and decrypt user data in one go.
        
        Args:
            tx_id: Transaction ID
            
        Returns:
            Dict containing result response and decrypted user data
        """
        access_token = await self.get_access_token()
        
        # Generate session key and keep the AES key/IV
        session_key, aes_key, iv = self._generate_session_key()
        
        url = f"{self.cert_base_url}/api/v2/sign/user/auth/id/result"
        payload = {
            "txId": tx_id,
            "sessionKey": session_key,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                )
                
                result_response = TossAuthResultResponse(**response.json())
                
                if result_response.resultType == "FAIL":
                    error = result_response.error
                    logger.error(f"Result retrieval failed: {error.errorCode} - {error.reason}")
                    
                    # Map specific error codes to HTTP status codes
                    status_code = response.status_code
                    if error.errorCode == "CE3102":
                        status_code = 400
                        
                    raise TossAuthError(
                        error.reason,
                        error_code=error.errorCode,
                        status_code=status_code
                    )
                
                logger.info("Auth result retrieved successfully")
                
                # Decrypt user data immediately using the keys we have
                personal_data = result_response.success.personalData
                
                decrypted_name = self._decrypt_value(personal_data.name, aes_key, iv)
                decrypted_ci = self._decrypt_value(personal_data.ci, aes_key, iv) if personal_data.ci else None
                decrypted_di = self._decrypt_value(personal_data.di, aes_key, iv) if personal_data.di else None
                decrypted_birthday = self._decrypt_value(personal_data.birthday, aes_key, iv) if personal_data.birthday else None
                decrypted_gender = self._decrypt_value(personal_data.gender, aes_key, iv) if personal_data.gender else None
                
                decrypted_data = DecryptedUserData(
                    name=decrypted_name,
                    ci=decrypted_ci,
                    di=decrypted_di,
                    birthday=decrypted_birthday,
                    gender=decrypted_gender
                )
                
                return {
                    "result_response": result_response,
                    "decrypted_data": decrypted_data
                }
                
        except httpx.TimeoutException:
            logger.error("Result retrieval timed out")
            raise TossAuthError("Result retrieval timed out", status_code=504)
        except TossAuthError:
            raise
        except Exception as e:
            logger.error(f"Result retrieval error: {e}")
            raise TossAuthError(f"Result retrieval failed: {str(e)}")
            
    # Deprecated methods kept for compatibility but should not be used for new flow
    async def get_auth_result(self, tx_id: str) -> TossAuthResultResponse:
        """Deprecated: Use get_auth_result_with_decryption instead"""
        # This method cannot decrypt properly because it loses the AES key
        # For backward compatibility, we'll generate a dummy key but decryption will fail
        # unless we change the architecture.
        # Better to raise error or warn.
        logger.warning("get_auth_result called directly - decryption will fail!")
        return (await self.get_auth_result_with_decryption(tx_id))["result_response"]

    def decrypt_user_data(self, result: TossAuthResultResponse) -> DecryptedUserData:
        """Deprecated: Cannot decrypt without AES key"""
        raise NotImplementedError("Use get_auth_result_with_decryption to get decrypted data directly")

