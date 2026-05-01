import ctypes
import ctypes.wintypes
import threading

WM_POWERBROADCAST = 0x0218
PBT_APMSUSPEND = 0x0004
PBT_APMRESUMEAUTOMATIC = 0x0012

WNDPROCTYPE = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.wintypes.HWND,
    ctypes.c_uint,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROCTYPE),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.wintypes.HINSTANCE),
        ("hIcon", ctypes.wintypes.HICON),
        ("hCursor", ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HBRUSH),
        ("lpszMenuName", ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
    ]


class WindowsPowerMonitor:
    """Listens for Windows suspend/resume events via a message-only window."""

    def __init__(self, on_suspend, on_resume):
        self._on_suspend = on_suspend
        self._on_resume = on_resume
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hinstance = kernel32.GetModuleHandleW(None)
        classname = "TimeboxPowerMonitor"

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_POWERBROADCAST:
                if wparam == PBT_APMSUSPEND:
                    try:
                        self._on_suspend()
                    except Exception as e:
                        print(f"[PowerMonitor] on_suspend error: {e}")
                elif wparam == PBT_APMRESUMEAUTOMATIC:
                    try:
                        self._on_resume()
                    except Exception as e:
                        print(f"[PowerMonitor] on_resume error: {e}")
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        # Keep reference alive to prevent GC
        self._wnd_proc_ptr = WNDPROCTYPE(wnd_proc)

        wc = WNDCLASSW()
        wc.style = 0
        wc.lpfnWndProc = self._wnd_proc_ptr
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = hinstance
        wc.hIcon = None
        wc.hCursor = None
        wc.hbrBackground = None
        wc.lpszMenuName = None
        wc.lpszClassName = classname

        user32.RegisterClassW(ctypes.byref(wc))

        hwnd = user32.CreateWindowExW(
            0, classname, "PowerMonitor",
            0, 0, 0, 0, 0,
            -3,  # HWND_MESSAGE — message-only window, no desktop presence
            None, hinstance, None,
        )
        if not hwnd:
            print(f"[PowerMonitor] CreateWindowExW failed: {ctypes.GetLastError()}")
            return

        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
