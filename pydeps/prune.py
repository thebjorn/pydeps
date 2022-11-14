"""
Routines for pruning the dependency graph.
"""

def prune_emptyish_init_files(depgraph):
    """Remove any nodes for ``__init__.py`` files that do not import anything.

       These nodes are created for ``a`` and ``b`` from the following import::

           from a.b import c

       Args:
           depgraph (DepGraph): The output of ``py2depgraph.py2dep(...)``.
    """
    # TODO: this removes too much, e.g. from collections import OrderedDict
    #       will not list collections as a dependency since OrderedDict is 
    #       entirely implemented in the __init__.py file
    for src in depgraph.source_iter():
        if src.filename == '__init__.py':
            if src.in_degree == 0:
                depgraph.exclude_source(src)

    depgraph.remove_excluded()
    return depgraph
