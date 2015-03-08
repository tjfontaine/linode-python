from distutils.core import setup

setup(
    name = "linode-python",
    version = "1.1.1",
    description = "Python bindings for Linode API",
    author = "TJ Fontaine",
    author_email = "tjfontaine@gmail.com",
    url = "https://github.com/tjfontaine/linode-python",
    packages = ['linode'],
    extras_require = {
        'requests': ["requests"],
    },
)
