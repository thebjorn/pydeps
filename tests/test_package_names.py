

from pydeps.package_names import find_package_names


def test_find_package_names():
    packages = find_package_names()
    # assert 'pip' in packages
    assert 'pytest' in packages
