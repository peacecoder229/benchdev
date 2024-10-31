#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/sched.h>
#include <linux/pid.h>
#include <asm/io.h>

unsigned long pid_to_cr3(int pid)
{
        struct task_struct *task;
	struct mm_struct *mm;
	void *cr3_virt;
	unsigned long cr3_phys;

	task = pid_task(find_vpid(pid), PIDTYPE_PID);

	if (task == NULL)
		return 0; // pid has no task_struct

	mm = task->mm;



	if (mm == NULL) {
		mm = task->active_mm;
	}

	if (mm == NULL)
		return 0; // this shouldn't happen, but just in case

	cr3_virt = (void *) mm->pgd;
	cr3_phys = virt_to_phys(cr3_virt);

	return cr3_phys;
}
