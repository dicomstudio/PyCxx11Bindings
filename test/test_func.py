import ctypes
import errno
import io
import os

from cxx11bindings import ErrorCodes, PyC11Stream, exception_to_code


def test_c11_callbacks_delegate_stream_operations():
    inner_stream = io.BytesIO(b"abcdef")
    stream = PyC11Stream(inner_stream)
    callbacks = stream._c11_stream
    read_buffer = (ctypes.c_uint8 * 3)()

    assert callbacks.read(None, read_buffer, len(read_buffer)) == 3
    assert bytes(read_buffer) == b"abc"
    assert callbacks.seek(None, 1, io.SEEK_SET) == 1

    data = b"XY"
    write_buffer = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    assert callbacks.write(None, write_buffer, len(data)) == len(data)
    assert callbacks.flush(None) == 0
    assert callbacks.trunc(None, 4) == 4
    assert inner_stream.getvalue() == b"aXYd"


def test_c11_callbacks_translate_stream_exceptions():
    class FailingStream:
        def read(self, _):
            raise TypeError("unexpected stream error")

        def write(self, _):
            raise io.UnsupportedOperation("write is not supported")

        def seek(self, *_):
            raise ValueError("invalid seek")

        def flush(self):
            raise OSError(errno.EIO, "flush failed")

        def truncate(self, _):
            raise PermissionError("truncate is not permitted")

        def close(self):
            pass

    callbacks = PyC11Stream(FailingStream())._c11_stream
    read_buffer = (ctypes.c_uint8 * 1)()
    write_buffer = (ctypes.c_uint8 * 1)()

    assert callbacks.read(None, read_buffer, 1) == ErrorCodes.C11_E_UNMAPPED.value
    assert callbacks.write(None, write_buffer, 1) == ErrorCodes.C11_E_NOTSUPPORTED.value
    assert callbacks.seek(None, 0, io.SEEK_SET) == ErrorCodes.C11_E_INVALIDARG.value
    assert callbacks.flush(None) == ErrorCodes.C11_E_IO.value
    assert callbacks.trunc(None, 1) == ErrorCodes.C11_E_UNAUTHORIZED.value


def test_py_c11_stream_methods_delegate_to_inner_stream():
    inner_stream = io.BytesIO(b"data")
    stream = PyC11Stream(inner_stream)

    assert stream.read(2) == b"da"
    assert stream.seek(0) == 0
    assert stream.write(b"XY") == 2
    assert stream.truncate(2) == 2
    assert inner_stream.getvalue() == b"XY"
    assert stream.readable()
    assert stream.writable()
    assert stream.seekable()
    assert stream.flush() is None

    stream.close()
    assert inner_stream.closed
    assert stream.closed


def test_context_manager_closes_wrapper_and_inner_stream():
    inner_stream = io.BytesIO(b"data")
    stream = PyC11Stream(inner_stream)

    with stream as entered_stream:
        assert entered_stream is stream
        assert not stream.closed

    assert stream.closed
    assert inner_stream.closed


def test_context_manager_does_not_suppress_exceptions():
    inner_stream = io.BytesIO()
    stream = PyC11Stream(inner_stream)

    try:
        with stream:
            raise RuntimeError("operation failed")
    except RuntimeError as error:
        assert str(error) == "operation failed"
    else:
        raise AssertionError("context manager suppressed the exception")

    assert stream.closed
    assert inner_stream.closed


def test_context_manager_rejects_reentering_closed_stream():
    stream = PyC11Stream(io.BytesIO())
    stream.close()

    try:
        with stream:
            pass
    except ValueError:
        pass
    else:
        raise AssertionError("closed stream was allowed to re-enter")


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
