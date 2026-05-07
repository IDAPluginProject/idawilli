from __future__ import annotations

import pytest

from idawilli.syntax import (
    COLOR_ADDR,
    COLOR_AUTOCMT,
    COLOR_BINPREF,
    COLOR_DEMNAME,
    COLOR_HIDNAME,
    COLOR_INSN,
    COLOR_KEYWORD,
    COLOR_LIBNAME,
    COLOR_NUMBER,
    COLOR_OPND1,
    COLOR_PREFIX,
    COLOR_REG,
    COLOR_REGCMT,
    COLOR_STRING,
    COLOR_SYMBOL,
    DEFAULT_THEME,
    render_tagged_line,
    strip_tags,
)

ON = "\x01"
OFF = "\x02"
ESC = "\x03"
INV = "\x04"


def _tag(color: int, text: str) -> str:
    return ON + chr(color) + text + OFF + chr(color)


def _on(color: int) -> str:
    return ON + chr(color)


def _off(color: int) -> str:
    return OFF + chr(color)


def _addr64(hex_addr: str = "0000000000401000") -> str:
    assert len(hex_addr) == 16
    return ON + chr(COLOR_ADDR) + hex_addr


def _addr32(hex_addr: str = "00401000") -> str:
    assert len(hex_addr) == 8
    return ON + chr(COLOR_ADDR) + hex_addr


def _get_spans(result: object) -> list[tuple[str, str]]:
    plain = result.plain  # type: ignore[attr-defined]
    return [(plain[s.start : s.end], str(s.style)) for s in result._spans]  # type: ignore[attr-defined]


REALISTIC_HEX = (
    "0113 3130 3035 3633 3033 0213 2001 0c30"
    "3038 2002 0c01 1436 4120 3532 2002 1420"
    "2020 2020 2020 2020 2020 2020 2020 2020"
    "2001 0570 7573 6802 0520 2020 2001 2901"
    "0c35 3268 020c 0229"
)
REALISTIC_LINE = bytes.fromhex(REALISTIC_HEX).decode("latin-1")
REALISTIC_PLAIN = "10056303 008 6A 52                   push    52h"

# Pseudocode tagged lines captured from Hex-Rays decompiler output.
# These use the same tag format as disassembly but with different color codes:
#   COLOR_HIDNAME (0x17) — function signature, type casts
#   COLOR_KEYWORD (0x20) — C keywords (if, return) and numeric literals
#   COLOR_LIBNAME (0x18) — local variable names and register annotations
#   COLOR_DEMNAME (0x08) — called function names
#   COLOR_SYMBOL  (0x09) — punctuation (parens, semicolons, operators)
#   COLOR_REG     (0x21) — variable declarations
#   COLOR_ADDR    (0x28) — ctree item anchors (consumed silently)

# "int __cdecl sub_401040(unsigned int a1, int a2, int a3)"
PSEUDO_SIGNATURE_HEX = (
    "0117 696e 7420 5f5f 6364 6563 6c20 7375"
    "625f 3430 3130 3430 0109 2802 0975 6e73"
    "6967 6e65 6420 696e 7420 6131 2c20 696e"
    "7420 6132 2c20 696e 7420 6133 0109 2902"
    "0902 17"
)
PSEUDO_SIGNATURE_LINE = bytes.fromhex(PSEUDO_SIGNATURE_HEX).decode("latin-1")
PSEUDO_SIGNATURE_PLAIN = "int __cdecl sub_401040(unsigned int a1, int a2, int a3)"

# "  int result; // eax"
PSEUDO_DECL_HEX = (
    "2020 0128 3030 3030 3030 3030 3430 3030"
    "3030 3033 0121 696e 7420 7265 7375 6c74"
    "0221 0109 3b02 0920 0118 2f2f 2065 6178"
    "0218"
)
PSEUDO_DECL_LINE = bytes.fromhex(PSEUDO_DECL_HEX).decode("latin-1")
PSEUDO_DECL_PLAIN = "  int result; // eax"

# "  if ( result )"
PSEUDO_IF_HEX = (
    "0128 3030 3030 3030 3030 3030 3030 3030"
    "3038 2020 0120 6966 0220 2001 0928 0209"
    "2001 2830 3030 3030 3030 3030 3030 3030"
    "3031 4101 1872 6573 756c 7402 1820 0109"
    "2902 0901 2830 3030 3030 3030 3030 3030"
    "3030 3030 38"
)
PSEUDO_IF_LINE = bytes.fromhex(PSEUDO_IF_HEX).decode("latin-1")
PSEUDO_IF_PLAIN = "  if ( result )"

# "  return result;"
PSEUDO_RETURN_HEX = (
    "0128 3030 3030 3030 3030 3030 3030 3030"
    "3142 2020 0120 7265 7475 726e 0220 2001"
    "2830 3030 3030 3030 3030 3030 3030 3031"
    "4301 1872 6573 756c 7402 1801 093b 0209"
    "0128 3030 3030 3030 3030 3030 3030 3030"
    "3142"
)
PSEUDO_RETURN_LINE = bytes.fromhex(PSEUDO_RETURN_HEX).decode("latin-1")
PSEUDO_RETURN_PLAIN = "  return result;"

# "  result = sub_401000(a1, a2);"
PSEUDO_CALL_HEX = (
    "0128 3030 3030 3030 3030 3030 3030 3030"
    "3030 0128 3030 3030 3030 3030 3030 3030"
    "3030 3031 2020 0128 3030 3030 3030 3030"
    "3030 3030 3030 3033 0118 7265 7375 6c74"
    "0218 2001 2830 3030 3030 3030 3030 3030"
    "3030 3030 3201 093d 0209 2001 2830 3030"
    "3030 3030 3030 3030 3030 3030 3501 0873"
    "7562 5f34 3031 3030 3002 0801 2830 3030"
    "3030 3030 3030 3030 3030 3030 3401 0928"
    "0209 0128 3030 3030 3030 3030 3030 3030"
    "3030 3036 0118 6131 0218 0109 2c02 0920"
    "0128 3030 3030 3030 3030 3030 3030 3030"
    "3037 0118 6132 0218 0109 2902 0901 093b"
    "0209 0128 3030 3030 3030 3030 3030 3030"
    "3030 3031"
)
PSEUDO_CALL_LINE = bytes.fromhex(PSEUDO_CALL_HEX).decode("latin-1")
PSEUDO_CALL_PLAIN = "  result = sub_401000(a1, a2);"


# --- render_tagged_line tests ---


def test_render_plain_text() -> None:
    result = render_tagged_line("push    eax")
    assert result.plain == "push    eax"


def test_render_single_tag_pair() -> None:
    line = _tag(COLOR_INSN, "push")
    result = render_tagged_line(line)
    assert result.plain == "push"
    assert ("push", DEFAULT_THEME[COLOR_INSN]) in _get_spans(result)


def test_render_multiple_sequential_tags() -> None:
    line = (
        _tag(COLOR_INSN, "mov")
        + "    "
        + _tag(COLOR_REG, "eax")
        + ", "
        + _tag(COLOR_NUMBER, "42h")
    )
    result = render_tagged_line(line)
    assert result.plain == "mov    eax, 42h"
    spans = _get_spans(result)
    assert ("mov", DEFAULT_THEME[COLOR_INSN]) in spans
    assert ("eax", DEFAULT_THEME[COLOR_REG]) in spans
    assert ("42h", DEFAULT_THEME[COLOR_NUMBER]) in spans


def test_render_nested_tags() -> None:
    line = _on(COLOR_OPND1) + _tag(COLOR_NUMBER, "52h") + _off(COLOR_OPND1)
    result = render_tagged_line(line)
    assert result.plain == "52h"
    assert ("52h", DEFAULT_THEME[COLOR_NUMBER]) in _get_spans(result)


def test_render_nested_tags_with_outer_text() -> None:
    line = (
        _on(COLOR_OPND1)
        + "["
        + _tag(COLOR_REG, "eax")
        + "+"
        + _tag(COLOR_NUMBER, "10h")
        + "]"
        + _off(COLOR_OPND1)
    )
    result = render_tagged_line(line)
    assert result.plain == "[eax+10h]"
    spans = _get_spans(result)
    assert ("eax", DEFAULT_THEME[COLOR_REG]) in spans
    assert ("10h", DEFAULT_THEME[COLOR_NUMBER]) in spans


def test_render_color_addr_64bit() -> None:
    line = _addr64() + "visible_text"
    result = render_tagged_line(line)
    assert result.plain == "visible_text"


def test_render_color_addr_32bit() -> None:
    line = _addr32() + "visible_text"
    result = render_tagged_line(line, addr_width=8)
    assert result.plain == "visible_text"


def test_render_color_esc() -> None:
    line = "before" + ESC + "\x01" + "after"
    result = render_tagged_line(line)
    assert result.plain == "before\x01after"


def test_render_color_inv() -> None:
    line = "before" + INV + "after"
    result = render_tagged_line(line)
    assert result.plain == "beforeafter"


def test_render_empty_input() -> None:
    result = render_tagged_line("")
    assert result.plain == ""


def test_render_custom_theme() -> None:
    line = _tag(COLOR_INSN, "nop")
    result = render_tagged_line(line, theme={COLOR_INSN: "bold green"})
    assert result.plain == "nop"
    assert ("nop", "bold green") in _get_spans(result)


def test_render_realistic_line() -> None:
    result = render_tagged_line(REALISTIC_LINE)
    assert result.plain == REALISTIC_PLAIN
    spans = _get_spans(result)
    assert ("10056303", DEFAULT_THEME[COLOR_PREFIX]) in spans
    assert ("push", DEFAULT_THEME[COLOR_INSN]) in spans
    assert ("52h", DEFAULT_THEME[COLOR_NUMBER]) in spans


def test_render_unmapped_color_code() -> None:
    line = _tag(0xFF, "mystery")
    result = render_tagged_line(line)
    assert result.plain == "mystery"


def test_render_addr_between_tags() -> None:
    line = _tag(COLOR_PREFIX, "addr") + _addr64() + " " + _tag(COLOR_INSN, "push")
    result = render_tagged_line(line)
    assert result.plain == "addr push"


def test_render_consecutive_addr_tags() -> None:
    line = _addr64("0000000000401000") + _addr64("0000000000401004") + "text"
    result = render_tagged_line(line)
    assert result.plain == "text"


def test_render_mismatched_off_tag() -> None:
    line = _on(COLOR_INSN) + "push" + _off(COLOR_NUMBER)
    result = render_tagged_line(line)
    assert result.plain == "push"
    assert ("push", DEFAULT_THEME[COLOR_INSN]) in _get_spans(result)


def test_render_extra_off_without_on() -> None:
    line = _off(COLOR_INSN) + "text"
    result = render_tagged_line(line)
    assert result.plain == "text"


def test_render_comment_styling() -> None:
    line = _tag(COLOR_REGCMT, "; this is a comment")
    result = render_tagged_line(line)
    assert result.plain == "; this is a comment"
    assert ("; this is a comment", DEFAULT_THEME[COLOR_REGCMT]) in _get_spans(result)


def test_render_truncated_color_on() -> None:
    result = render_tagged_line("text" + ON)
    assert result.plain == "text"


def test_render_truncated_color_off() -> None:
    result = render_tagged_line("text" + OFF)
    assert result.plain == "text"


def test_render_truncated_color_esc() -> None:
    result = render_tagged_line("text" + ESC)
    assert result.plain == "text"


def test_render_truncated_addr_payload() -> None:
    line = ON + chr(COLOR_ADDR) + "00004010"
    result = render_tagged_line(line)
    assert result.plain == ""


def test_render_unicode_visible_text() -> None:
    line = _tag(COLOR_STRING, '"Ünïcödé"')
    result = render_tagged_line(line)
    assert result.plain == '"Ünïcödé"'


def test_render_addr_then_immediate_tag() -> None:
    line = _addr64() + _tag(COLOR_INSN, "push")
    result = render_tagged_line(line)
    assert result.plain == "push"
    assert ("push", DEFAULT_THEME[COLOR_INSN]) in _get_spans(result)


def test_render_empty_tag_pair() -> None:
    line = _on(COLOR_INSN) + _off(COLOR_INSN) + "text"
    result = render_tagged_line(line)
    assert result.plain == "text"


def test_render_triple_nesting() -> None:
    line = (
        _on(COLOR_OPND1)
        + _on(COLOR_REG)
        + _on(COLOR_SYMBOL)
        + "+"
        + _off(COLOR_SYMBOL)
        + _off(COLOR_REG)
        + _off(COLOR_OPND1)
    )
    result = render_tagged_line(line)
    assert result.plain == "+"


def test_render_esc_inside_styled_region() -> None:
    line = _on(COLOR_STRING) + "str" + ESC + "\x01" + "ing" + _off(COLOR_STRING)
    result = render_tagged_line(line)
    assert result.plain == "str\x01ing"


def test_render_esc_all_sentinel_bytes() -> None:
    line = ESC + "\x01" + ESC + "\x02" + ESC + "\x03" + ESC + "\x04"
    result = render_tagged_line(line)
    assert result.plain == "\x01\x02\x03\x04"


def test_render_multiple_inv() -> None:
    line = INV + "a" + INV + "b" + INV
    result = render_tagged_line(line)
    assert result.plain == "ab"


def test_render_only_tags_no_text() -> None:
    line = _on(COLOR_INSN) + _off(COLOR_INSN)
    result = render_tagged_line(line)
    assert result.plain == ""


def test_render_autocmt_not_confused_with_inv() -> None:
    line = _tag(COLOR_AUTOCMT, "; auto comment")
    result = render_tagged_line(line)
    assert result.plain == "; auto comment"
    assert ("; auto comment", DEFAULT_THEME[COLOR_AUTOCMT]) in _get_spans(result)


def test_render_text_before_and_after_addr() -> None:
    line = "prefix" + _addr64() + "suffix"
    result = render_tagged_line(line)
    assert result.plain == "prefixsuffix"


def test_render_nested_visible_outer_style() -> None:
    line = _on(COLOR_INSN) + "mov " + _tag(COLOR_REG, "eax") + ", 0" + _off(COLOR_INSN)
    result = render_tagged_line(line)
    assert result.plain == "mov eax, 0"
    spans = _get_spans(result)
    assert ("mov ", DEFAULT_THEME[COLOR_INSN]) in spans
    assert ("eax", DEFAULT_THEME[COLOR_REG]) in spans
    assert (", 0", DEFAULT_THEME[COLOR_INSN]) in spans


def test_render_addr_width_mismatch() -> None:
    line = ON + chr(COLOR_ADDR) + "0000000000401000" + "visible"
    result = render_tagged_line(line, addr_width=8)
    assert result.plain == "00401000visible"


def test_render_invalid_addr_width() -> None:
    with pytest.raises(ValueError, match="addr_width must be 8 or 16"):
        render_tagged_line("", addr_width=4)


# --- pseudocode render tests (real Hex-Rays decompiler output) ---


def test_render_pseudocode_signature() -> None:
    result = render_tagged_line(PSEUDO_SIGNATURE_LINE)
    assert result.plain == PSEUDO_SIGNATURE_PLAIN
    spans = _get_spans(result)
    assert ("int __cdecl sub_401040", DEFAULT_THEME[COLOR_HIDNAME]) in spans
    assert (
        "unsigned int a1, int a2, int a3",
        DEFAULT_THEME[COLOR_HIDNAME],
    ) in spans


def test_render_pseudocode_declaration() -> None:
    result = render_tagged_line(PSEUDO_DECL_LINE)
    assert result.plain == PSEUDO_DECL_PLAIN
    spans = _get_spans(result)
    assert ("int result", DEFAULT_THEME[COLOR_REG]) in spans
    assert ("// eax", DEFAULT_THEME[COLOR_LIBNAME]) in spans


def test_render_pseudocode_if() -> None:
    result = render_tagged_line(PSEUDO_IF_LINE)
    assert result.plain == PSEUDO_IF_PLAIN
    spans = _get_spans(result)
    assert ("if", DEFAULT_THEME[COLOR_KEYWORD]) in spans
    assert ("result", DEFAULT_THEME[COLOR_LIBNAME]) in spans


def test_render_pseudocode_return() -> None:
    result = render_tagged_line(PSEUDO_RETURN_LINE)
    assert result.plain == PSEUDO_RETURN_PLAIN
    spans = _get_spans(result)
    assert ("return", DEFAULT_THEME[COLOR_KEYWORD]) in spans
    assert ("result", DEFAULT_THEME[COLOR_LIBNAME]) in spans


def test_render_pseudocode_call() -> None:
    result = render_tagged_line(PSEUDO_CALL_LINE)
    assert result.plain == PSEUDO_CALL_PLAIN
    spans = _get_spans(result)
    assert ("result", DEFAULT_THEME[COLOR_LIBNAME]) in spans
    assert ("sub_401000", DEFAULT_THEME[COLOR_DEMNAME]) in spans
    assert ("a1", DEFAULT_THEME[COLOR_LIBNAME]) in spans
    assert ("a2", DEFAULT_THEME[COLOR_LIBNAME]) in spans


def test_strip_pseudocode_signature() -> None:
    assert strip_tags(PSEUDO_SIGNATURE_LINE) == PSEUDO_SIGNATURE_PLAIN


def test_strip_pseudocode_call() -> None:
    assert strip_tags(PSEUDO_CALL_LINE) == PSEUDO_CALL_PLAIN


# --- strip_tags tests ---


def test_strip_plain_text() -> None:
    assert strip_tags("push    eax") == "push    eax"


def test_strip_single_tag_pair() -> None:
    assert strip_tags(_tag(COLOR_INSN, "push")) == "push"


def test_strip_multiple_sequential_tags() -> None:
    line = (
        _tag(COLOR_INSN, "mov")
        + "    "
        + _tag(COLOR_REG, "eax")
        + ", "
        + _tag(COLOR_NUMBER, "42h")
    )
    assert strip_tags(line) == "mov    eax, 42h"


def test_strip_nested_tags() -> None:
    line = _on(COLOR_OPND1) + _tag(COLOR_NUMBER, "52h") + _off(COLOR_OPND1)
    assert strip_tags(line) == "52h"


def test_strip_color_addr_64bit() -> None:
    assert strip_tags(_addr64() + "visible") == "visible"


def test_strip_color_addr_32bit() -> None:
    assert strip_tags(_addr32() + "visible", addr_width=8) == "visible"


def test_strip_color_esc() -> None:
    assert strip_tags("a" + ESC + "\x01" + "b") == "a\x01b"


def test_strip_color_inv() -> None:
    assert strip_tags("a" + INV + "b") == "ab"


def test_strip_empty_input() -> None:
    assert strip_tags("") == ""


def test_strip_preserves_spaces() -> None:
    line = _tag(COLOR_PREFIX, "1000") + "   " + _tag(COLOR_INSN, "nop")
    assert strip_tags(line) == "1000   nop"


def test_strip_realistic_line() -> None:
    assert strip_tags(REALISTIC_LINE) == REALISTIC_PLAIN


def test_strip_truncated_color_on() -> None:
    assert strip_tags("text" + ON) == "text"


def test_strip_truncated_color_off() -> None:
    assert strip_tags("text" + OFF) == "text"


def test_strip_truncated_color_esc() -> None:
    assert strip_tags("text" + ESC) == "text"


def test_strip_truncated_addr_payload() -> None:
    assert strip_tags(ON + chr(COLOR_ADDR) + "00004010") == ""


def test_strip_unicode() -> None:
    assert strip_tags(_tag(COLOR_STRING, '"héllo"')) == '"héllo"'


def test_strip_invalid_addr_width() -> None:
    with pytest.raises(ValueError, match="addr_width must be 8 or 16"):
        strip_tags("", addr_width=4)


# --- invariant: strip_tags(line) == render_tagged_line(line).plain ---


INVARIANT_LINES = [
    "",
    "plain text",
    _tag(COLOR_INSN, "push"),
    _tag(COLOR_INSN, "mov") + "    " + _tag(COLOR_REG, "eax"),
    _on(COLOR_OPND1) + _tag(COLOR_NUMBER, "52h") + _off(COLOR_OPND1),
    _on(COLOR_OPND1)
    + "["
    + _tag(COLOR_REG, "eax")
    + "+"
    + _tag(COLOR_NUMBER, "10h")
    + "]"
    + _off(COLOR_OPND1),
    _addr64() + "after",
    "before" + ESC + "\x01" + "after",
    "a" + INV + "b",
    _tag(COLOR_REGCMT, "; comment"),
    _tag(COLOR_AUTOCMT, "; auto"),
    _on(COLOR_INSN) + _off(COLOR_INSN) + "text",
    _on(COLOR_OPND1)
    + _on(COLOR_REG)
    + _on(COLOR_SYMBOL)
    + "+"
    + _off(COLOR_SYMBOL)
    + _off(COLOR_REG)
    + _off(COLOR_OPND1),
    REALISTIC_LINE,
    PSEUDO_SIGNATURE_LINE,
    PSEUDO_DECL_LINE,
    PSEUDO_IF_LINE,
    PSEUDO_RETURN_LINE,
    PSEUDO_CALL_LINE,
]


@pytest.mark.parametrize("line", INVARIANT_LINES)
def test_strip_matches_render_plain(line: str) -> None:
    assert strip_tags(line) == render_tagged_line(line).plain
