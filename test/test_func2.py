import ctypes
import os

from cxx11bindings import PyC11Stream

# Load the DLL (use the full path if not in the current directory)
if os.name == "nt":
    dll = ctypes.CDLL("./Cxx11BindingsTests.dll")
elif os.name == "posix":
    dll = ctypes.CDLL("./Cxx11BindingsTests.so")
else:
    assert False, "Unsupported OS"


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
