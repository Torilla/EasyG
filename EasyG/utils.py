class Singleton(object):
    __instance = None

    def __init__(self):
        cls = type(self)
        if cls.__instance:
            raise RuntimeError(f"Can't create two instances of {cls.__name__}! "
                               f"Use {cls.__name__}.getGlobalInstance() to "
                               "retrieve the current instance.")

        cls.__instance = self

    @classmethod
    def getGlobalInstance(cls):
        return cls.__instance
