from lit_lib import Lit, langs_from_compiled_dict

l = Lit("./config.json", diasble_warnings=True)


print(l["DE"]["Hi everyone"])
print(l["UK"]["Hi everyone"])
print(l["BE"]["Hi everyone"])
print(l["FI"]["Hi everyone"])
print(l["FI"]["Hi everyone"])


print(l.compile_all())
print(langs_from_compiled_dict(l.compile_all()))