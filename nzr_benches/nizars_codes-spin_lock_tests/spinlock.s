	.section	.rodata.str1.1,"aMS",@progbits,1
.LC0:
	.text
	.p2align 4,,15
	.globl	spin_lock
	.type	spin_lock, @function
spin_lock:
.LFB11:
	.cfi_startproc

       push   %rbp
       mov    %rsp,%rbp
       mov    $0x20000,%eax
       lock xadd %eax,(%rdi)
       mov    %eax,%edx
       shr    $0x10,%edx
       cmp    %ax,%dx
       jne    .LP1
.LP2:
       pop    %rbp
       retq
.LP1:
       movzwl (%rdi),%eax
       mov    %edx,%ecx
       cmp    %dx,%ax
       je     .LP2
.LP3:
       pause
       movzwl (%rdi),%eax
       cmp    %cx,%ax
       jne    .LP3
       pop    %rbp
	   retq


	.cfi_endproc
.LFE11:
	.size	spin_lock, .-spin_lock
	.section	.rodata.str1.1
.LC1:
	.text
	.p2align 4,,15
	.globl	spin_unlock
	.type	spin_unlock, @function
spin_unlock:
.LFB12:
	.cfi_startproc

	addw $0x02,(%rdi)
	retq
	
	.cfi_endproc
.LFE12:
	.size	spin_unlock, .-spin_unlock
	.section	.note.GNU-stack,"",@progbits
