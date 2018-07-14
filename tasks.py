# pragma: nocover
from invoke import Collection
from dktasklib import version
from dktasklib import upversion
from dktasklib import publish
from dktasklib import docs
from dktasklib.package import Package, package


ns = Collection(
    'pydeps',
    version,
    upversion,
    publish,
    docs,
    package
)
ns.configure({
    'pkg': Package(),
    'run': {
        'echo': True
    }
})
           
