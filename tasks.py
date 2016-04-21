
from invoke import Collection
from dktasklib import version
from dktasklib import upversion
from dktasklib import publish

ns = Collection(
    'pydeps',
    version,
    upversion,
    publish
)
