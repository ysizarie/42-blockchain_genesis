def unlimited_args(*args, **kargs):
    for arg in args:
        print(arg)


unlimited_args(*[1, 2, 3])
