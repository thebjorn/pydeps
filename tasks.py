# pragma: nocover
from invoke import Collection, task
from dktasklib import version
from dktasklib import upversion
from dktasklib import publish
from dktasklib import docs
from dktasklib.package import Package, package


@task
def freeze(ctx):
    "pip freeze, but without -e installed packages"
    ctx.run("pip list --exclude-editable --format freeze")


@task
def outdated(ctx):
    "list all outdated requirements"
    ctx.run("pip list --outdated")


ns = Collection(
    'pydeps',
    freeze,
    outdated,
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
