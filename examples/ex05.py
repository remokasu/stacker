from stacker import Stacker
from stacker import Stacker

stacker = Stacker()
stacker.eval(
    """time $s_t set
100000 $n set
0 $p set
0 n $k {
    -1 k ^ 2 k * 1 + / p + p set
} do
4 p * p set
time $e_t set

p echo
"time: " e_t s_t - str + echo
"""
)
