from acdpnet import protocol

class Authority:
    def __init__(self) -> None:
        pass

    def add(name:str, pwd:str, group:str, uid:str=None) -> None:
        # add a user in the given group
        # will create a group when it's not have
        pass

    def remove(gourp:str, uid:str) -> bool:
        # remove a user
        pass

    def gourp(name:str=None) -> dict:
        # return the list of all group or the all users in the group when the name is None
        pass


class Tree:
    def __init__(self) -> None:
        pass

    def open(port:int) -> None:
        pass

    def close() -> None:
        pass

