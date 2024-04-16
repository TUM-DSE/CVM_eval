#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>

#define MODULE_NAME "hello"

MODULE_LICENSE("GPL");

static int __init hello_init(void) {
    printk(KERN_INFO "hello world!\n");
    return 0;
}

static void __exit hello_exit(void) {
    printk(KERN_INFO "bye world!\n");
}

module_init(hello_init);
module_exit(hello_exit);
