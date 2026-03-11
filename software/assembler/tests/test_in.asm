# jojojojojo
main:
    add x1, x2, x3      # r-type
    
    # i-type
    addi x4, x1, 10     # i-type: cong voi 10
    sub x5, x4, x1      # lai la r-type
    
loop_start:             # ok label
    lw x6, 0(x5)        # load (i-type)
    sw x6, 4(x5)        # store (s-type)

    # comment o giua
              and x7, x6, x1      # r-type: phep AND bit
    or x8, x7, x2       # r-type: phep OR bit
    
    beq x8, x0, end_prg # branch (b-type), nhay den cuoi neu bang 0
    
    sll x9, x8, x1      # r-type: dich trai logic
    
    jal x0, loop_start  # jump (j-type)

end_prg:
    # ket thuc
    add x10, x0, x0     # r-type: clear x10 ve 0
