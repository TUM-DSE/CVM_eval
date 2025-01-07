from ctypes import *

so_file = "/root/libmy_outb.so"
my_functions = CDLL(so_file)
my_functions.my_outb(249)
