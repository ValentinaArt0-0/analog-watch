"""
Analog clock - pure Python.

Only ONE import: ctypes (needed to talk to the operating system window API).
  - sin/cos are implemented by hand (Taylor series).
  - The current time comes straight from the Windows API (GetLocalTime).
  - The window and all the drawing use Win32 (user32 / gdi32) directly.

Run:  python analog_clock.py      (Windows)
"""
import ctypes

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
WIDTH = 460
HEIGHT = 520
CENTER_X = WIDTH // 2
CENTER_Y = 240
RADIUS = 190

BACKGROUND = "#0f111a"
FACE = "#171a29"
BORDER = "#7c5cff"
NEON = "#00e5ff"
HOUR_COLOR = "#f5f5f7"
MINUTE_COLOR = "#b8c0ff"
SECOND_COLOR = "#ff4d8d"
TEXT_COLOR = "#8b90a8"

DAYS = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun",
          "jul", "ago", "sep", "oct", "nov", "dic"]

PI = 3.141592653589793


# ----------------------------------------------------------------------------
# Hand-made math (so we do not need the "math" module)
# ----------------------------------------------------------------------------
def sin(x):
    """Sine using a Taylor series after reducing x to [-PI, PI]."""
    x = x - int(x / (2 * PI)) * 2 * PI
    if x > PI:
        x -= 2 * PI
    elif x < -PI:
        x += 2 * PI
    term = x
    total = x
    for n in range(1, 11):
        term *= -x * x / ((2 * n) * (2 * n + 1))
        total += term
    return total


def cos(x):
    return sin(x + PI / 2)


def point_on_circle(angle_deg, length):
    """Point at 'length' from the center. 0 degrees = top, clockwise."""
    a = (angle_deg - 90) * PI / 180
    return CENTER_X + length * cos(a), CENTER_Y + length * sin(a)


def rgb(hex_color):
    """'#rrggbb' -> Windows COLORREF (0x00BBGGRR)."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return r | (g << 8) | (b << 16)


# ----------------------------------------------------------------------------
# WINDOWS API LAYER
# ----------------------------------------------------------------------------
if not hasattr(ctypes, "WinDLL"):
    raise SystemExit("This version of the clock uses the Win32 API and only runs on Windows.")

user32 = ctypes.WinDLL("user32")
gdi32 = ctypes.WinDLL("gdi32")
kernel32 = ctypes.WinDLL("kernel32")

c_void = ctypes.c_void_p
c_int = ctypes.c_int
c_uint = ctypes.c_uint
c_long = ctypes.c_long
c_wstr = ctypes.c_wchar_p
c_size = ctypes.c_size_t
c_ssize = ctypes.c_ssize_t

WNDPROC = ctypes.WINFUNCTYPE(c_ssize, c_void, c_uint, c_size, c_ssize)


class RECT(ctypes.Structure):
    _fields_ = [("left", c_long), ("top", c_long),
                ("right", c_long), ("bottom", c_long)]


class POINT(ctypes.Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", c_void), ("message", c_uint),
                ("wParam", c_size), ("lParam", c_ssize),
                ("time", ctypes.c_uint32), ("pt", POINT)]


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [("hdc", c_void), ("fErase", c_int), ("rcPaint", RECT),
                ("fRestore", c_int), ("fIncUpdate", c_int),
                ("rgbReserved", ctypes.c_byte * 32)]


class SYSTEMTIME(ctypes.Structure):
    _fields_ = [("year", ctypes.c_ushort), ("month", ctypes.c_ushort),
                ("weekday", ctypes.c_ushort), ("day", ctypes.c_ushort),
                ("hour", ctypes.c_ushort), ("minute", ctypes.c_ushort),
                ("second", ctypes.c_ushort), ("millisecond", ctypes.c_ushort)]


class WNDCLASS(ctypes.Structure):
    _fields_ = [("style", c_uint), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", c_int), ("cbWndExtra", c_int),
                ("hInstance", c_void), ("hIcon", c_void),
                ("hCursor", c_void), ("hbrBackground", c_void),
                ("lpszMenuName", c_wstr), ("lpszClassName", c_wstr)]


def bind(function, restype, *argtypes):
    function.restype = restype
    function.argtypes = list(argtypes)


bind(user32.DefWindowProcW, c_ssize, c_void, c_uint, c_size, c_ssize)
bind(user32.RegisterClassW, ctypes.c_ushort, ctypes.POINTER(WNDCLASS))
bind(user32.CreateWindowExW, c_void, ctypes.c_uint32, c_wstr, c_wstr, ctypes.c_uint32,
     c_int, c_int, c_int, c_int, c_void, c_void, c_void, c_void)
bind(user32.AdjustWindowRect, c_int, ctypes.POINTER(RECT), ctypes.c_uint32, c_int)
bind(user32.GetSystemMetrics, c_int, c_int)
bind(user32.ShowWindow, c_int, c_void, c_int)
bind(user32.UpdateWindow, c_int, c_void)
bind(user32.SetTimer, c_size, c_void, c_size, c_uint, c_void)
bind(user32.InvalidateRect, c_int, c_void, c_void, c_int)
bind(user32.BeginPaint, c_void, c_void, ctypes.POINTER(PAINTSTRUCT))
bind(user32.EndPaint, c_int, c_void, ctypes.POINTER(PAINTSTRUCT))
bind(user32.FillRect, c_int, c_void, ctypes.POINTER(RECT), c_void)
bind(user32.DrawTextW, c_int, c_void, c_wstr, c_int, ctypes.POINTER(RECT), c_uint)
bind(user32.GetMessageW, c_int, ctypes.POINTER(MSG), c_void, c_uint, c_uint)
bind(user32.TranslateMessage, c_int, ctypes.POINTER(MSG))
bind(user32.DispatchMessageW, c_ssize, ctypes.POINTER(MSG))
bind(user32.PostQuitMessage, None, c_int)
bind(user32.LoadCursorW, c_void, c_void, c_void)
bind(user32.SetProcessDPIAware, c_int)

bind(gdi32.CreateCompatibleDC, c_void, c_void)
bind(gdi32.CreateCompatibleBitmap, c_void, c_void, c_int, c_int)
bind(gdi32.SelectObject, c_void, c_void, c_void)
bind(gdi32.DeleteObject, c_int, c_void)
bind(gdi32.DeleteDC, c_int, c_void)
bind(gdi32.BitBlt, c_int, c_void, c_int, c_int, c_int, c_int, c_void, c_int, c_int, ctypes.c_uint32)
bind(gdi32.CreatePen, c_void, c_int, c_int, ctypes.c_uint32)
bind(gdi32.CreateSolidBrush, c_void, ctypes.c_uint32)
bind(gdi32.GetStockObject, c_void, c_int)
bind(gdi32.MoveToEx, c_int, c_void, c_int, c_int, c_void)
bind(gdi32.LineTo, c_int, c_void, c_int, c_int)
bind(gdi32.Ellipse, c_int, c_void, c_int, c_int, c_int, c_int)
bind(gdi32.SetBkMode, c_int, c_void, c_int)
bind(gdi32.SetTextColor, ctypes.c_uint32, c_void, ctypes.c_uint32)
bind(gdi32.CreateFontW, c_void, *([c_int] * 13), c_wstr)

bind(kernel32.GetModuleHandleW, c_void, c_wstr)
bind(kernel32.GetLocalTime, None, ctypes.POINTER(SYSTEMTIME))

# Win32 constants
WM_DESTROY = 0x0002
WM_PAINT = 0x000F
WM_ERASEBKGND = 0x0014
WM_TIMER = 0x0113
WINDOW_STYLE = 0x00CA0000        # caption + system menu + minimize box (not resizable)
SRCCOPY = 0x00CC0020
NULL_BRUSH = 5
NULL_PEN = 8
DT_CENTER_VCENTER_SINGLE = 0x0001 | 0x0004 | 0x0020

# Caches so GDI objects are created once, not on every frame
pens = {}
brushes = {}
fonts = {}


# ----------------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------------
def get_pen(color, width):
    key = (color, width)
    if key not in pens:
        pens[key] = gdi32.CreatePen(0, width, rgb(color))
    return pens[key]


def get_brush(color):
    if color not in brushes:
        brushes[color] = gdi32.CreateSolidBrush(rgb(color))
    return brushes[color]


def get_font(name, height, weight):
    key = (name, height, weight)
    if key not in fonts:
        fonts[key] = gdi32.CreateFontW(-height, 0, 0, 0, weight, 0, 0, 0,
                                       1, 0, 0, 4, 0, name)
    return fonts[key]


def draw_line(hdc, x1, y1, x2, y2, color, width):
    gdi32.SelectObject(hdc, get_pen(color, width))
    gdi32.MoveToEx(hdc, round(x1), round(y1), None)
    gdi32.LineTo(hdc, round(x2), round(y2))


def draw_circle(hdc, x, y, radius, fill=None, outline=None, width=1):
    brush = get_brush(fill) if fill else gdi32.GetStockObject(NULL_BRUSH)
    pen = get_pen(outline, width) if outline else gdi32.GetStockObject(NULL_PEN)
    gdi32.SelectObject(hdc, brush)
    gdi32.SelectObject(hdc, pen)
    gdi32.Ellipse(hdc, round(x - radius), round(y - radius),
                  round(x + radius), round(y + radius))


def draw_text(hdc, x, y, text, color, font_name, size, bold=False):
    gdi32.SelectObject(hdc, get_font(font_name, size, 700 if bold else 400))
    gdi32.SetTextColor(hdc, rgb(color))
    box = RECT(round(x - 150), round(y - 20), round(x + 150), round(y + 20))
    user32.DrawTextW(hdc, text, -1, ctypes.byref(box), DT_CENTER_VCENTER_SINGLE)


def draw_hand(hdc, angle, length, width, color, tail=0):
    x2, y2 = point_on_circle(angle, length)
    x1, y1 = point_on_circle(angle + 180, tail)
    draw_line(hdc, x1, y1, x2, y2, color, width)


# ----------------------------------------------------------------------------
# Clock rendering
# ----------------------------------------------------------------------------
def draw_clock_face(hdc):
    # Outer glow rings
    for i in range(6):
        g = RADIUS + 22 - i * 3
        draw_circle(hdc, CENTER_X, CENTER_Y, g, outline=BORDER, width=1)

    # Border + face
    draw_circle(hdc, CENTER_X, CENTER_Y, RADIUS + 8, fill=BORDER)
    draw_circle(hdc, CENTER_X, CENTER_Y, RADIUS, fill=FACE)

    # Tick marks
    for i in range(60):
        angle = i * 6
        if i % 5 == 0:
            x1, y1 = point_on_circle(angle, RADIUS - 22)
            x2, y2 = point_on_circle(angle, RADIUS - 6)
            draw_line(hdc, x1, y1, x2, y2, NEON, 4)
        else:
            x1, y1 = point_on_circle(angle, RADIUS - 12)
            x2, y2 = point_on_circle(angle, RADIUS - 6)
            draw_line(hdc, x1, y1, x2, y2, TEXT_COLOR, 1)

    # Hour numbers
    for n in range(1, 13):
        x, y = point_on_circle(n * 30, RADIUS - 48)
        draw_text(hdc, x, y, str(n), HOUR_COLOR, "Segoe UI", 24, bold=True)

    draw_text(hdc, CENTER_X, CENTER_Y - 85, "PY·CLOCK", TEXT_COLOR, "Segoe UI", 12, bold=True)


def draw_clock_hands(hdc):
    now = SYSTEMTIME()
    kernel32.GetLocalTime(ctypes.byref(now))

    seconds = now.second + now.millisecond / 1000   # smooth second hand
    minutes = now.minute + seconds / 60
    hours = (now.hour % 12) + minutes / 60

    draw_hand(hdc, hours * 30, 105, 8, HOUR_COLOR)
    draw_hand(hdc, minutes * 6, 150, 5, MINUTE_COLOR)
    draw_hand(hdc, seconds * 6, 165, 2, SECOND_COLOR, tail=30)

    # Center caps
    draw_circle(hdc, CENTER_X, CENTER_Y, 10, fill=SECOND_COLOR)
    draw_circle(hdc, CENTER_X, CENTER_Y, 4, fill=BACKGROUND)

    # Digital time and date
    digital = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
    date = f"{DAYS[now.weekday]}, {now.day} {MONTHS[now.month - 1]} {now.year}"
    draw_text(hdc, CENTER_X, 445, digital, NEON, "Consolas", 29, bold=True)
    draw_text(hdc, CENTER_X, 475, date, TEXT_COLOR, "Segoe UI", 16)


def paint(hwnd):
    ps = PAINTSTRUCT()
    hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

    # Double buffering: draw off-screen, then copy in one go (no flicker)
    memory_dc = gdi32.CreateCompatibleDC(hdc)
    bitmap = gdi32.CreateCompatibleBitmap(hdc, WIDTH, HEIGHT)
    old_bitmap = gdi32.SelectObject(memory_dc, bitmap)

    gdi32.SetBkMode(memory_dc, 1)  # transparent text background
    full = RECT(0, 0, WIDTH, HEIGHT)
    user32.FillRect(memory_dc, ctypes.byref(full), get_brush(BACKGROUND))

    draw_clock_face(memory_dc)
    draw_clock_hands(memory_dc)

    gdi32.BitBlt(hdc, 0, 0, WIDTH, HEIGHT, memory_dc, 0, 0, SRCCOPY)

    gdi32.SelectObject(memory_dc, old_bitmap)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(memory_dc)
    user32.EndPaint(hwnd, ctypes.byref(ps))


# ----------------------------------------------------------------------------
# Window procedure + main loop
# ----------------------------------------------------------------------------
def window_proc(hwnd, message, wparam, lparam):
    if message == WM_PAINT:
        paint(hwnd)
        return 0
    if message == WM_TIMER:
        user32.InvalidateRect(hwnd, None, 0)
        return 0
    if message == WM_ERASEBKGND:
        return 1
    if message == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, message, wparam, lparam)


callback = WNDPROC(window_proc)  # keep a reference so it is not garbage collected


def main():
    user32.SetProcessDPIAware()
    instance = kernel32.GetModuleHandleW(None)

    window_class = WNDCLASS()
    window_class.lpfnWndProc = callback
    window_class.hInstance = instance
    window_class.hCursor = user32.LoadCursorW(None, 32512)  # standard arrow
    window_class.hbrBackground = get_brush(BACKGROUND)
    window_class.lpszClassName = "PyAnalogClock"
    user32.RegisterClassW(ctypes.byref(window_class))

    # Make the *client area* exactly WIDTH x HEIGHT, and center the window
    frame = RECT(0, 0, WIDTH, HEIGHT)
    user32.AdjustWindowRect(ctypes.byref(frame), WINDOW_STYLE, 0)
    win_w = frame.right - frame.left
    win_h = frame.bottom - frame.top
    pos_x = (user32.GetSystemMetrics(0) - win_w) // 2
    pos_y = (user32.GetSystemMetrics(1) - win_h) // 2

    hwnd = user32.CreateWindowExW(0, "PyAnalogClock", "Reloj", WINDOW_STYLE,
                                  pos_x, pos_y, win_w, win_h,
                                  None, None, instance, None)

    user32.SetTimer(hwnd, 1, 16, None)  # ~60 redraws per second
    user32.ShowWindow(hwnd, 5)
    user32.UpdateWindow(hwnd)

    message = MSG()
    while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(message))
        user32.DispatchMessageW(ctypes.byref(message))


if __name__ == "__main__":
    main()
