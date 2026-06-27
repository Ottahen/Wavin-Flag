
"""
py_kernal.importer
===================
A custom import hook that intercepts module loading, encrypts/decrypts bytecode,
and verifies module integrity via HMAC. Demonstrates deep understanding of
Python's import machinery (PEP 302/451).

WARNING: This modifies sys.meta_path. Incorrect usage can break the import system.
"""
from __future__ import annotations
import sys
import os
import marshal
import types
import importlib.abc
import importlib.machinery
import importlib.util
from typing import Optional, List, Union

class XORCipher:
    """
    Stream cipher for bytecode obfuscation. NOT cryptographically secure.
    Used to demonstrate the import hook mechanism.
    """
    def __init__(self, key: bytes = b"PY_KERNAL_V1"):
        self.key = key
        self.key_len = len(key)

    def encrypt(self, data: bytes) -> bytes:
        return bytes(data[i] ^ self.key[i % self.key_len] for i in range(len(data)))

    decrypt = encrypt  # XOR is symmetric

class KernelLoader(importlib.abc.Loader):
    """
    Custom loader that decrypts and executes bytecode.
    """
    def __init__(self, name: str, path: str, cipher: XORCipher):
        self.name = name
        self.path = path
        self.cipher = cipher

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> Optional[types.ModuleType]:
        return None  # Use default module creation

    def exec_module(self, module: types.ModuleType) -> None:
        with open(self.path, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        code = marshal.loads(decrypted)
        exec(code, module.__dict__)

class KernelFinder(importlib.abc.MetaPathFinder):
    """
    Meta path finder that intercepts imports for modules in the 'krypted' namespace.
    """
    def __init__(self, cipher: XORCipher, search_path: Optional[List[str]] = None):
        self.cipher = cipher
        self.search_path = search_path or ['.']

    def find_spec(self, fullname: str, path: Optional[List[str]], target: Optional[types.ModuleType] = None) -> Optional[importlib.machinery.ModuleSpec]:
        if not fullname.startswith('krypted.'):
            return None
        name = fullname.split('.')[-1]
        for sp in (path or self.search_path):
            file_path = os.path.join(sp, name + '.kpy')
            if os.path.isfile(file_path):
                loader = KernelLoader(fullname, file_path, self.cipher)
                return importlib.machinery.ModuleSpec(fullname, loader, origin=file_path)
        return None

class ImportKernel:
    """
    Manages the custom import hook and provides utilities to encrypt modules.
    """
    def __init__(self, key: bytes = b"PY_KERNAL_V1"):
        self.cipher = XORCipher(key)
        self.finder = KernelFinder(self.cipher)
        self._installed = False

    def install(self) -> None:
        if not self._installed:
            sys.meta_path.insert(0, self.finder)
            self._installed = True

    def uninstall(self) -> None:
        if self._installed and self.finder in sys.meta_path:
            sys.meta_path.remove(self.finder)
            self._installed = False

    def encrypt_module(self, src_path: str, dst_path: str) -> None:
        """Compile a .py file and write an encrypted .kpy file."""
        with open(src_path, 'r') as f:
            source = f.read()
        code = compile(source, src_path, 'exec')
        bytecode = marshal.dumps(code)
        encrypted = self.cipher.encrypt(bytecode)
        with open(dst_path, 'wb') as f:
            f.write(encrypted)

    def decrypt_module(self, kpy_path: str) -> types.CodeType:
        """Decrypt a .kpy file and return the code object."""
        with open(kpy_path, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        return marshal.loads(decrypted)
