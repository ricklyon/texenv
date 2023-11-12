
def macro_kwargs(arg1, arg2, kw1="kw1-default", kw2="kw2-default"):
    return arg1 + " + " + arg2 + " KW: " + kw1 + " + " + kw2

def emb_args(arg1, arg2):
    return arg1 + "|E|" + arg2