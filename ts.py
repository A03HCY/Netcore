class MyClass:
    def __init__(self):
        self.__routes = {}

    def get_functions(self):
        members = dir(self)
        for member in members:
            if member.startswith("__") or isinstance(getattr(self, member), (type(self.__init__), property)):
                continue
            if callable(getattr(self, member)):
                self.__routes[member] = getattr(self, member)

    def execute_functions(self):
        for name, func in self.__routes.items():
            func()

    def example_function(self):
        print("Example function")

    def __private_function(self):
        print("Private function")

    def variable_function(self):
        print("Variable function")

my_object = MyClass()
my_object.get_functions()
my_object.execute_functions()