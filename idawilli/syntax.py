from __future__ import annotations

from typing import TypeAlias

from rich.text import Text

COLOR_ON = 0x01
COLOR_OFF = 0x02
COLOR_ESC = 0x03
COLOR_INV = 0x04

COLOR_DEFAULT = 0x01
COLOR_REGCMT = 0x02
COLOR_RPTCMT = 0x03
COLOR_AUTOCMT = 0x04
COLOR_INSN = 0x05
COLOR_DATNAME = 0x06
COLOR_DNAME = 0x07
COLOR_DEMNAME = 0x08
COLOR_SYMBOL = 0x09
COLOR_CHAR = 0x0A
COLOR_STRING = 0x0B
COLOR_NUMBER = 0x0C
COLOR_VOIDOP = 0x0D
COLOR_CREF = 0x0E
COLOR_DREF = 0x0F
COLOR_CREFTAIL = 0x10
COLOR_DREFTAIL = 0x11
COLOR_ERROR = 0x12
COLOR_PREFIX = 0x13
COLOR_BINPREF = 0x14
COLOR_EXTRA = 0x15
COLOR_ALTOP = 0x16
COLOR_HIDNAME = 0x17
COLOR_LIBNAME = 0x18
COLOR_LOCNAME = 0x19
COLOR_CODNAME = 0x1A
COLOR_ASMDIR = 0x1B
COLOR_MACRO = 0x1C
COLOR_DSTR = 0x1D
COLOR_DCHAR = 0x1E
COLOR_DNUM = 0x1F
COLOR_KEYWORD = 0x20
COLOR_REG = 0x21
COLOR_IMPNAME = 0x22
COLOR_SEGNAME = 0x23
COLOR_UNKNAME = 0x24
COLOR_CNAME = 0x25
COLOR_UNAME = 0x26
COLOR_COLLAPSED = 0x27
COLOR_ADDR = 0x28
COLOR_OPND1 = 0x29
COLOR_OPND2 = 0x2A
COLOR_OPND3 = 0x2B
COLOR_OPND4 = 0x2C
COLOR_OPND5 = 0x2D
COLOR_OPND6 = 0x2E
COLOR_UTF8 = 0x32

Theme: TypeAlias = dict[int, str]

DEFAULT_THEME: Theme = {
    COLOR_DEFAULT: "",
    COLOR_REGCMT: "bright_black italic",
    COLOR_RPTCMT: "bright_black italic",
    COLOR_AUTOCMT: "bright_black italic",
    COLOR_INSN: "bold bright_blue",
    COLOR_DATNAME: "yellow",
    COLOR_DNAME: "yellow",
    COLOR_DEMNAME: "yellow",
    COLOR_SYMBOL: "",
    COLOR_CHAR: "green",
    COLOR_STRING: "green",
    COLOR_NUMBER: "bright_red",
    COLOR_VOIDOP: "bright_black",
    COLOR_CREF: "yellow",
    COLOR_DREF: "yellow",
    COLOR_CREFTAIL: "yellow",
    COLOR_DREFTAIL: "yellow",
    COLOR_ERROR: "bold red",
    COLOR_PREFIX: "bright_black",
    COLOR_BINPREF: "bright_black",
    COLOR_EXTRA: "bright_black",
    COLOR_ALTOP: "",
    COLOR_HIDNAME: "bright_black",
    COLOR_LIBNAME: "bright_cyan",
    COLOR_LOCNAME: "bright_white",
    COLOR_CODNAME: "yellow",
    COLOR_ASMDIR: "magenta",
    COLOR_MACRO: "magenta",
    COLOR_DSTR: "green",
    COLOR_DCHAR: "green",
    COLOR_DNUM: "bright_red",
    COLOR_KEYWORD: "magenta bold",
    COLOR_REG: "cyan",
    COLOR_IMPNAME: "bright_cyan",
    COLOR_SEGNAME: "magenta",
    COLOR_UNKNAME: "yellow",
    COLOR_CNAME: "yellow",
    COLOR_UNAME: "yellow",
    COLOR_COLLAPSED: "",
    COLOR_OPND1: "",
    COLOR_OPND2: "",
    COLOR_OPND3: "",
    COLOR_OPND4: "",
    COLOR_OPND5: "",
    COLOR_OPND6: "",
    COLOR_UTF8: "",
}


def render_tagged_line(
    tagged_line: str,
    *,
    theme: Theme | None = None,
    addr_width: int = 16,
) -> Text:
    """Convert an IDA tagged line to a rich Text object with syntax highlighting.

    Raises:
        ValueError: If addr_width is not 8 or 16.
    """
    if addr_width not in (8, 16):
        raise ValueError(f"addr_width must be 8 or 16, got {addr_width}")

    if theme is None:
        theme = DEFAULT_THEME

    text = Text()
    style_stack: list[str] = []
    buf: list[str] = []
    cur_style = ""
    i = 0
    n = len(tagged_line)

    def _flush() -> None:
        nonlocal buf
        if buf:
            text.append("".join(buf), style=cur_style)
            buf = []

    while i < n:
        ch = ord(tagged_line[i])

        if ch == COLOR_ON:
            if i + 1 >= n:
                break
            tag = ord(tagged_line[i + 1])
            i += 2
            if tag == COLOR_ADDR:
                i += min(addr_width, n - i)
            else:
                _flush()
                style_stack.append(theme.get(tag, ""))
                cur_style = style_stack[-1]
        elif ch == COLOR_OFF:
            if i + 1 >= n:
                break
            i += 2
            _flush()
            if style_stack:
                style_stack.pop()
            cur_style = style_stack[-1] if style_stack else ""
        elif ch == COLOR_ESC:
            if i + 1 >= n:
                break
            buf.append(tagged_line[i + 1])
            i += 2
        elif ch == COLOR_INV:
            i += 1
        else:
            buf.append(tagged_line[i])
            i += 1

    _flush()
    return text


def strip_tags(
    tagged_line: str,
    *,
    addr_width: int = 16,
) -> str:
    """Remove all IDA color tags, returning only the visible text.

    Raises:
        ValueError: If addr_width is not 8 or 16.
    """
    if addr_width not in (8, 16):
        raise ValueError(f"addr_width must be 8 or 16, got {addr_width}")

    parts: list[str] = []
    i = 0
    n = len(tagged_line)

    while i < n:
        ch = ord(tagged_line[i])

        if ch == COLOR_ON:
            if i + 1 >= n:
                break
            tag = ord(tagged_line[i + 1])
            i += 2
            if tag == COLOR_ADDR:
                i += min(addr_width, n - i)
        elif ch == COLOR_OFF:
            if i + 1 >= n:
                break
            i += 2
        elif ch == COLOR_ESC:
            if i + 1 >= n:
                break
            parts.append(tagged_line[i + 1])
            i += 2
        elif ch == COLOR_INV:
            i += 1
        else:
            parts.append(tagged_line[i])
            i += 1

    return "".join(parts)
