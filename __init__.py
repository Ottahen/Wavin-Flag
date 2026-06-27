
"""
py_kernal
==========
The Python Kernel — A pure-Python systems programming suite.

Modules:
    vm          Register-based virtual machine with tracing JIT
    metal       Metaclass kernel with C3 MRO, AOP, and contracts
    memory      Raw C-level memory introspection via ctypes
    ast_engine  AST transformation engine (TCO, CPS, memoization)
    importer    Encrypted bytecode import hook

WARNING:
    This package uses CPython implementation details, frame manipulation,
    raw memory access, and import system hooks. It can crash the interpreter
    or corrupt the import machinery if misused. For educational and
    research purposes only.

    Only professionals who have mastered Python internals should attempt
    to modify or extend this code.
"""

__version__ = "1.0.0"
__author__ = "The Kernel Architect"

from .vm import VirtualMachine, JITCompiler, OpCode, Instruction
from .metal import KernelMeta, C3Linearization, StructuralProtocol, aspect
from .memory import MemoryKernel, ImmortalBypass
from .ast_engine import ASTKernel, TCOTransformer, CPSTransformer
from .importer import ImportKernel, XORCipher, KernelFinder, KernelLoader

__all__ = [
    "VirtualMachine", "JITCompiler", "OpCode", "Instruction",
    "KernelMeta", "C3Linearization", "StructuralProtocol", "aspect",
    "MemoryKernel", "ImmortalBypass",
    "ASTKernel", "TCOTransformer", "CPSTransformer",
    "ImportKernel", "XORCipher", "KernelFinder", "KernelLoader",
]
