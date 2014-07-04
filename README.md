# Linode Python Bindings


The bindings consist of three pieces:
  - api.py: Core library that manages authentication and api calls
  - shell.py: A command line interface to api.py that allows you to invoke
      a specific api command quickly
  - oop.py: An object oriented interface to api.py inspired by django

For definitive documentation on how the api works please visit:
https://www.linode.com/api

## API Keys


When creating an api object you may specify the key manually, or use the
Api.user_getapikey which will return your apikey as well as set the internal
key that will be used for subsequent api calls.

Both the shell.py and oop.py have mechanisms to pull the api key from the
environment variable LINODE_API_KEY as well.

## Batching


Batching should be used with care, once enabled all api calls are cached until
Api.batchFlush() is called, however you must remember the order in which calls
were made as that's the order of the list returned to you

## License


This code is provided under an MIT-style license. Please refer to the LICENSE
file in the root of the project for specifics.
