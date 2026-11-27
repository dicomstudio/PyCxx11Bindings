import ctypes
import errno
import os

from cxx11bindings import ErrorCodes, PyC11Stream, exception_to_code


def test_default():
    filename = "default.bin"
    try:
        with open(filename, "wb") as f:
            with PyC11Stream(f) as stream:
                assert stream is not None
    except Exception as e:
        print("Error occurred: ", e)
        assert False, "Failed to create PyC11Stream"


def test_truncate_file_to_10_bytes():
    file_path = "truncate_test.bin"
    # Write more than 10 bytes
    with open(file_path, "wb") as f:
        stream = PyC11Stream(f)
        stream.write(b"abcdefghijklmnopqrstuvwxyz")
    # Truncate to 10 bytes
    with open(file_path, "r+b") as f:
        stream = PyC11Stream(f)
        stream.truncate(10)
    # Verify length
    assert os.path.getsize(file_path) == 10
    # Optionally, check content
    with open(file_path, "rb") as f:
        stream = PyC11Stream(f)
        data = stream.read()
        assert data == b"abcdefghij"


def test_unmapped_callback_exception_returns_unmapped_error_code():
    class FailingStream:
        def read(self, _):
            raise TypeError("unexpected stream error")

        def close(self):
            pass

    stream = PyC11Stream(FailingStream())
    buffer = (ctypes.c_uint8 * 1)()

    result = stream._c11_stream.read(None, buffer, len(buffer))

    assert result == ErrorCodes.C11_E_UNMAPPED.value


def test_python_exceptions_map_to_native_error_codes():
    cases = [
        (NotImplementedError(), ErrorCodes.C11_E_NOTIMPLEMENTED),
        (PermissionError(), ErrorCodes.C11_E_UNAUTHORIZED),
        (MemoryError(), ErrorCodes.C11_E_OUTOFMEMORY),
        (TimeoutError(), ErrorCodes.C11_E_TIMEOUT),
        (InterruptedError(), ErrorCodes.C11_E_CANCELED),
        (FileNotFoundError(), ErrorCodes.C11_E_FILENOTFOUND),
        (NotADirectoryError(), ErrorCodes.C11_E_DIRECTORYNOTFOUND),
        (EOFError(), ErrorCodes.C11_E_ENDOFSTREAM),
        (
            OSError(errno.ENAMETOOLONG, "path too long"),
            ErrorCodes.C11_E_PATHTOOLONG,
        ),
        (
            OSError(errno.ENOTDIR, "not a directory"),
            ErrorCodes.C11_E_DIRECTORYNOTFOUND,
        ),
    ]

    for exception, error_code in cases:
        assert exception_to_code(exception) == error_code.value


def test_python_error_codes_match_native_error_code_values():
    expected_values = range(-2147483648, -2147483630)
    assert [code.value for code in ErrorCodes] == list(expected_values)
