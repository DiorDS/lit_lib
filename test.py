from time import perf_counter_ns

from lit_lib import Lit, langs_from_compiled_dict

l = Lit("./config.json", diasble_warnings=True)

start = perf_counter_ns()

for i in range(1000000):           
    l["DE"]["Hi everyone"]

end = perf_counter_ns()

print((end - start) / 1000000)
