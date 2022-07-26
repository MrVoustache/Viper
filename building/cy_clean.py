from sys import argv

def print_usage():
    print("Usage :")
    print("py cy_clean.py <source>   -> Deletes the file(s) at source that result from a cython compilation")
    exit()

if len(argv) != 2:
    print_usage()

import os.path as pth
import os

target = argv[1]

if pth.isfile(target) and target.endswith((".py", ".pyx")):
    files = [target]
elif pth.isdir(target):
    from fs.iterators import type_iter
    from itertools import chain
    from sys import platform
    c_it = type_iter("c", target)
    cpp_it = type_iter("cpp", target)
    html_iter = type_iter("html", target)
    if "win" in platform.lower():
        mod_it = type_iter("pyd", target)
    else:
        mod_it = type_iter("so", target)
    files = list(chain(c_it, cpp_it, html_iter, mod_it))
else:
    print("Could not compile " + repr(target))
    exit()


for p in files:
    os.remove(p)