# from . import definitions


class NodeCollection(object):

    def __init__(self):
        self.list = list()


class FunctionCollection(NodeCollection):
    pass


class NodeWalker(object):

    def __init__(self, node, visitor):
        self.node = node
        self.depth = 0
        self.visitor = visitor

        self.visitor(self, self.node)

    def walk(self, currentNode=None):
        self.depth += 1
        if currentNode:
            self.node = currentNode
            self.visitor(self, currentNode)
        elif not currentNode:
            currentNode = self.node
        for x in currentNode.getChildren():
            self.node = x
            self.visitor(self, self.node)

    # def visitor(self, node):
    #     raise NotImplementedError()
