import ctypes
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
fn = dir_path + "/libGetLine.dll"
handle = ctypes.pydll.LoadLibrary(fn)

handle.get_line.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.py_object, ctypes.c_int]

def get_line(start: tuple, end: tuple, opacity_grid: list, height: int) -> bool:
    return handle.get_line(
        start[0], start[1], end[0], end[1],
        opacity_grid, height)

if __name__ == '__main__':
    import time
    grid = [False for _ in range(150)]
    start = time.time_ns() / 1e6
    for x in range(10000):
        out1 = bool(get_line((1, 1), (3, 3), grid, 10))
        out2 = bool(get_line((1, 1), (3, 5), grid, 10))
        out3 = bool(get_line((2, 1), (3, 5), grid, 10))
        out4 = bool(get_line((4, 7), (3, 1), grid, 10))
    end = time.time_ns() / 1e6
    print(end - start)

    print(out1, out2, out3, out4)
