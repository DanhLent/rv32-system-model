from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
SOFTWARE_DIR = SCRIPT_DIR.parent
TEST_DIR = SOFTWARE_DIR / "tests"

if str(SOFTWARE_DIR) not in sys.path:
    sys.path.insert(0, str(SOFTWARE_DIR))

from isa import isa_def


MASK_32 = 0xFFFFFFFF


def sign_extend_12(value: int) -> int:
    """Return the signed value of a 12-bit immediate."""
    if value & 0x800:
        return value - 0x1000
    return value


def signed32(value: int) -> int:
    """Interpret a 32-bit value as signed."""
    value &= MASK_32
    return value if value < 0x80000000 else value - 0x100000000


class RegisterFile:
    """32-entry integer register file."""

    def __init__(self):
        self.registers = [0] * 32

    def read(self, addr: int) -> int:
        return self.registers[addr]

    def write(self, addr: int, data: int) -> None:
        if addr != 0:
            self.registers[addr] = data & MASK_32
        self.registers[0] = 0

    def print_regs(self, only_non_zero: bool = True) -> None:
        print("\n--- Register File ---")
        for i in range(32):
            value = self.registers[i]
            if only_non_zero and value == 0:
                continue
            print(f"x{i:02d}: 0x{value:08x}")


class Memory:
    """Instruction memory."""

    def __init__(self):
        self.mem = {}

    def load_bin(self, filepath: str | Path) -> None:
        """Load one 32-bit instruction per line."""
        path = Path(filepath)

        if not path.is_absolute():
            path = (TEST_DIR / path).resolve()

        addr = 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    if line:
                        self.mem[addr] = int(line, 2)

                    addr += 4

        except FileNotFoundError:
            print(f"Error: could not find file '{path}'")

    def read_word(self, address: int):
        """Return the instruction word at the given address."""
        return self.mem.get(address, None)


class ISS:
    """RV32I simulator for the current R-type, I-type, and U-type subset."""

    def __init__(self):
        self.pc = 0
        self.rf = RegisterFile()
        self.ram = Memory()

        self.r_opcode = int(isa_def.INSTRUCTIONS["add"]["opcode"], 2)
        self.i_opcode = int(isa_def.INSTRUCTIONS["addi"]["opcode"], 2)
        self.lui_opcode = int(isa_def.INSTRUCTIONS["lui"]["opcode"], 2)
        self.auipc_opcode = int(isa_def.INSTRUCTIONS["auipc"]["opcode"], 2)

        self.r_handlers = {
            (
                int(isa_def.INSTRUCTIONS["add"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["add"]["funct7"], 2),
            ): self.exec_add,

            (
                int(isa_def.INSTRUCTIONS["sub"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["sub"]["funct7"], 2),
            ): self.exec_sub,

            (
                int(isa_def.INSTRUCTIONS["sll"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["sll"]["funct7"], 2),
            ): self.exec_sll,

            (
                int(isa_def.INSTRUCTIONS["slt"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["slt"]["funct7"], 2),
            ): self.exec_slt,

            (
                int(isa_def.INSTRUCTIONS["sltu"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["sltu"]["funct7"], 2),
            ): self.exec_sltu,

            (
                int(isa_def.INSTRUCTIONS["xor"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["xor"]["funct7"], 2),
            ): self.exec_xor,

            (
                int(isa_def.INSTRUCTIONS["srl"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["srl"]["funct7"], 2),
            ): self.exec_srl,

            (
                int(isa_def.INSTRUCTIONS["sra"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["sra"]["funct7"], 2),
            ): self.exec_sra,

            (
                int(isa_def.INSTRUCTIONS["or"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["or"]["funct7"], 2),
            ): self.exec_or,

            (
                int(isa_def.INSTRUCTIONS["and"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["and"]["funct7"], 2),
            ): self.exec_and,
        }

        self.i_handlers = {
            int(isa_def.INSTRUCTIONS["addi"]["funct3"], 2): self.exec_addi,
            int(isa_def.INSTRUCTIONS["slti"]["funct3"], 2): self.exec_slti,
            int(isa_def.INSTRUCTIONS["sltiu"]["funct3"], 2): self.exec_sltiu,
            int(isa_def.INSTRUCTIONS["xori"]["funct3"], 2): self.exec_xori,
            int(isa_def.INSTRUCTIONS["ori"]["funct3"], 2): self.exec_ori,
            int(isa_def.INSTRUCTIONS["andi"]["funct3"], 2): self.exec_andi,
        }

        self.i_shift_handlers = {
            (
                int(isa_def.INSTRUCTIONS["slli"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["slli"]["funct7"], 2),
            ): self.exec_slli,

            (
                int(isa_def.INSTRUCTIONS["srli"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["srli"]["funct7"], 2),
            ): self.exec_srli,

            (
                int(isa_def.INSTRUCTIONS["srai"]["funct3"], 2),
                int(isa_def.INSTRUCTIONS["srai"]["funct7"], 2),
            ): self.exec_srai,
        }

    def exec_add(self, rd: int, rs1: int, rs2: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) + self.rf.read(rs2))

    def exec_sub(self, rd: int, rs1: int, rs2: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) - self.rf.read(rs2))

    def exec_sll(self, rd: int, rs1: int, rs2: int) -> None:
        shamt = self.rf.read(rs2) & 0x1F
        self.rf.write(rd, self.rf.read(rs1) << shamt)

    def exec_slt(self, rd: int, rs1: int, rs2: int) -> None:
        self.rf.write(rd, int(signed32(self.rf.read(rs1))
                      < signed32(self.rf.read(rs2))))

    def exec_sltu(self, rd: int, rs1: int, rs2: int) -> None:
        lhs = self.rf.read(rs1) & MASK_32
        rhs = self.rf.read(rs2) & MASK_32
        self.rf.write(rd, int(lhs < rhs))

    def exec_xor(self, rd: int, rs1: int, rs2: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) ^ self.rf.read(rs2))

    def exec_srl(self, rd: int, rs1: int, rs2: int) -> None:
        shamt = self.rf.read(rs2) & 0x1F
        self.rf.write(rd, (self.rf.read(rs1) & MASK_32) >> shamt)

    def exec_sra(self, rd: int, rs1: int, rs2: int) -> None:
        shamt = self.rf.read(rs2) & 0x1F
        self.rf.write(rd, signed32(self.rf.read(rs1)) >> shamt)

    def exec_or(self, rd: int, rs1: int, rs2: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) | self.rf.read(rs2))

    def exec_and(self, rd: int, rs1: int, rs2: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) & self.rf.read(rs2))

    def exec_addi(self, rd: int, rs1: int, imm: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) + imm)

    def exec_slti(self, rd: int, rs1: int, imm: int) -> None:
        self.rf.write(rd, int(signed32(self.rf.read(rs1)) < imm))

    def exec_sltiu(self, rd: int, rs1: int, imm: int) -> None:
        lhs = self.rf.read(rs1) & MASK_32
        rhs = imm & MASK_32
        self.rf.write(rd, int(lhs < rhs))

    def exec_xori(self, rd: int, rs1: int, imm: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) ^ imm)

    def exec_ori(self, rd: int, rs1: int, imm: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) | imm)

    def exec_andi(self, rd: int, rs1: int, imm: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) & imm)

    def exec_slli(self, rd: int, rs1: int, shamt: int) -> None:
        self.rf.write(rd, self.rf.read(rs1) << (shamt & 0x1F))

    def exec_srli(self, rd: int, rs1: int, shamt: int) -> None:
        self.rf.write(rd, (self.rf.read(rs1) & MASK_32) >> (shamt & 0x1F))

    def exec_srai(self, rd: int, rs1: int, shamt: int) -> None:
        self.rf.write(rd, signed32(self.rf.read(rs1)) >> (shamt & 0x1F))

    def exec_lui(self, rd: int, imm_u: int) -> None:
        self.rf.write(rd, imm_u)

    def exec_auipc(self, rd: int, imm_u: int) -> None:
        self.rf.write(rd, self.pc + imm_u)

    def run(self) -> None:
        while True:
            inst = self.ram.read_word(self.pc)

            if inst is None:
                print("\nEnd.")
                break

            opcode = inst & 0x7F
            rd = (inst >> 7) & 0x1F
            funct3 = (inst >> 12) & 0x7
            rs1 = (inst >> 15) & 0x1F
            rs2 = (inst >> 20) & 0x1F
            funct7 = (inst >> 25) & 0x7F
            imm_raw = (inst >> 20) & 0xFFF
            imm_i = sign_extend_12(imm_raw)
            imm_u = inst & 0xFFFFF000

            if opcode == self.r_opcode:
                key = (funct3, funct7)
                handler = self.r_handlers.get(key)

                if handler is None:
                    print(f"0x{self.pc:04X} | Unsupported")
                    break

                handler(rd, rs1, rs2)

            elif opcode == self.i_opcode:
                if funct3 in (0b001, 0b101):
                    key = (funct3, funct7)
                    handler = self.i_shift_handlers.get(key)

                    if handler is None:
                        print(f"0x{self.pc:04X} | Unsupported")
                        break

                    shamt = imm_raw & 0x1F
                    handler(rd, rs1, shamt)

                else:
                    handler = self.i_handlers.get(funct3)

                    if handler is None:
                        print(f"0x{self.pc:04X} | Unsupported")
                        break

                    handler(rd, rs1, imm_i)

            elif opcode == self.lui_opcode:
                self.exec_lui(rd, imm_u)

            elif opcode == self.auipc_opcode:
                self.exec_auipc(rd, imm_u)

            else:
                print(f"0x{self.pc:04X} | Unsupported")
                break

            self.pc += 4

        self.rf.print_regs()


if __name__ == "__main__":
    cpu = ISS()
    cpu.ram.load_bin(TEST_DIR / "test_iss_out.bin")
    cpu.run()
