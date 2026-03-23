# I-type
addi  x1,  x0, 10
addi  x2,  x0, 3
addi  x13, x0, -1
andi  x14, x13, 0x0F
slti  x15, x13, 0
sltiu x16, x13, 1
xori  x17, x1, 0x0F
ori   x18, x2, 0x08
slli  x19, x2, 4
srli  x20, x13, 1
srai  x21, x13, 1

# R-type
add   x3,  x1, x2
sub   x4,  x1, x2
and   x5,  x1, x2
or    x6,  x1, x2
xor   x7,  x1, x2
sll   x8,  x2, x2
srl   x9,  x1, x2
sra   x10, x1, x2
slt   x11, x2, x1
sltu  x12, x2, x1

# U-type
lui   x22, 0x12345
auipc x23, 0x00001

# Unsupported
beq   x0, x0, done
done: