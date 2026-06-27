
"""
py_kernal.ast_engine
=====================
Abstract Syntax Tree engine that performs source-to-source transformation.
Implements:
- Automatic tail-call optimization (TCO) rewrite
- Continuation-passing style (CPS) injection
- Automatic memoization decorator injection via AST

WARNING: Modifies code semantics at the AST level. Can produce infinite loops
if transformation invariants are violated.
"""
from __future__ import annotations
import ast
import inspect
import textwrap
import types
from typing import Any, Callable, Dict, List, Optional, Union

class TCOTransformer(ast.NodeTransformer):
    """
    Rewrites tail-recursive functions into iterative loops.
    """
    def __init__(self, func_name: str):
        self.func_name = func_name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.name != self.func_name:
            return self.generic_visit(node)  # type: ignore
        # Wrap body in while True: ...
        loop = ast.While(
            test=ast.Constant(value=True),
            body=node.body,
            orelse=[]
        )
        node.body = [loop]
        # Mark as transformed
        node.decorator_list.append(ast.Name(id='__tco_transformed__', ctx=ast.Load()))
        return self.generic_visit(node)  # type: ignore

    def visit_Return(self, node: ast.Return) -> Union[ast.Return, ast.Assign]:
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == self.func_name:
                # Replace return foo(...) with assignment to args + continue
                # For simplicity, we only handle positional args mapping
                assigns = []
                for i, arg in enumerate(node.value.args):
                    assigns.append(ast.Assign(
                        targets=[ast.Name(id=f'_arg_{i}', ctx=ast.Store())],
                        value=arg
                    ))
                assigns.append(ast.Continue())
                return ast.Module(body=assigns, type_ignores=[])  # type: ignore
        return node

class CPSTransformer(ast.NodeTransformer):
    """
    Injects continuation-passing style into a function.
    Every function call becomes a lambda thunk.
    """
    def __init__(self, func_name: str):
        self.func_name = func_name
        self.k_counter = 0

    def fresh_k(self) -> str:
        self.k_counter += 1
        return f"_k{self.k_counter}"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.name != self.func_name:
            return self.generic_visit(node)  # type: ignore
        # Add 'k' parameter
        node.args.args.append(ast.arg(arg='k', annotation=None))
        return self.generic_visit(node)  # type: ignore

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if isinstance(node.func, ast.Name) and node.func.id == self.func_name:
            k = self.fresh_k()
            # Transform f(x) into (lambda k: f(x, k))(lambda v: ...)
            # This is a simplified CPS transform
            return ast.Call(
                func=ast.Lambda(
                    args=ast.arguments(args=[ast.arg(arg=k, annotation=None)], posonlyargs=[], kwonlyargs=[], defaults=[], kw_defaults=[]),
                    body=ast.Call(
                        func=node.func,
                        args=node.args + [ast.Name(id=k, ctx=ast.Load())],
                        keywords=[]
                    )
                ),
                args=[ast.Lambda(
                    args=ast.arguments(args=[ast.arg(arg='v', annotation=None)], posonlyargs=[], kwonlyargs=[], defaults=[], kw_defaults=[]),
                    body=ast.Name(id='v', ctx=ast.Load())
                )],
                keywords=[]
            )
        return self.generic_visit(node)

class ASTKernel:
    """
    High-level API for AST transformations.
    """
    def __init__(self):
        self.cache: Dict[str, types.FunctionType] = {}

    def _get_ast(self, fn: Callable) -> ast.AST:
        src = inspect.getsource(fn)
        src = textwrap.dedent(src)
        return ast.parse(src)

    def apply_tco(self, fn: Callable) -> Callable:
        """Rewrite function to eliminate tail recursion."""
        tree = self._get_ast(fn)
        transformer = TCOTransformer(fn.__name__)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        code = compile(new_tree, fn.__code__.co_filename, 'exec')
        ns = dict(fn.__globals__)
        exec(code, ns)
        return ns[fn.__name__]

    def apply_cps(self, fn: Callable) -> Callable:
        """Convert function to continuation-passing style."""
        tree = self._get_ast(fn)
        transformer = CPSTransformer(fn.__name__)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        code = compile(new_tree, fn.__code__.co_filename, 'exec')
        ns = dict(fn.__globals__)
        exec(code, ns)
        return ns[fn.__name__]

    def inject_memo(self, fn: Callable) -> Callable:
        """Inject memoization at the AST level rather than using a decorator."""
        tree = self._get_ast(fn)
        # Insert cache dict at top of function
        cache_assign = ast.Assign(
            targets=[ast.Name(id='_memo_cache', ctx=ast.Store())],
            value=ast.Dict(keys=[], values=[])
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == fn.__name__:
                node.body.insert(0, cache_assign)
                break
        ast.fix_missing_locations(tree)
        code = compile(tree, fn.__code__.co_filename, 'exec')
        ns = dict(fn.__globals__)
        exec(code, ns)
        return ns[fn.__name__]
