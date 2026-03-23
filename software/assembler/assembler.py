"""
RISC-V RV32I Assembler
Supports the 6 basic instruction formats:
R, I, S, B, U, J
"""

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
SOFTWARE_DIR = SCRIPT_DIR.parent
TEST_DIR = SOFTWARE_DIR / "tests"

if str(SOFTWARE_DIR) not in sys.path:
    sys.path.insert(0, str(SOFTWARE_DIR))

from isa import isa_def

LOAD_INSTRUCTIONS = {"lb", "lh", "lw", "lbu", "lhu"}
SHIFT_IMM_INSTRUCTIONS = {"slli", "srli", "srai"}
BLANK_MC = " " * 32

SUPPORTED_INSTRUCTIONS = set(isa_def.INSTRUCTIONS) - {"ecall", "ebreak"}


def int_to_bin(value: int, bits: int) -> str:
    """Convert an integer to a zero-padded two's complement binary string."""
    mask = (1 << bits) - 1
    return format(value & mask, f"0{bits}b")


def parse_mem_operand(operand: str) -> tuple[str, str]:
    """Parse a memory operand of the form imm(rs1)."""
    operand = operand.strip()

    if "(" not in operand or not operand.endswith(")"):
        raise ValueError(f"Invalid memory operand: {operand}")

    imm_str, rs1_name = operand[:-1].split("(", 1)
    imm_str = imm_str.strip() or "0"
    rs1_name = rs1_name.strip()

    return imm_str, rs1_name


def clean_code(filepath: str | Path) -> list[str]:
    """Read the assembly file, remove comments, and skip empty lines."""
    clean_lines = []
    path = Path(filepath)

    if not path.is_absolute():
        path = (SCRIPT_DIR / path).resolve()

    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                instruction = line.split("#", 1)[0].strip()
                if instruction:
                    clean_lines.append(instruction)
    except FileNotFoundError:
        print(f"Error: Could not find source file '{path}'")

    return clean_lines


def collect_labels_and_instructions(clean_lines: list[str]) -> tuple[dict[str, int], list[str]]:
    """
    Collect labels and build the final instruction list.

    Labels may appear on their own line:
        loop:

    or inline with an instruction:
        loop: addi x1, x1, -1
    """
    label_table = {}
    instructions_only = []
    pc_address = 0

    for line in clean_lines:
        remaining = line

        while ":" in remaining:
            label_name, tail = remaining.split(":", 1)
            label_name = label_name.strip()

            if not label_name:
                raise ValueError(f"Invalid label syntax: {line}")

            if any(ch.isspace() for ch in label_name):
                break

            if label_name in label_table:
                raise ValueError(f"Duplicate label: {label_name}")

            label_table[label_name] = pc_address
            remaining = tail.strip()

            if not remaining:
                break

        if remaining:
            instructions_only.append(remaining)
            pc_address += 4

    return label_table, instructions_only


def get_register_bin(register_name: str) -> str:
    """Return the 5-bit encoding of a register name."""
    try:
        return isa_def.REGISTERS[register_name]
    except KeyError as exc:
        raise ValueError(f"Unknown register: {register_name}") from exc


def get_instruction_meta(inst_name: str) -> dict:
    """Return instruction metadata from isa_def."""
    try:
        return isa_def.INSTRUCTIONS[inst_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported instruction: {inst_name}") from exc


def parse_signed_immediate(token: str, bits: int, field_name: str, align: int = 1) -> int:
    """Parse and validate a signed immediate."""
    value = int(token, 0)

    if value % align != 0:
        raise ValueError(f"{field_name} must be a multiple of {align}: {value}")

    min_value = -(1 << (bits - 1))
    max_value = (1 << (bits - 1)) - 1

    if not (min_value <= value <= max_value):
        raise ValueError(f"{field_name} out of range for {bits} bits: {value}")

    return value


def parse_unsigned_immediate(token: str, bits: int, field_name: str) -> int:
    """Parse and validate an unsigned immediate."""
    value = int(token, 0)
    max_value = (1 << bits) - 1

    if not (0 <= value <= max_value):
        raise ValueError(f"{field_name} out of range for {bits} bits: {value}")

    return value


def resolve_pc_relative(
    token: str,
    label_table: dict[str, int],
    pc_address: int,
    bits: int,
    field_name: str,
) -> int:
    """Resolve a label or numeric literal into a PC-relative offset."""
    if token in label_table:
        value = label_table[token] - pc_address
    else:
        value = int(token, 0)

    return parse_signed_immediate(str(value), bits, field_name, align=2)


def encode_rtype(parts: list[str]) -> str:
    """Encode an R-type instruction."""
    if len(parts) != 4:
        raise ValueError(f"Invalid R-type syntax: {' '.join(parts)}")

    inst_name, rd_name, rs1_name, rs2_name = parts
    meta = get_instruction_meta(inst_name)

    rd_bin = get_register_bin(rd_name)
    rs1_bin = get_register_bin(rs1_name)
    rs2_bin = get_register_bin(rs2_name)

    return (
        meta["funct7"]
        + rs2_bin
        + rs1_bin
        + meta["funct3"]
        + rd_bin
        + meta["opcode"]
    )


def encode_itype(parts: list[str]) -> str:
    """Encode an I-type instruction."""
    inst_name = parts[0]
    meta = get_instruction_meta(inst_name)

    if len(parts) < 3:
        raise ValueError(f"Invalid I-type syntax: {' '.join(parts)}")

    rd_bin = get_register_bin(parts[1])

    if inst_name in LOAD_INSTRUCTIONS:
        if len(parts) != 3:
            raise ValueError(f"Invalid load syntax: {' '.join(parts)}")

        imm_str, rs1_name = parse_mem_operand(parts[2])
        rs1_bin = get_register_bin(rs1_name)
        imm_bin = int_to_bin(parse_signed_immediate(imm_str, 12, "load offset"), 12)

    elif inst_name == "jalr":
        if len(parts) == 3 and "(" in parts[2]:
            imm_str, rs1_name = parse_mem_operand(parts[2])
        elif len(parts) == 4:
            rs1_name, imm_str = parts[2], parts[3]
        else:
            raise ValueError(f"Invalid jalr syntax: {' '.join(parts)}")

        rs1_bin = get_register_bin(rs1_name)
        imm_bin = int_to_bin(parse_signed_immediate(imm_str, 12, "jalr offset"), 12)

    elif inst_name in SHIFT_IMM_INSTRUCTIONS:
        if len(parts) != 4:
            raise ValueError(f"Invalid shift-immediate syntax: {' '.join(parts)}")

        rs1_bin = get_register_bin(parts[2])
        shamt_bin = int_to_bin(
            parse_unsigned_immediate(parts[3], 5, "shift amount"),
            5,
        )
        imm_bin = meta["funct7"] + shamt_bin

    else:
        if len(parts) != 4:
            raise ValueError(f"Invalid immediate syntax: {' '.join(parts)}")

        rs1_bin = get_register_bin(parts[2])
        imm_bin = int_to_bin(parse_signed_immediate(parts[3], 12, "immediate"), 12)

    return imm_bin + rs1_bin + meta["funct3"] + rd_bin + meta["opcode"]


def encode_stype(parts: list[str]) -> str:
    """Encode an S-type instruction."""
    if len(parts) != 3:
        raise ValueError(f"Invalid S-type syntax: {' '.join(parts)}")

    inst_name, rs2_name, mem_operand = parts
    meta = get_instruction_meta(inst_name)

    imm_str, rs1_name = parse_mem_operand(mem_operand)

    rs1_bin = get_register_bin(rs1_name)
    rs2_bin = get_register_bin(rs2_name)
    imm_bin = int_to_bin(parse_signed_immediate(imm_str, 12, "store offset"), 12)

    imm_11_5 = imm_bin[:7]
    imm_4_0 = imm_bin[7:]

    return imm_11_5 + rs2_bin + rs1_bin + meta["funct3"] + imm_4_0 + meta["opcode"]


def encode_btype(parts: list[str], label_table: dict[str, int], pc_address: int) -> str:
    """Encode a B-type instruction."""
    if len(parts) != 4:
        raise ValueError(f"Invalid B-type syntax: {' '.join(parts)}")

    inst_name, rs1_name, rs2_name, target = parts
    meta = get_instruction_meta(inst_name)

    rs1_bin = get_register_bin(rs1_name)
    rs2_bin = get_register_bin(rs2_name)
    offset = resolve_pc_relative(target, label_table, pc_address, 13, "branch offset")
    imm_bin = int_to_bin(offset, 13)

    return (
        imm_bin[0]
        + imm_bin[2:8]
        + rs2_bin
        + rs1_bin
        + meta["funct3"]
        + imm_bin[8:12]
        + imm_bin[1]
        + meta["opcode"]
    )


def encode_utype(parts: list[str]) -> str:
    """Encode a U-type instruction."""
    if len(parts) != 3:
        raise ValueError(f"Invalid U-type syntax: {' '.join(parts)}")

    inst_name, rd_name, imm_str = parts
    meta = get_instruction_meta(inst_name)

    rd_bin = get_register_bin(rd_name)
    imm_bin = int_to_bin(int(imm_str, 0), 20)

    return imm_bin + rd_bin + meta["opcode"]


def encode_jtype(parts: list[str], label_table: dict[str, int], pc_address: int) -> str:
    """Encode a J-type instruction."""
    if len(parts) != 3:
        raise ValueError(f"Invalid J-type syntax: {' '.join(parts)}")

    inst_name, rd_name, target = parts
    meta = get_instruction_meta(inst_name)

    rd_bin = get_register_bin(rd_name)
    offset = resolve_pc_relative(target, label_table, pc_address, 21, "jump offset")
    imm_bin = int_to_bin(offset, 21)

    return (
        imm_bin[0]
        + imm_bin[10:20]
        + imm_bin[9]
        + imm_bin[1:9]
        + rd_bin
        + meta["opcode"]
    )


def assemble(instructions: list[str], label_table: dict[str, int]) -> list[str]:
    """Encode all instructions into 32-bit machine-code strings."""
    machine_codes = []

    for i, line in enumerate(instructions):
        pc_address = i * 4
        parts = line.replace(",", " ").split()

        if not parts:
            continue

        inst_name = parts[0]

        if inst_name not in isa_def.INSTRUCTIONS:
            raise ValueError(f"Assembly error at PC 0x{pc_address:04X}: {line}\nUnsupported instruction: {inst_name}")

        if inst_name not in SUPPORTED_INSTRUCTIONS:
            machine_codes.append(BLANK_MC)
            continue

        try:
            inst_type = get_instruction_meta(inst_name)["type"]

            if inst_type == "R":
                mc = encode_rtype(parts)
            elif inst_type == "I":
                mc = encode_itype(parts)
            elif inst_type == "S":
                mc = encode_stype(parts)
            elif inst_type == "B":
                mc = encode_btype(parts, label_table, pc_address)
            elif inst_type == "U":
                mc = encode_utype(parts)
            elif inst_type == "J":
                mc = encode_jtype(parts, label_table, pc_address)
            else:
                mc = BLANK_MC

        except Exception as exc:
            raise ValueError(
                f"Assembly error at PC 0x{pc_address:04X}: {line}\n{exc}"
            ) from exc

        machine_codes.append(mc)

    return machine_codes


TEST_DIR = SOFTWARE_DIR / "tests"

if __name__ == "__main__":
    src_file = TEST_DIR / "test_iss_in.asm"
    out_file = TEST_DIR / "test_iss_out.bin"

    lines = clean_code(src_file)

    if lines:
        labels, instructions = collect_labels_and_instructions(lines)

        print("--- Labels ---")
        for name, addr in labels.items():
            print(f"{name}: 0x{addr:04X}")

        print("\n--- Instruction Memory ---")
        for i, inst in enumerate(instructions):
            print(f"0x{(i * 4):04X}: {inst}")

        print("\n--- Assembled ---")
        machine_codes = assemble(instructions, labels)

        with open(out_file, "w", encoding="utf-8") as out_file_obj:
            for i, mc in enumerate(machine_codes):
                print(f"0x{(i * 4):04X} | {mc} | {instructions[i]}")
                out_file_obj.write(f"{mc}\n")
