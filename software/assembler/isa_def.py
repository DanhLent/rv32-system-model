# File: software/assembler/isa_def.py
"""
ISA Definitions for RISC-V 32-bit (RV32I)
Contains register ABI mappings and instruction opcodes.
"""

# =============================================================================
# REGISTERS
# =============================================================================
REGISTERS = {
    # Zero, Return Address, and Pointers
    'x0':  '00000', 'zero': '00000',
    'x1':  '00001', 'ra':   '00001',
    'x2':  '00010', 'sp':   '00010',
    'x3':  '00011', 'gp':   '00011',
    'x4':  '00100', 'tp':   '00100',

    # Arguments / Return values
    'x10': '01010', 'a0':   '01010',
    'x11': '01011', 'a1':   '01011',
    'x12': '01100', 'a2':   '01100',
    'x13': '01101', 'a3':   '01101',
    'x14': '01110', 'a4':   '01110',
    'x15': '01111', 'a5':   '01111',
    'x16': '10000', 'a6':   '10000',
    'x17': '10001', 'a7':   '10001',

    # Saved registers
    'x8':  '01000', 's0':   '01000', 'fp': '01000',
    'x9':  '01001', 's1':   '01001',
    'x18': '10010', 's2':   '10010',
    'x19': '10011', 's3':   '10011',
    'x20': '10100', 's4':   '10100',
    'x21': '10101', 's5':   '10101',
    'x22': '10110', 's6':   '10110',
    'x23': '10111', 's7':   '10111',
    'x24': '11000', 's8':   '11000',
    'x25': '11001', 's9':   '11001',
    'x26': '11010', 's10':  '11010',
    'x27': '11011', 's11':  '11011',

    # Temporaries
    'x5':  '00101', 't0':   '00101',
    'x6':  '00110', 't1':   '00110',
    'x7':  '00111', 't2':   '00111',
    'x28': '11100', 't3':   '11100',
    'x29': '11101', 't4':   '11101',
    'x30': '11110', 't5':   '11110',
    'x31': '11111', 't6':   '11111'
}

# =============================================================================
# INSTRUCTION OPCODES
# =============================================================================
INSTRUCTIONS = {
    # --- R-Type ---
    'add':  {'type': 'R', 'opcode': '0110011', 'funct3': '000', 'funct7': '0000000'},
    'sub':  {'type': 'R', 'opcode': '0110011', 'funct3': '000', 'funct7': '0100000'},
    'sll':  {'type': 'R', 'opcode': '0110011', 'funct3': '001', 'funct7': '0000000'},
    'slt':  {'type': 'R', 'opcode': '0110011', 'funct3': '010', 'funct7': '0000000'},
    'sltu': {'type': 'R', 'opcode': '0110011', 'funct3': '011', 'funct7': '0000000'},
    'xor':  {'type': 'R', 'opcode': '0110011', 'funct3': '100', 'funct7': '0000000'},
    'srl':  {'type': 'R', 'opcode': '0110011', 'funct3': '101', 'funct7': '0000000'},
    'sra':  {'type': 'R', 'opcode': '0110011', 'funct3': '101', 'funct7': '0100000'},
    'or':   {'type': 'R', 'opcode': '0110011', 'funct3': '110', 'funct7': '0000000'},
    'and':  {'type': 'R', 'opcode': '0110011', 'funct3': '111', 'funct7': '0000000'},

    # --- I-Type (ALU) ---
    'addi': {'type': 'I', 'opcode': '0010011', 'funct3': '000'},
    'slti': {'type': 'I', 'opcode': '0010011', 'funct3': '010'},
    'sltiu': {'type': 'I', 'opcode': '0010011', 'funct3': '011'},
    'xori': {'type': 'I', 'opcode': '0010011', 'funct3': '100'},
    'ori':  {'type': 'I', 'opcode': '0010011', 'funct3': '110'},
    'andi': {'type': 'I', 'opcode': '0010011', 'funct3': '111'},

    # --- I-Type (Shift) ---
    'slli': {'type': 'I', 'opcode': '0010011', 'funct3': '001', 'funct7': '0000000'},
    'srli': {'type': 'I', 'opcode': '0010011', 'funct3': '101', 'funct7': '0000000'},
    'srai': {'type': 'I', 'opcode': '0010011', 'funct3': '101', 'funct7': '0100000'},

    # --- I-Type (Load) ---
    'lb':   {'type': 'I', 'opcode': '0000011', 'funct3': '000'},
    'lh':   {'type': 'I', 'opcode': '0000011', 'funct3': '001'},
    'lw':   {'type': 'I', 'opcode': '0000011', 'funct3': '010'},
    'lbu':  {'type': 'I', 'opcode': '0000011', 'funct3': '100'},
    'lhu':  {'type': 'I', 'opcode': '0000011', 'funct3': '101'},

    # --- S-Type (Store) ---
    'sb':   {'type': 'S', 'opcode': '0100011', 'funct3': '000'},
    'sh':   {'type': 'S', 'opcode': '0100011', 'funct3': '001'},
    'sw':   {'type': 'S', 'opcode': '0100011', 'funct3': '010'},

    # --- B-Type (Branch) ---
    'beq':  {'type': 'B', 'opcode': '1100011', 'funct3': '000'},
    'bne':  {'type': 'B', 'opcode': '1100011', 'funct3': '001'},
    'blt':  {'type': 'B', 'opcode': '1100011', 'funct3': '100'},
    'bge':  {'type': 'B', 'opcode': '1100011', 'funct3': '101'},
    'bltu': {'type': 'B', 'opcode': '1100011', 'funct3': '110'},
    'bgeu': {'type': 'B', 'opcode': '1100011', 'funct3': '111'},

    # --- U-Type ---
    'lui':  {'type': 'U', 'opcode': '0110111'},
    'auipc': {'type': 'U', 'opcode': '0010111'},

    # --- J-Type ---
    'jal':  {'type': 'J', 'opcode': '1101111'},
    # JALR
    'jalr': {'type': 'I', 'opcode': '1100111', 'funct3': '000'},

    # --- System ---
    'ecall': {'type': 'I', 'opcode': '1110011', 'funct3': '000'},
    'ebreak': {'type': 'I', 'opcode': '1110011', 'funct3': '000'}
}
