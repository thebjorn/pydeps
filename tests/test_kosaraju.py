
from pydeps.depgraph import Graph, GraphNode


class Source:
    def __init__(self, name):
        self.name = name
        self.imported_by = set()

def test_kosaraju():
    nodes = [GraphNode(Source(str(i))) for i in range(10)]
    edges = [
        (nodes[0], nodes[1]),
        (nodes[1], nodes[2]),
        (nodes[2], nodes[0]),
        (nodes[2], nodes[8]),
        (nodes[8], nodes[9]),
        (nodes[1], nodes[3]),
        (nodes[3], nodes[4]),
        (nodes[4], nodes[5]),
        (nodes[5], nodes[6]),
        (nodes[6], nodes[3]),
        (nodes[5], nodes[7]),
    ]
    graph = Graph(nodes, edges)
    # print(graph)
    # import pprint
    # pprint.pprint(graph)
    scc = graph.kosaraju()
    print(scc)
    assert scc == [
        {nodes[3], nodes[4], nodes[5], nodes[6]}, 
        {nodes[2], nodes[0], nodes[1]}, 
        {nodes[7]},
        {nodes[8]},
        {nodes[9]}
    ]
