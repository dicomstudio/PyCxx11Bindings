import ctypes
import os
from pathlib import Path

from cxx11bindings import C11Stream, ErrorCodes, PyC11Stream

project_root = Path(__file__).resolve().parents[1]
if os.name == "nt":
    library_name = "Cxx11BindingsTests.dll"
    library_paths = [
        project_root / library_name,
        project_root / "build" / "lib" / "Release" / library_name,
    ]
elif os.name == "posix":
    library_name = "Cxx11BindingsTests.so"
    library_paths = [
        project_root / library_name,
        project_root / "build" / "lib" / library_name,
    ]
else:
    assert False, "Unsupported OS"

library_path = next((path for path in library_paths if path.is_file()), None)
if library_path is None:
    searched_paths = ", ".join(str(path) for path in library_paths)
    raise FileNotFoundError(
        f"Could not find {library_name}; searched: {searched_paths}"
    )

dll = ctypes.CDLL(str(library_path))

dll.test_c11_stream_write.argtypes = [
    ctypes.POINTER(C11Stream),
    ctypes.c_void_p,
    ctypes.c_int32,
]
dll.test_c11_stream_write.restype = ctypes.c_int32
dll.test_c11_stream_flush.argtypes = [ctypes.POINTER(C11Stream)]
dll.test_c11_stream_flush.restype = ctypes.c_int


def test_default1():
    filename = "default1.bin"
    try:
        with open(filename, "wb") as f:
            with PyC11Stream(f) as stream:
                data = b"abcdefghijklmnopqrstuvwxyz"
                ret = dll.test_c11_stream_write(stream.ptr, data, len(data))
                assert ret == 26
                # can we assume no flush yet ?
                assert os.path.getsize(filename) == 0
                ret = dll.test_c11_stream_flush(stream.ptr)
                assert ret == 0
                assert os.path.getsize(filename) == 26
    except Exception as e:
        print("Error occurred: ", e)
        assert False, "No exception should occur in test"
    finally:
        os.remove(filename)


def test_exception():
    filename = "exception.bin"
    try:
        with open(filename, "w"):
            pass
        assert os.path.getsize(filename) == 0
        # open read-only it should trigger an exception:
        with open(filename, "rb") as f:
            with PyC11Stream(f) as stream:
                data = b"abcdefghijklmnopqrstuvwxyz"
                ret = dll.test_c11_stream_write(stream.ptr, data, len(data))
                assert ret == ErrorCodes.C11_E_NOTSUPPORTED.value
                ret = dll.test_c11_stream_flush(stream.ptr)
                assert ret == 0
    except Exception as e:
        print("Error occurred: ", e)
        assert False, "No exception should occur in test"
    finally:
        os.remove(filename)
