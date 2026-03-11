"""
RISC-V (RV32I) Assembler
"""

import isa_def

def int_to_bin(value: int, bits: int) -> str:
    """
    Converts a decimal integer to its two's complement binary string representation.
    """
    mask = (1 << bits) - 1
    return format(value & mask, f'0{bits}b')

def parse_mem_operand(operand: str) -> tuple[str, str]:
    """
    Parses a memory operand string (e.g., "offset(register)") into its components.
    """
    parts = operand.replace(')', '').split('(')
    return parts[0], parts[1]

def clean_code(filepath: str) -> list:
    """
    Reads the source assembly file and performs preprocessing.
    Removes inline comments and filters out empty lines.
    Returns a list of sanitized instruction strings.
    """
    clean_lines = []
    try:
        with open(filepath, 'r') as file:
            for line in file:
                # Isolate the instruction from any trailing comments
                instruction = line.split('#')[0].strip()
                if instruction:
                    clean_lines.append(instruction)
    except FileNotFoundError:
        print(f"Error: Could not find source file '{filepath}'")
    
    return clean_lines

def build_label_table(clean_lines: list) -> tuple[dict, list]:
    """
    Pass 1: Scans the sanitized code to identify labels and compute instruction addresses.
    Returns a tuple containing the symbol table and the list of pure instructions.
    """
    label_table = {}
    instructions_only = []
    pc_address = 0

    for line in clean_lines:
        if line.endswith(':'):
            # Extract label name without the colon
            label_name = line[:-1]
            label_table[label_name] = pc_address
        else:
            instructions_only.append(line)
            # RV32I instructions are fixed at 32 bits (4 bytes)
            pc_address += 4
            
    return label_table, instructions_only

def encode_rtype(parts: list) -> str:
    """
    Encodes an R-Type instruction into a 32-bit machine code string.
    Format: funct7[31:25] | rs2[24:20] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    """
    inst_name, rd_name, rs1_name, rs2_name = parts[0], parts[1], parts[2], parts[3]

    # Map register names to 5-bit binary strings
    rd_bin = isa_def.REGISTERS[rd_name]
    rs1_bin = isa_def.REGISTERS[rs1_name]
    rs2_bin = isa_def.REGISTERS[rs2_name]

    # Retrieve instruction-specific control fields
    opcode = isa_def.INSTRUCTIONS[inst_name]['opcode']
    funct3 = isa_def.INSTRUCTIONS[inst_name]['funct3']
    funct7 = isa_def.INSTRUCTIONS[inst_name]['funct7']

    # Concatenate fields according to the RV32I specification
    return funct7 + rs2_bin + rs1_bin + funct3 + rd_bin + opcode

def encode_itype(parts: list) -> str:
    """
    Encodes an I-Type instruction into a 32-bit machine code string.
    Format: imm[11:0] | rs1[19:15] | funct3[14:12] | rd[11:7] | opcode[6:0]
    """
    inst_name, rd_name = parts[0], parts[1]

    opcode = isa_def.INSTRUCTIONS[inst_name]['opcode']
    funct3 = isa_def.INSTRUCTIONS[inst_name]['funct3']
    rd_bin = isa_def.REGISTERS[rd_name]

    # Handle syntax differences between load instructions and immediate ALU operations
    if inst_name in ['lw', 'lb', 'lh', 'lbu', 'lhu']:
        imm_str, rs1_name = parse_mem_operand(parts[2])
    else:
        rs1_name, imm_str = parts[2], parts[3]

    rs1_bin = isa_def.REGISTERS[rs1_name]
    imm_bin = int_to_bin(int(imm_str), 12)

    return imm_bin + rs1_bin + funct3 + rd_bin + opcode

def encode_stype(parts: list) -> str:
    """
    Encodes an S-Type (Store) instruction into a 32-bit machine code string.
    Format: imm[11:5] | rs2[24:20] | rs1[19:15] | funct3[14:12] | imm[4:0] | opcode[6:0]
    """
    inst_name, rs2_name = parts[0], parts[1]

    imm_str, rs1_name = parse_mem_operand(parts[2])

    rs1_bin = isa_def.REGISTERS[rs1_name]
    rs2_bin = isa_def.REGISTERS[rs2_name]
    opcode = isa_def.INSTRUCTIONS[inst_name]['opcode']
    funct3 = isa_def.INSTRUCTIONS[inst_name]['funct3']

    imm_bin = int_to_bin(int(imm_str), 12)

    # Bit-slicing the 12-bit immediate to preserve fixed rs1/rs2 locations
    imm_11_5 = imm_bin[0:7]
    imm_4_0 = imm_bin[7:12]

    return imm_11_5 + rs2_bin + rs1_bin + funct3 + imm_4_0 + opcode

def assemble(instructions: list) -> list:
    """
    Dispatcher function. Parses instruction mnemonics, determines the format type,
    and routes operands to the appropriate encoding function.
    """
    machine_codes = []

    for line in instructions:
        # Standardize separators by replacing commas with spaces
        parts = line.replace(',', ' ').split()
        inst_name = parts[0]
        inst_type = isa_def.INSTRUCTIONS[inst_name]['type']

        # Default placeholder (32 spaces) to maintain memory alignment for unimplemented types
        mc = " " * 32

        # Route to specific encoders based on instruction format
        if inst_type == 'R':
            mc = encode_rtype(parts)
        elif inst_type == 'I':
            mc = encode_itype(parts) 
        elif inst_type == 'S':
            mc = encode_stype(parts) 
        elif inst_type in ['B', 'U', 'J']:
            pass # Pending implementation
        else:
            raise ValueError(f"Unsupported")

        machine_codes.append(mc)

    return machine_codes

if __name__ == "__main__":
    src_file = "test_in.asm"
    lines = clean_code(src_file)

    if lines:
        labels, instructions = build_label_table(lines)

        print("--- Symbol Table (Labels) ---")
        for name, addr in labels.items():
            print(f"{name}: 0x{addr:04X}")

        print("\n--- Instruction Memory Allocation ---")
        for i, inst in enumerate(instructions):
            print(f"0x{(i * 4):04X}: {inst}")

        print("\n--- Assembled Machine Code ---")
        machine_codes = assemble(instructions)

        # Output the generated machine code to a binary file
        with open("test_out.bin", "w") as out_file:
            for i, mc in enumerate(machine_codes):
                print(f"0x{(i * 4):04X} | {mc} | {instructions[i]}")
                out_file.write(f"{mc}\n")
