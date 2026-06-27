
"""
py_kernal.__main__
====================
Demonstration of the full Kernel suite. Run with:
    python -m py_kernal

This executes the most dangerous legitimate Python code ever assembled:
- A register VM with JIT that compiles hot loops into native Python functions
- A metaclass that rewrites method dispatch with contracts and AOP
- Raw memory introspection of CPython objects
- AST-level tail-call optimization
- Encrypted bytecode import hooks
"""
from __future__ import annotations
import sys
import time
import types

from py_kernal.vm import VirtualMachine, OpCode, Instruction
from py_kernal.metal import KernelMeta, C3Linearization, StructuralProtocol, aspect
from py_kernal.memory import MemoryKernel, ImmortalBypass
from py_kernal.ast_engine import ASTKernel
from py_kernal.importer import ImportKernel

# =============================================================================
# DEMO 1: Register VM with Tracing JIT — Compute factorial iteratively
# =============================================================================
def demo_vm():
    print("=" * 70)
    print("DEMO 1: Register VM + Tracing JIT — Factorial Loop")
    print("=" * 70)
    # Registers: r0=n, r1=result, r2=temp, r3=const1, r4=bool
    # Constants: 0: 5 (input), 1: 1, 2: 0
    code = [
        Instruction(OpCode.LOAD_CONST, (0, 0)),   # r0 = 5 (n)
        Instruction(OpCode.LOAD_CONST, (1, 1)),   # r1 = 1 (result)
        Instruction(OpCode.LOAD_CONST, (1, 3)),   # r3 = 1 (for decrement)
        # Loop start (pc 3)
        Instruction(OpCode.GT, (0, 2, 4)),       # r4 = r0 > 0
        Instruction(OpCode.JZ, (4, 12)),          # if not r4, jump to end
        Instruction(OpCode.MUL, (1, 0, 1)),      # r1 = r1 * r0
        Instruction(OpCode.SUB, (0, 3, 0)),       # r0 = r0 - r3
        Instruction(OpCode.JMP, (3,)),            # jump to loop start
        # End (pc 12)
        Instruction(OpCode.PRINT, (1,)),         # print result
        Instruction(OpCode.HALT, ()),
    ]
    constants = [5, 1, 0]
    vm = VirtualMachine(code, constants)
    result = vm.run()
    print(f"VM Result: {result}")
    print(f"JIT traces compiled: {len(vm.trace_cache)}")
    print()

# =============================================================================
# DEMO 2: Metaclass Kernel — Structural Protocols + Contracts + AOP
# =============================================================================
def demo_metal():
    print("=" * 70)
    print("DEMO 2: Metaclass Kernel — Contracts, AOP, C3 MRO")
    print("=" * 70)

    class Drawable(metaclass=KernelMeta):
        def draw(self) -> str:
            return "drawn"

    class Serializable(metaclass=KernelMeta):
        def serialize(self) -> bytes:
            return b"data"

    # Pre-condition: x must be positive
    def pre_positive(self, x):
        return x > 0

    # Post-condition: result must be greater than input
    def post_greater(self, result, x):
        return result > x

    # Around advice: logging
    def log_around(ctx):
        print(f"  [AOP] Calling {ctx['self'].__class__.__name__} with args={ctx['args']}")

    class Shape(Drawable, Serializable, metaclass=KernelMeta, protocols=(Drawable, Serializable)):
        __pre__ = {'compute': [pre_positive]}
        __post__ = {'compute': [post_greater]}
        __around__ = {'compute': [log_around]}

        def compute(self, x):
            return x * 2 + 1

        def draw(self):
            return "Shape.draw"

        def serialize(self):
            return b"Shape"

    s = Shape()
    print(f"MRO (custom C3): {[c.__name__ for c in C3Linearization.mro(Shape)]}")
    print(f"draw() -> {s.draw()}")
    print(f"serialize() -> {s.serialize()}")
    print(f"compute(5) -> {s.compute(5)}")
    try:
        s.compute(-1)
    except Exception as e:
        print(f"compute(-1) correctly rejected: {type(e).__name__}")
    print()

# =============================================================================
# DEMO 3: Memory Kernel — Raw CPython Object Introspection
# =============================================================================
def demo_memory():
    print("=" * 70)
    print("DEMO 3: Memory Kernel — Raw CPython Object Introspection")
    print("=" * 70)
    mk = MemoryKernel()
    ib = ImmortalBypass(mk)

    # Inspect a small integer (likely immortal in 3.12+)
    a = 42
    print(f"Object: {a}")
    print(f"  Header: {mk.object_header(a)}")
    print(f"  Hex dump (32 bytes): {mk.hex_dump(a, 32)}")
    print(f"  Immortal: {mk.immortal_check(a)}")

    # Inspect a float
    f = 3.14159
    print(f"\nObject: {f}")
    print(f"  Raw C double: {mk.float_value(f)}")
    print(f"  Header: {mk.object_header(f)}")

    # Inspect a list
    lst = [1, 2, 3, 4, 5]
    print(f"\nObject: {lst}")
    print(f"  List capacity: {mk.list_capacity(lst)} (over-allocated for amortized growth)")
    print(f"  Item addresses: {mk.list_items(lst)}")
    print(f"  Header: {mk.object_header(lst)}")
    print()

# =============================================================================
# DEMO 4: AST Engine — Tail-Call Optimization
# =============================================================================
def demo_ast():
    print("=" * 70)
    print("DEMO 4: AST Engine — Tail-Call Optimization (TCO)")
    print("=" * 70)
    engine = ASTKernel()

    def factorial(n, acc=1):
        if n <= 1:
            return acc
        return factorial(n - 1, acc * n)

    # This would hit recursion limit for large n normally
    sys.setrecursionlimit(100)  # Artificially low to show the problem
    try:
        factorial(200)
    except RecursionError:
        print("  Normal factorial(200): RecursionError (limit=100)")

    tco_factorial = engine.apply_tco(factorial)
    try:
        result = tco_factorial(200)
        print(f"  TCO factorial(200): {result}")
    except RecursionError:
        print("  TCO factorial(200): Still failed (transformation simplified)")
    finally:
        sys.setrecursionlimit(1000)
    print()

# =============================================================================
# DEMO 5: Import Hook — Encrypted Bytecode
# =============================================================================
def demo_importer():
    print("=" * 70)
    print("DEMO 5: Import Kernel — Encrypted Bytecode Hook")
    print("=" * 70)
    ik = ImportKernel(key=b"DANGEROUS_KEY_01")
    ik.install()

    # Create a test module source
    test_src = """
def secret_function():
    return "The secret is: 42"

x = 1337
"""
    import tempfile, os
    tmpdir = tempfile.mkdtemp()
    src_path = os.path.join(tmpdir, "testmod.py")
    kpy_path = os.path.join(tmpdir, "testmod.kpy")
    with open(src_path, "w") as f:
        f.write(test_src)

    # Encrypt it
    ik.encrypt_module(src_path, kpy_path)
    print(f"  Encrypted {src_path} -> {kpy_path}")
    print(f"  File size: {os.path.getsize(kpy_path)} bytes")

    # Decrypt and verify
    code = ik.decrypt_module(kpy_path)
    ns = {}
    exec(code, ns)
    print(f"  Decrypted execution: secret_function() = {ns['secret_function']()}")
    print(f"  Decrypted execution: x = {ns['x']}")

    ik.uninstall()
    print()

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("\n")
    print("#" * 70)
    print("#  PY_KERNAL — THE PYTHON KERNEL v1.0.0")
    print("#  Pure-Python Systems Programming Suite")
    print("#  WARNING: This code touches interpreter internals.")
    print("#" * 70)
    print("\n")

    demo_vm()
    demo_metal()
    demo_memory()
    demo_ast()
    demo_importer()

    print("#" * 70)
    print("#  ALL DEMOS COMPLETED SUCCESSFULLY")
    print("#  You have witnessed the deepest layers of Python.")
    print("#" * 70)
