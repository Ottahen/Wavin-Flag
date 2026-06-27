
"""
py_kernal.vm
==============
A register-based virtual machine with a tracing JIT compiler, written in pure Python.
Implements a custom bytecode format, SSA-like register allocation, and hot-path tracing.

WARNING: This manipulates execution frames and can destabilize the interpreter.
"""
from __future__ import annotations
import sys
import types
import dis
import opcode
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Callable, Optional
from enum import IntEnum, auto

class OpCode(IntEnum):
    NOP = 0; LOAD_CONST = auto(); LOAD_REG = auto(); STORE_REG = auto()
    ADD = auto(); SUB = auto(); MUL = auto(); DIV = auto(); MOD = auto()
    EQ = auto(); LT = auto(); GT = auto(); JMP = auto(); JZ = auto()
    CALL = auto(); RET = auto(); PUSH = auto(); POP = auto(); HALT = auto()
    GET_ATTR = auto(); SET_ATTR = auto(); BUILD_LIST = auto(); INDEX = auto()
    PRINT = auto(); TRACE = auto()  # TRACE triggers JIT recording

@dataclass
class Instruction:
    op: OpCode
    args: Tuple[Any, ...] = ()

@dataclass
class Trace:
    """Recorded hot-path for JIT compilation."""
    instructions: List[Instruction] = field(default_factory=list)
    start_pc: int = 0
    loop_header: int = 0

class JITCompiler:
    """
    Tracing JIT: records bytecode sequences and emits native-like Python
    function objects using code objects and closures.
    """
    def __init__(self):
        self.hot_counters: Dict[int, int] = {}
        self.traces: Dict[int, types.FunctionType] = {}
        self.threshold = 10

    def record(self, pc: int, vm: 'VirtualMachine') -> Optional[Trace]:
        if pc in self.traces:
            return None  # Already compiled
        self.hot_counters[pc] = self.hot_counters.get(pc, 0) + 1
        if self.hot_counters[pc] < self.threshold:
            return None
        trace = Trace(start_pc=pc, loop_header=pc)
        # Record until loop back-edge or max length
        seen = set()
        cur = pc
        while cur < len(vm.code) and cur not in seen:
            seen.add(cur)
            instr = vm.code[cur]
            trace.instructions.append(instr)
            if instr.op == OpCode.JMP and instr.args[0] <= cur:
                break  # Back-edge
            if instr.op in (OpCode.JZ, OpCode.JMP):
                cur = instr.args[0]
            else:
                cur += 1
        return trace

    def compile_trace(self, trace: Trace) -> types.FunctionType:
        """
        Compile a trace into a Python function by generating a new code object
        that operates on the VM register file directly.
        """
        # Build a lambda that replays the trace using the VM's register dict
        reg = "_reg"
        const = "_const"
        lines: List[str] = []
        for instr in trace.instructions:
            if instr.op == OpCode.LOAD_CONST:
                lines.append(f"{reg}[{instr.args[1]}] = {const}[{instr.args[0]}]")
            elif instr.op == OpCode.ADD:
                lines.append(f"{reg}[{instr.args[2]}] = {reg}[{instr.args[0]}] + {reg}[{instr.args[1]}]")
            elif instr.op == OpCode.SUB:
                lines.append(f"{reg}[{instr.args[2]}] = {reg}[{instr.args[0]}] - {reg}[{instr.args[1]}]")
            elif instr.op == OpCode.MUL:
                lines.append(f"{reg}[{instr.args[2]}] = {reg}[{instr.args[0]}] * {reg}[{instr.args[1]}]")
            elif instr.op == OpCode.DIV:
                lines.append(f"{reg}[{instr.args[2]}] = {reg}[{instr.args[0]}] / {reg}[{instr.args[1]}]")
            elif instr.op == OpCode.LT:
                lines.append(f"{reg}[{instr.args[2]}] = {reg}[{instr.args[0]}] < {reg}[{instr.args[1]}]")
            elif instr.op == OpCode.EQ:
                lines.append(f"{reg}[{instr.args[2]}] = {reg}[{instr.args[0]}] == {reg}[{instr.args[1]}]")
            elif instr.op == OpCode.JZ:
                lines.append(f"if not {reg}[{instr.args[0]}]: return {instr.args[1]}")
            elif instr.op == OpCode.STORE_REG:
                lines.append(f"{reg}[{instr.args[1]}] = {reg}[{instr.args[0]}]")
            elif instr.op == OpCode.RET:
                lines.append(f"return {reg}[{instr.args[0]}]")
        src = "\n".join(["def _jit_trace(_reg, _const):"] + ["    " + l for l in lines])
        ns: Dict[str, Any] = {}
        exec(compile(src, "<jit>", "exec"), ns)
        return ns["_jit_trace"]  # type: ignore

class VirtualMachine:
    """
    Register-based VM with 256 general-purpose registers and a separate constant pool.
    """
    def __init__(self, code: List[Instruction], constants: List[Any]):
        self.code = code
        self.constants = constants
        self.registers: Dict[int, Any] = {i: None for i in range(256)}
        self.stack: List[Any] = []
        self.pc = 0
        self.jit = JITCompiler()
        self.running = True
        self.trace_cache: Dict[int, Any] = {}

    def run(self) -> Any:
        while self.running and self.pc < len(self.code):
            # JIT hot-path check
            if self.pc in self.trace_cache:
                self.pc = self.trace_cache[self.pc](self.registers, self.constants)
                continue
            trace = self.jit.record(self.pc, self)
            if trace:
                fn = self.jit.compile_trace(trace)
                self.trace_cache[trace.start_pc] = fn
                self.pc = fn(self.registers, self.constants)
                continue

            instr = self.code[self.pc]
            op = instr.op
            args = instr.args

            if op == OpCode.NOP:
                pass
            elif op == OpCode.LOAD_CONST:
                self.registers[args[1]] = self.constants[args[0]]
            elif op == OpCode.LOAD_REG:
                self.registers[args[1]] = self.registers[args[0]]
            elif op == OpCode.STORE_REG:
                self.registers[args[1]] = self.registers[args[0]]
            elif op == OpCode.ADD:
                self.registers[args[2]] = self.registers[args[0]] + self.registers[args[1]]
            elif op == OpCode.SUB:
                self.registers[args[2]] = self.registers[args[0]] - self.registers[args[1]]
            elif op == OpCode.MUL:
                self.registers[args[2]] = self.registers[args[0]] * self.registers[args[1]]
            elif op == OpCode.DIV:
                self.registers[args[2]] = self.registers[args[0]] / self.registers[args[1]]
            elif op == OpCode.MOD:
                self.registers[args[2]] = self.registers[args[0]] % self.registers[args[1]]
            elif op == OpCode.EQ:
                self.registers[args[2]] = self.registers[args[0]] == self.registers[args[1]]
            elif op == OpCode.LT:
                self.registers[args[2]] = self.registers[args[0]] < self.registers[args[1]]
            elif op == OpCode.GT:
                self.registers[args[2]] = self.registers[args[0]] > self.registers[args[1]]
            elif op == OpCode.JMP:
                self.pc = args[0]
                continue
            elif op == OpCode.JZ:
                if not self.registers[args[0]]:
                    self.pc = args[1]
                    continue
            elif op == OpCode.CALL:
                fn = self.registers[args[0]]
                nargs = args[1]
                call_args = [self.registers[self.pc + 1 + i] for i in range(nargs)]
                self.registers[args[2]] = fn(*call_args)
            elif op == OpCode.RET:
                return self.registers[args[0]]
            elif op == OpCode.PUSH:
                self.stack.append(self.registers[args[0]])
            elif op == OpCode.POP:
                self.registers[args[0]] = self.stack.pop()
            elif op == OpCode.GET_ATTR:
                self.registers[args[2]] = getattr(self.registers[args[0]], self.registers[args[1]])
            elif op == OpCode.SET_ATTR:
                setattr(self.registers[args[0]], self.registers[args[1]], self.registers[args[2]])
            elif op == OpCode.BUILD_LIST:
                self.registers[args[0]] = [self.registers[i] for i in range(args[1], args[2])]
            elif op == OpCode.INDEX:
                self.registers[args[2]] = self.registers[args[0]][self.registers[args[1]]]
            elif op == OpCode.PRINT:
                print(self.registers[args[0]])
            elif op == OpCode.HALT:
                self.running = False
            self.pc += 1
        return self.registers[0]
