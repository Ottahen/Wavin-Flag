
"""
py_kernal.memory
=================
Direct memory introspection of CPython objects using ctypes.
Maps PyObject_HEAD, PyVarObject, and reads interpreter internals.

WARNING: This is READ-ONLY by default. Any write can segfault the interpreter.
This is the deepest layer — touching the C structure of Python objects.
"""
from __future__ import annotations
import sys
import ctypes
from typing import Any, Dict, Optional, Tuple

# CPython object header (64-bit assumption)
class PyObject_HEAD(ctypes.Structure):
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type", ctypes.c_void_p),
    ]

class PyVarObject_HEAD(PyObject_HEAD):
    _fields_ = [
        ("ob_size", ctypes.c_ssize_t),
    ]

class PyLongObject(ctypes.Structure):
    _fields_ = [
        ("ob_base", PyVarObject_HEAD),
        ("ob_digit", ctypes.c_uint32 * 1),  # Variable length
    ]

class PyFloatObject(ctypes.Structure):
    _fields_ = [
        ("ob_base", PyObject_HEAD),
        ("ob_fval", ctypes.c_double),
    ]

class PyListObject(ctypes.Structure):
    _fields_ = [
        ("ob_base", PyVarObject_HEAD),
        ("ob_item", ctypes.POINTER(ctypes.c_void_p)),
        ("allocated", ctypes.c_ssize_t),
    ]

class MemoryKernel:
    """
    Provides a window into the C-level representation of Python objects.
    """
    def __init__(self):
        self._ptr_cache: Dict[int, Any] = {}

    def id_to_ptr(self, obj: Any) -> int:
        return id(obj)

    def refcnt(self, obj: Any) -> int:
        """Read the reference count directly from C memory."""
        ptr = self.id_to_ptr(obj)
        head = PyObject_HEAD.from_address(ptr)
        return head.ob_refcnt

    def type_addr(self, obj: Any) -> int:
        ptr = self.id_to_ptr(obj)
        head = PyObject_HEAD.from_address(ptr)
        return head.ob_type

    def float_value(self, obj: float) -> float:
        """Bypass Python float() and read the C double directly."""
        ptr = self.id_to_ptr(obj)
        fobj = PyFloatObject.from_address(ptr)
        return fobj.ob_fval

    def list_capacity(self, obj: list) -> int:
        """Read the over-allocation of a Python list."""
        ptr = self.id_to_ptr(obj)
        lobj = PyListObject.from_address(ptr)
        return lobj.allocated

    def list_items(self, obj: list) -> Tuple[int, ...]:
        """Return the raw memory addresses of list elements."""
        ptr = self.id_to_ptr(obj)
        lobj = PyListObject.from_address(ptr)
        addrs = []
        for i in range(len(obj)):
            addrs.append(lobj.ob_item[i])
        return tuple(addrs)

    def object_header(self, obj: Any) -> Dict[str, Any]:
        ptr = self.id_to_ptr(obj)
        head = PyVarObject_HEAD.from_address(ptr)
        return {
            "address": hex(ptr),
            "refcnt": head.ob_refcnt,
            "type_ptr": hex(head.ob_type),
            "size": head.ob_size,
        }

    def hex_dump(self, obj: Any, length: int = 64) -> str:
        """Raw hex dump of object memory."""
        ptr = self.id_to_ptr(obj)
        buf = (ctypes.c_ubyte * length).from_address(ptr)
        return " ".join(f"{b:02x}" for b in buf)

    def immortal_check(self, obj: Any) -> bool:
        """Detect if object is immortal (Python 3.12+ refcnt sentinel)."""
        return self.refcnt(obj) >= (1 << 30)

class ImmortalBypass:
    """
    Experimental: Demonstrates understanding of the immortal object mechanism.
    READ-ONLY. Do not attempt mutation.
    """
    def __init__(self, kernel: MemoryKernel):
        self._kernel = kernel

    def inspect(self, obj: Any) -> Dict[str, Any]:
        return {
            "object": repr(obj)[:80],
            "immortal": self._kernel.immortal_check(obj),
            "header": self._kernel.object_header(obj),
            "hex": self._kernel.hex_dump(obj, 32),
        }
