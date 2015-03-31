

class User:

    def __init__(**args):
        for key, value in args.items():
            setattr(self, key, value)
