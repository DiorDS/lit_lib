from lit_lib import Lit

l = Lit("./config.json", diasble_warnings=True)
l["DE"] = [
    ("Hello World", "hi")
]

de = l["DE"]

print(de["Hi everyone"])