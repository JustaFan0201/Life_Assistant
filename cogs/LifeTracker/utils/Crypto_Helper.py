import os
from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY

class Crypto_Helper:
    _key = ENCRYPTION_KEY
    if not _key:
        raise ValueError("🚨 系統錯誤：.env 檔案中遺失 ENCRYPTION_KEY 設定！")
        
    _fernet = Fernet(_key.encode('utf-8'))

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """加密明文字串，回傳加密後的字串"""
        return cls._fernet.encrypt(plaintext.encode('utf-8')).decode('utf-8')

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """解密字串，回傳明文"""
        return cls._fernet.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')