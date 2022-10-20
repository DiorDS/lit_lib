# lit_lib


### 1 localisation ended in 1008 ns!
```
from time import perf_counter_ns

from lit_lib import Lit

l = Lit("./config.json", diasble_warnings=True)

start = perf_counter_ns()

for i in range(1000000):           
    l["DE"]["Hi everyone"]

end = perf_counter_ns()
```
