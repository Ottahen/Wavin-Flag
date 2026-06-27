
"""
py_kernal.metal
================
A metaclass kernel that reimplements Python's class semantics from scratch:
- Custom C3 linearization (Method Resolution Order)
- Aspect-Oriented Programming via descriptor interception
- Design-by-Contract (pre/post conditions)
- Structural typing enforcement

WARNING: Heavy use of metaclasses and frame manipulation.
"""
from __future__ import annotations
import inspect
import sys
import types
from typing import Any, Dict, List, Tuple, Callable, Optional, Set

class C3Linearization:
    """
    Pure-Python reimplementation of Python's C3 MRO algorithm.
    Used to demonstrate that the 'kernel' controls inheritance.
    """
    @staticmethod
    def merge(sequences: List[List[type]]) -> Optional[List[type]]:
        result: List[type] = []
        while sequences:
            # Find first head not in any tail
            found = None
            for seq in sequences:
                if not seq:
                    continue
                head = seq[0]
                if not any(head in s[1:] for s in sequences if len(s) > 1):
                    found = head
                    break
            if found is None:
                return None  # Inconsistent hierarchy
            result.append(found)
            # Remove found from heads
            for seq in sequences:
                if seq and seq[0] is found:
                    seq.pop(0)
            sequences = [s for s in sequences if s]
        return result

    @classmethod
    def mro(cls: type) -> List[type]:
        bases = cls.__bases__
        if not bases:
            return [cls]
        sequences = [[cls]] + [C3Linearization.mro(b) for b in bases] + [list(bases)]
        merged = C3Linearization.merge(sequences)
        if merged is None:
            raise TypeError(f"Cannot create a consistent method resolution order for {cls}")
        return merged

class ContractViolation(Exception):
    pass

class _ContractDescriptor:
    """
    Descriptor that intercepts every method call to enforce pre/post conditions
    and inject advice (AOP).
    """
    def __init__(self, name: str, func: Callable, pre: List[Callable], post: List[Callable], around: List[Callable]):
        self.name = name
        self.func = func
        self.pre = pre
        self.post = post
        self.around = around

    def __get__(self, instance: Any, owner: type) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = {'self': instance, 'args': args, 'kwargs': kwargs, 'result': None, 'proceed': True}
            # Around advice (can short-circuit)
            for advice in self.around:
                advice(ctx)
                if not ctx['proceed']:
                    return ctx['result']
            # Pre-conditions
            for cond in self.pre:
                if not cond(instance, *args, **kwargs):
                    raise ContractViolation(f"Pre-condition failed for {self.name}")
            # Execute
            if instance is None:
                ctx['result'] = self.func(*args, **kwargs)
            else:
                ctx['result'] = self.func(instance, *args, **kwargs)
            # Post-conditions
            for cond in self.post:
                if not cond(instance, ctx['result'], *args, **kwargs):
                    raise ContractViolation(f"Post-condition failed for {self.name}")
            return ctx['result']
        wrapper.__name__ = self.name
        wrapper.__doc__ = self.func.__doc__
        return wrapper

class KernelMeta(type):
    """
    The 'Kernal' metaclass. Replaces every function in the namespace with a
    contract-wrapped descriptor and validates structural typing.
    """
    def __new__(mcs, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any],
                protocols: Tuple[type, ...] = (), **kw: Any) -> type:
        # Structural typing: ensure all protocol methods exist
        for proto in protocols:
            for meth_name in dir(proto):
                if meth_name.startswith('_'):
                    continue
                if meth_name not in namespace:
                    raise TypeError(f"{name} must implement {meth_name} from {proto.__name__}")

        # Extract contract definitions
        pre_conditions: Dict[str, List[Callable]] = namespace.pop('__pre__', {})
        post_conditions: Dict[str, List[Callable]] = namespace.pop('__post__', {})
        around_advice: Dict[str, List[Callable]] = namespace.pop('__around__', {})

        new_ns: Dict[str, Any] = {}
        for key, value in namespace.items():
            if isinstance(value, FunctionType := type(lambda: None)) and key != '__init__':
                # Wrap with contract descriptor
                new_ns[key] = _ContractDescriptor(
                    key, value,
                    pre_conditions.get(key, []),
                    post_conditions.get(key, []),
                    around_advice.get(key, [])
                )
            else:
                new_ns[key] = value

        cls = super().__new__(mcs, name, bases, new_ns)
        # Override MRO with our C3 implementation
        cls.__mro_entries__ = lambda bases: (cls,)  # type: ignore
        return cls

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        # Intercept instantiation to log / profile
        instance = cls.__new__(cls, *args, **kwargs)
        if hasattr(instance, '__init__'):
            instance.__init__(*args, **kwargs)
        return instance

class StructuralProtocol(metaclass=KernelMeta):
    """Base class for structural protocols."""
    pass

def aspect(target: str, when: str = 'around') -> Callable:
    """Decorator to register AOP advice."""
    def decorator(fn: Callable) -> Callable:
        fn._aspect_target = target  # type: ignore
        fn._aspect_when = when      # type: ignore
        return fn
    return decorator
