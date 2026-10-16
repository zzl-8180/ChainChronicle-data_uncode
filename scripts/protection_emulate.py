"""Bounded CPU emulation of this build's protection code; no host syscall bridge.

Imported functions have explicit controlled models. Unmodeled imports/syscalls and
unmapped accesses stop the experiment. This is not an Android environment.
"""
import argparse
import hashlib
import io
import json
import struct
from collections import deque
from collections import Counter
from pathlib import Path

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UcError, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_INTR, UC_HOOK_MEM_WRITE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X30, UC_ARM64_REG_SP, UC_ARM64_REG_PC, UC_ARM64_REG_TPIDR_EL0

SOURCE = Path("work/apk/lib/arm64-v8a/libcompatible.so")
BASE, HEAP, STACK, TLS, IMPORTS, STOP = 0x10000000, 0x20000000, 0x70000000, 0x71000000, 0x30000000, 0x40000000


class Experiment:
    def __init__(self, raw, seed, context_result=None, omit_constructors=False, heap_size=0x1000000):
        self.uc = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        if not 0x1000000 <= heap_size <= 0x8000000 or heap_size % 4096:
            raise ValueError("Guest heap size must be page aligned, 16..128 MiB")
        self.heap_limit = HEAP+heap_size
        self.raw, self.heap, self.seed = raw, HEAP, seed
        self.context_result = context_result
        self.omit_constructors = omit_constructors
        self.virtual_fds = set()
        self.virtual_mutexes = set()
        self.guest_files, self.guest_open_files = {}, {}
        self.external, self.calls, self.failure = {}, [], None
        self.recent = deque(maxlen=12)
        self.tracked_writes = []
        self.syscalls = []
        elf = ELFFile(io.BytesIO(raw))
        self.uc.mem_map(BASE, 0x200000)
        for segment in elf.iter_segments():
            if segment["p_type"] == "PT_LOAD":
                self.uc.mem_write(BASE+segment["p_vaddr"], raw[segment["p_offset"]:segment["p_offset"]+segment["p_filesz"]])
        self.uc.mem_map(HEAP, heap_size)
        self.uc.mem_map(STACK, 0x100000)
        self.uc.mem_map(TLS, 0x1000)
        self.uc.mem_map(IMPORTS, 0x10000)
        self.uc.mem_map(STOP, 0x1000)
        self.uc.reg_write(UC_ARM64_REG_TPIDR_EL0, TLS)
        self.uc.reg_write(UC_ARM64_REG_SP, STACK+0xf0000)
        symbols = next(s for s in elf.iter_sections() if s["sh_type"] == "SHT_DYNSYM")
        defined = {s.name: s["st_value"] for s in symbols.iter_symbols() if s["st_shndx"] != "SHN_UNDEF"}
        relocations = json.loads(Path("output/protection/relocations.json").read_text())["all_relocations"]
        imported = {}
        for row in relocations:
            if row["type"] == 1027:
                value = BASE + row["addend"]
            elif row["type"] in (257, 1025, 1026):  # ABS64, GLOB_DAT, JUMP_SLOT: S+A
                name = row["symbol"]
                if name in defined:
                    value = BASE + defined[name] + row["addend"]
                else:
                    if name not in imported:
                        imported[name] = IMPORTS + len(imported)*16
                    value = imported[name] + row["addend"]
                    self.external[value] = name
            else:
                raise ValueError(f"Unsupported relocation {row['type']}")
            self.uc.mem_write(BASE+row["slot"], struct.pack("<Q", value))
        if "environ" in imported:
            self.uc.mem_write(imported["environ"], struct.pack("<Q", self.allocate(8)))
        self.uc.hook_add(UC_HOOK_CODE, self.hook, begin=IMPORTS, end=IMPORTS+0xffff)
        self.uc.hook_add(UC_HOOK_CODE, self.hook, begin=STOP, end=STOP)
        self.uc.hook_add(UC_HOOK_CODE, self.hook, begin=BASE+0xe6094, end=BASE+0xe6094)
        if context_result is not None:
            self.uc.hook_add(UC_HOOK_CODE, self.hook, begin=BASE+0x14adc8, end=BASE+0x14adc8)
        if omit_constructors:
            self.uc.hook_add(UC_HOOK_CODE, self.hook, begin=BASE+0x148780, end=BASE+0x148780)
        self.uc.hook_add(UC_HOOK_INTR, self.interrupt)
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self.memory_write, begin=BASE+0x1a46a0, end=BASE+0x1a61e8)

    def memory_write(self, uc, access, address, size, value, _):
        for cell in (0x1a46a0, 0x1a61e0):
            if address <= BASE+cell < address+size:
                self.tracked_writes.append({"pc_rva": hex(uc.reg_read(UC_ARM64_REG_PC)-BASE),
                                            "address_rva": hex(address-BASE), "size": size, "value": hex(value)})

    def allocate(self, size, data=None):
        address = self.heap
        if size < 0 or self.heap+size >= self.heap_limit:
            raise ValueError("Controlled heap exceeded")
        self.heap += (max(size, 16)+15) & ~15
        if data:
            self.uc.mem_write(address, data)
        return address

    def string(self, address):
        result = bytearray()
        for i in range(4096):
            byte = self.uc.mem_read(address+i, 1)[0]
            if not byte:
                return bytes(result)
            result.append(byte)
        raise ValueError("Unterminated string")

    def interrupt(self, uc, number, _):
        syscall = uc.reg_read(UC_ARM64_REG_X0+8)
        args = [uc.reg_read(UC_ARM64_REG_X0+i) for i in range(6)]
        self.syscalls.append({"number": syscall, "pc_rva": hex(uc.reg_read(UC_ARM64_REG_PC)-BASE),
                              "caller_lr_rva": hex(uc.reg_read(UC_ARM64_REG_X30)-BASE),
                              "args": [hex(a) for a in args]})
        if number == 2 and syscall == 56:
            path = self.string(args[1])
            self.syscalls[-1]["path"] = path.decode("utf-8", "replace")
            if args[0] == 0xffffffffffffff9c and args[2] == 0 and path in self.guest_files:
                fd = 200 + len(self.guest_open_files)
                self.guest_open_files[fd] = [self.guest_files[path], 0]
                uc.reg_write(UC_ARM64_REG_X0, fd)
                return
        if number == 2 and syscall == 63 and args[0] in self.guest_open_files:
            data, offset = self.guest_open_files[args[0]]
            chunk = data[offset:offset+args[2]]
            uc.mem_write(args[1], chunk)
            self.guest_open_files[args[0]][1] += len(chunk)
            uc.reg_write(UC_ARM64_REG_X0, len(chunk))
            return
        if number == 2 and syscall == 62 and args[0] in self.guest_open_files and args[2] in (0,1,2):
            data, offset = self.guest_open_files[args[0]]
            signed_offset = args[1] if args[1] < 1<<63 else args[1]-(1<<64)
            position = (0, offset, len(data))[args[2]] + signed_offset
            if not 0 <= position <= len(data):
                self.failure = "Guest seek outside controlled file"
                uc.emu_stop()
                return
            self.guest_open_files[args[0]][1] = position
            uc.reg_write(UC_ARM64_REG_X0, position)
            return
        if number == 2 and syscall == 57 and args[0] in self.guest_open_files:
            del self.guest_open_files[args[0]]
            uc.reg_write(UC_ARM64_REG_X0, 0)
            return
        if number == 2 and syscall == 172:
            uc.reg_write(UC_ARM64_REG_X0, 1234)  # controlled guest getpid
            return
        if number == 2 and syscall == 222 and args[0] == 0 and args[3] == 0x22 and args[4] == 0xffffffffffffffff:
            self.heap = (self.heap+4095) & ~4095
            uc.reg_write(UC_ARM64_REG_X0, self.allocate((args[1]+4095) & ~4095))
            return
        if number == 2 and syscall == 226:
            # Guest module/heap are mapped writable; no host protection change.
            uc.reg_write(UC_ARM64_REG_X0, 0)
            return
        if number == 2 and syscall == 215 and HEAP <= args[0] < self.heap_limit and 0 < args[1] <= self.heap_limit-args[0]:
            # Retain guest allocation like the free model; no host unmapping.
            uc.reg_write(UC_ARM64_REG_X0, 0)
            return
        self.failure = (f"CPU interrupt {number}; syscall={uc.reg_read(UC_ARM64_REG_X0+8)}; "
                        f"args={[hex(uc.reg_read(UC_ARM64_REG_X0+i)) for i in range(6)]}; no host syscall execution")
        uc.emu_stop()

    def hook(self, uc, address, size, _):
        self.recent.append(hex(address-BASE))
        if address == STOP:
            uc.emu_stop()
            return
        if address == BASE+0x14adc8 and self.context_result is not None:
            self.calls.append({"name": "CONTROLLED_CONTEXT_RESULT", "result": self.context_result,
                               "caller_lr": hex(uc.reg_read(UC_ARM64_REG_X30)-BASE)})
            uc.reg_write(UC_ARM64_REG_X0, self.context_result)
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            return
        if address == BASE+0x148780 and self.omit_constructors:
            self.calls.append({"name": "CONTROLLED_OMIT_CONSTRUCTORS", "from_rva": "0x148780", "to_rva": "0x148894"})
            uc.reg_write(UC_ARM64_REG_PC, BASE+0x148894)
            return
        # Instruction cache maintenance is unnecessary for this CPU model.
        if address == BASE+0xe6094:
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
            return
        if address not in self.external:
            return
        name = self.external[address]
        args = [uc.reg_read(UC_ARM64_REG_X0+i) for i in range(4)]
        self.calls.append({"name": name, "caller_lr": hex(uc.reg_read(UC_ARM64_REG_X30)-BASE)})
        try:
            if name in ("malloc", "calloc"):
                value = self.allocate(args[0] if name == "malloc" else args[0]*args[1])
            elif name in ("free", "srand", "__cxa_atexit", "__cxa_finalize", "madvise", "mprotect", "unsetenv"):
                value = 0
            elif name in ("pthread_mutex_lock", "pthread_mutex_unlock"):
                # Single-thread guest-only lock ownership; never touch host locks.
                uc.mem_read(args[0], 40)
                if name == "pthread_mutex_lock":
                    if args[0] in self.virtual_mutexes:
                        raise ValueError("Recursive guest mutex lock is not modeled")
                    self.virtual_mutexes.add(args[0])
                else:
                    if args[0] not in self.virtual_mutexes:
                        raise ValueError("Guest mutex unlock without ownership")
                    self.virtual_mutexes.remove(args[0])
                value = 0
            elif name == "time":
                value = 1700000000
                if args[0]:
                    uc.mem_write(args[0], struct.pack("<Q", value))
            elif name == "getpid":
                value = 1234
            elif name == "getuid":
                value = 10000
            elif name == "clock":
                value = 100
            elif name == "pthread_self":
                value = TLS
            elif name == "getauxval" and args[0] in (6, 16, 26):
                value = 4096 if args[0] == 6 else 0  # controlled pagesize / no optional CPU features
            elif name == "__open_2" and self.string(args[0]) == b"/dev/urandom":
                value = 100 + len(self.virtual_fds)
                self.virtual_fds.add(value)
            elif name in ("read", "__read_chk") and args[0] in self.virtual_fds and args[2] <= 4096:
                if name == "__read_chk" and args[3] < args[2]:
                    raise ValueError("Guest checked-read buffer too short")
                data = bytearray()
                for _ in range(args[2]):
                    self.seed = (1103515245*self.seed+12345) & 0x7fffffff
                    data.append((self.seed >> 16) & 255)
                uc.mem_write(args[1], bytes(data))
                value = len(data)
            elif name == "close" and args[0] in self.virtual_fds:
                self.virtual_fds.remove(args[0])
                value = 0
            elif name == "rand":
                self.seed = (1103515245*self.seed+12345) & 0x7fffffff
                value = self.seed
            elif name == "strlen":
                value = len(self.string(args[0]))
            elif name == "printf" and self.string(args[0]) == b"nOutSize = %d":
                signed = args[1] & 0xffffffff
                signed = signed if signed < 1<<31 else signed-(1<<32)
                rendered = f"nOutSize = {signed}"
                self.calls[-1]["guest_diagnostic"] = rendered
                value = len(rendered)
            elif name == "dlsym" and args[0] == 0 and self.string(args[1]) == b"mprotect":
                value = next(address for address, symbol in self.external.items() if symbol == "mprotect")
            elif name in ("memcpy", "memmove"):
                uc.mem_write(args[0], bytes(uc.mem_read(args[1], args[2])))
                value = args[0]
            elif name == "memset":
                uc.mem_write(args[0], bytes([args[1]&255])*args[2])
                value = args[0]
            elif name == "__errno":
                value = TLS+0x100
            else:
                if name in ("__open_2", "open", "fopen"):
                    raise ValueError(f"Unmodeled file access: {name} {self.string(args[0])!r}")
                if name == "vsnprintf":
                    raise ValueError(f"Unmodeled formatting: {self.string(args[2])!r}; caller={hex(uc.reg_read(UC_ARM64_REG_X30)-BASE)}")
                if name == "dlsym":
                    raise ValueError(f"Unmodeled dlsym: {self.string(args[1])!r}; handle={hex(args[0])}; caller={hex(uc.reg_read(UC_ARM64_REG_X30)-BASE)}")
                if name == "printf":
                    raise ValueError(f"Unmodeled printf: {self.string(args[0])!r}; args={[hex(a) for a in args[1:]]}; caller={hex(uc.reg_read(UC_ARM64_REG_X30)-BASE)}")
                raise ValueError(f"Unmodeled import: {name}")
            uc.reg_write(UC_ARM64_REG_X0, value)
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
        except Exception as error:
            self.failure = str(error)
            uc.emu_stop()

    def call(self, rva, *args, instruction_limit=30000000):
        for i, value in enumerate(args):
            self.uc.reg_write(UC_ARM64_REG_X0+i, value)
        self.uc.reg_write(UC_ARM64_REG_X30, STOP)
        return self.run_from(BASE+rva, instruction_limit)

    def resume(self, instruction_limit=100000000):
        """Continue an execution-limit stop without changing its live registers."""
        return self.run_from(self.uc.reg_read(UC_ARM64_REG_PC), instruction_limit)

    def run_from(self, address, instruction_limit):
        self.failure = None
        try:
            self.uc.emu_start(address, STOP+4, timeout=15000000, count=instruction_limit)
        except UcError as error:
            self.failure = str(error)
        if self.failure or self.uc.reg_read(UC_ARM64_REG_PC) != STOP:
            raise ValueError(f"{self.failure or 'Execution limit'} at {hex(self.uc.reg_read(UC_ARM64_REG_PC)-BASE)}; recent={list(self.recent)}")
        return self.uc.reg_read(UC_ARM64_REG_X0)

    def decrypt(self, key, data):
        ctx = self.allocate(0x430)
        kp, dp = self.allocate(len(key), key), self.allocate(len(data), data)
        self.call(0x12b488, ctx)
        assert self.call(0x12b49c, ctx, kp, kp, len(key), 16) == 1
        size = len(data) & ~15
        assert self.call(0x12c7d4, ctx, dp, dp, size, 0) == size
        return bytes(self.uc.mem_read(dp, len(data)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--context-result", type=int, choices=(0, 1),
                        help="explicit counterfactual return at environment-dependent 0x14adc8; NOT observed game state")
    parser.add_argument("--omit-constructors", action="store_true", help="explicitly omit unrelated constructor tables; resulting state is counterfactual")
    args = parser.parse_args()
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "79b6ae193625494b5facbc1c7eafa5bb16c4252dd9050fe10caee2393aa8767c", "Pinned build only"
    experiment = Experiment(raw, args.seed, args.context_result, args.omit_constructors)
    label = f"seed{args.seed}" + (f"_context{args.context_result}" if args.context_result is not None else "")
    label += "_omitctors" if args.omit_constructors else ""
    # FIPS-197 AES-128 known answer, before using real file inputs.
    plain = experiment.decrypt(bytes.fromhex("000102030405060708090a0b0c0d0e0f"), bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a"))
    assert plain.hex() == "00112233445566778899aabbccddeeff"
    restored = experiment.decrypt(raw[0x1458cc:0x1458dc], raw[0x14007c:0x14007c+612])
    experiment.uc.mem_write(BASE+0x1458cc, restored)
    header = experiment.allocate(0x1070, raw[0x1407a8:0x1407a8+0x70])
    experiment.uc.mem_write(BASE+0x1a6948, struct.pack("<QQ", header, BASE))
    output = Path("output/protection/emulation")
    output.mkdir(parents=True, exist_ok=True)
    Path("work/protection").mkdir(parents=True, exist_ok=True)
    stages = []
    for index, rva in enumerate((0x1458cc, 0x146820, 0x1471b4), 1):
        status, returned, failure = "STOPPED", None, None
        try:
            returned = experiment.call(rva)
            status = "RETURNED"
        except ValueError as error:
            failure = str(error)
        snapshot = bytes(experiment.uc.mem_read(BASE, 0x200000))
        Path(f"work/protection/compatible_stage{index}_{label}.bin").write_bytes(snapshot)
        stages.append({"stage": index, "rva": hex(rva), "status": status,
                       "returned": hex(returned-BASE) if returned and BASE <= returned < BASE+0x200000 else hex(returned) if returned else None,
                       "failure": failure})
        if failure:
            break
    result = {"status": status, "source_sha256": hashlib.sha256(raw).hexdigest(), "seed": args.seed,
              "controlled_context_result": args.context_result,
              "controlled_omit_constructors": args.omit_constructors,
              "native_AES_FIPS197": "PASS", "stages": stages,
              "failure": failure, "modeled_imports": experiment.calls, "tracked_writes": experiment.tracked_writes,
              "modeled_syscalls": experiment.syscalls,
              "limits": ["Controlled time/pid/uid/seed, zero BSS and modeled imports are not game runtime state",
                         "Guest environment is empty; virtual urandom is deterministic when used",
                         "No guest syscall forwarded to host; only explicit guest-memory operations modeled"]}
    (output / f"stages_{label}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "modeled_imports"} |
                     {"import_counts": dict(Counter(r["name"] for r in experiment.calls))}, indent=2))


if __name__ == "__main__":
    main()
