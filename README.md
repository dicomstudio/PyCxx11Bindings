[![img](https://img.shields.io/github/contributors/dicomstudio/PyCxx11Bindings.svg?style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/graphs/contributors)
[![img](https://img.shields.io/github/forks/dicomstudio/PyCxx11Bindings.svg?style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/network/members)
[![img](https://img.shields.io/github/stars/dicomstudio/PyCxx11Bindings.svg?style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/stargazers)
[![img](https://img.shields.io/github/issues/dicomstudio/PyCxx11Bindings.svg?style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/issues)
[![img](https://img.shields.io/github/license/dicomstudio/PyCxx11Bindings.svg?style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/blob/main/LICENSE)
[![img](https://img.shields.io/github/actions/workflow/status/dicomstudio/PyCxx11Bindings/test.yaml.svg?label=test&style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/actions/workflows/test.yaml)
[![img](https://img.shields.io/github/actions/workflow/status/dicomstudio/PyCxx11Bindings/release.yaml.svg?label=release&style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/actions/workflows/release.yaml)
[![img](https://img.shields.io/badge/pre--commit-enabled-brightgreen.svg?logo=pre-commit&style=flat-square)](https://github.com/dicomstudio/PyCxx11Bindings/blob/main/.pre-commit-config.yaml)

[![img](https://img.shields.io/pypi/v/PyCxx11Bindings.svg?style=flat-square)](https://pypi.org/project/PyCxx11Bindings)
[![img](https://img.shields.io/pypi/pyversions/PyCxx11Bindings.svg?style=flat-square)](https://pypi.org/project/PyCxx11Bindings)

# PyCxx11Bindings

PyCxx11Bindings adapts Python file-like objects to the C `c11_stream` interface
using `ctypes`. This lets a native library written in C or C++ call Python
streams without needing to expose C++ stream types across the language boundary.

The Python package provides the callback adapter; it does not include the
native library that consumes the callbacks. That library must expose a C ABI
function accepting a `struct c11_stream*`.

## Installation

Install the package from PyPI:

```shell
python -m pip install PyCxx11Bindings
```

## Usage

Declare the native function with `ctypes`, wrap Python streams, and pass their
`c11_stream` pointers to the native function:

```python
import ctypes

from cxx11bindings import C11Stream, PyC11Stream

# Load your own native library, which must export acme_convert.
native = ctypes.CDLL("path/to/libacme.so")
convert = native.acme_convert
convert.argtypes = [
    ctypes.POINTER(C11Stream),
    ctypes.POINTER(C11Stream),
]
convert.restype = ctypes.c_int

with open("input.dat", "rb") as input_file, open("output.dat", "wb") as output_file:
    input_stream = PyC11Stream(input_file)
    output_stream = PyC11Stream(output_file)
    result = convert(input_stream.ptr, output_stream.ptr)
    if result != 0:
        raise RuntimeError(f"Native conversion failed with code {result}")
```

On Windows, load a `.dll`; on macOS, load a `.dylib`. Use the path to the
native library built for your platform and process architecture. The C
declaration for the example function is:

```c
int acme_convert(struct c11_stream* input, struct c11_stream* output);
```

Include `cxx11bindings/stream.h` in the native project to use the interface.
The callback table and stream wrapper must stay alive for the entire native
call. The interface is synchronous: do not retain the pointer or access a
callback's buffer after the call or callback returns. Calls may block, and
thread safety is the responsibility of the application.

`PyC11Stream` delegates read, write, seek, flush, and truncate operations to
the wrapped Python object. Exceptions raised by those operations are converted
to negative `C11_E_*` error codes for native code. An unknown exception maps
to `C11_E_UNMAPPED`. Check the native function's documented return contract to
determine how it reports callback failures.

## Native interface

The C ABI is defined by `c11_stream` in
[`native/include/cxx11bindings/stream.h`](native/include/cxx11bindings/stream.h).
It consists of five callbacks:

| Callback | Success result |
| --- | --- |
| `read` | Number of bytes read; short reads are allowed |
| `write` | Number of bytes written; short writes are allowed |
| `seek` | New stream position |
| `flush` | Zero |
| `trunc` | New stream length |

Callbacks return negative error codes on failure. The header defines the
complete error-code list and callback signatures. C++ consumers can use the
adapters in `native/include/cxx11bindings/streambuf.hxx`; the optional native
shared library provides `FILE*` and `std::filebuf` implementations. Neither
the shared library nor the C++ adapters are required to implement the
interface from Python.

## Build and test from source

Building the native project requires CMake and C/C++ compilers. Initialize its
Git submodule and build:

```shell
git submodule update --init --recursive
cmake -S native -B build -DBUILD_TESTING=OFF
cmake --build build --config Release
```

To build the native C++ unit tests too, install GoogleTest and configure with
`-DBUILD_TESTING=ON`.

Install the Python test dependencies and run the test suite:

```shell
python -m pip install -e ".[test]"
python -m pytest
```

## Contributing

Contributions and questions are welcome. Please read the
[contributing guidelines](CONTRIBUTING.md) before opening an issue or pull
request.

## License

Distributed under the [MIT License](LICENSE).

## Related projects

* [Cxx11Bindings](https://github.com/dicomstudio/Cxx11Bindings)
* [Cxx11BindingsSharp](https://github.com/dicomstudio/Cxx11BindingsSharp)
* [PyCxx11Bindings on PyPI](https://pypi.org/project/PyCxx11Bindings/)
