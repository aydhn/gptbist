import re
path = "bist_signal_bot/__main__.py"
with open(path, "r") as f:
    content = f.read()

# Make sure execute_model_registry_command is actually hit instead of the print "BIST Signal Bot OK"
# It seems __main__.py has a short-circuit for other args. Let's see what's in there.
print("main contents:")
print(content[:200])
