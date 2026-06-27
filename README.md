
# PY_KERNAL — The Python Kernel

> **WARNING:** This repository contains code that manipulates CPython internals, raw memory, and the import system. It is for **educational and research purposes only**. Misuse can crash the interpreter or corrupt the runtime.

## Overview

`py_kernal` is a pure-Python systems programming suite that reimplements and hooks into the deepest layers of the CPython runtime. It is not a library for production use — it is a demonstration of what is possible when you have mastered Python at the C-API, bytecode, AST, and metaclass levels.

## Modules

### `vm.py` — Register-Based Virtual Machine with Tracing JIT
- Custom register-based bytecode format (256 registers)
- Tracing JIT compiler that records hot loops and emits optimized Python functions
- Demonstrates compiler theory and dynamic code generation

### `metal.py` — Metaclass Kernel
- Pure-Python C3 linearization (Method Resolution Order)
- Aspect-Oriented Programming (AOP) via descriptor interception
- Design-by-Contract (pre/post conditions)
- Structural protocol enforcement

### `memory.py` — Raw Memory Introspection
- Uses `ctypes` to read CPython object headers (`PyObject_HEAD`, `PyVarObject`)
- Reads reference counts, type pointers, and raw memory dumps
- Detects immortal objects (Python 3.12+)
- Inspects list internal capacity and element addresses

### `ast_engine.py` — AST Transformation Engine
- Tail-Call Optimization (TCO) rewrite via AST manipulation
- Continuation-Passing Style (CPS) injection
- Memoization injection at the AST level

### `importer.py` — Encrypted Bytecode Import Hook
- Custom `sys.meta_path` hook for encrypted `.kpy` modules
- XOR stream cipher for bytecode obfuscation
- Full PEP 302/451 compliant import machinery override

## Running

```bash
python -m py_kernal
```

This executes all five demonstrations:
1. VM factorial computation with JIT trace compilation
2. Metaclass-enforced contracts and AOP logging
3. Raw memory hex-dumps of integers, floats, and lists
4. AST-level tail-call elimination
5. Encrypted module compilation and decryption

## Requirements

- CPython 3.10+ (3.12+ recommended for immortal object detection)
- 64-bit architecture (memory layout assumptions)
- **Expert-level Python knowledge** to modify or extend

## License

APACHE 2.0 — Use at your own risk. The authors are not responsible for interpreter crashes or existential dread caused by reading the source code.
