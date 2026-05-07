# idawilli.syntax — Design

Companion: syntax-spec.md (behavioral specification)

## File Layout

Single file: `idawilli/syntax.py`. No submodules, no additional files beyond the test file.


## Tag Format

IDA tagged lines are Python `str` objects where certain character positions contain non-printable control bytes:

| Byte | Name | Meaning |
|---|---|---|
| `\x01` | COLOR_ON | Next byte is the color type; start applying that style |
| `\x02` | COLOR_OFF | Next byte is the color type; stop applying that style |
| `\x03` | COLOR_ESC | Next byte is a literal character (escaped) |
| `\x04` | COLOR_INV | Invisible text marker (single byte, no payload) |

Color types range from `0x01` to `0x32`. Most come in ON/OFF pairs. The exception is `COLOR_ADDR` (`0x28`), which carries an inline hex-encoded address payload of fixed width (16 chars for 64-bit, 8 for 32-bit) with no OFF pair. Since idalib (IDA 9.0+) always uses 64-bit internal addressing, the payload is always 16 characters regardless of target binary bitness. A 32-bit address like `0x10002004` is zero-padded to `0000000010002004`.

Tags can nest. IDA wraps operand-level tags (OPND1 through OPND6, at `0x29` through `0x2E`) around finer-grained color tags (NUMBER, REG, CNAME, etc.).

The same tag format and color code palette are used by both the disassembler and the Hex-Rays decompiler. In pseudocode, COLOR_ADDR embeds ctree item anchors rather than instruction addresses, and lines are densely packed with them (often 5-10 per line). The decompiler reuses existing color codes for pseudocode elements: COLOR_KEYWORD for C keywords and numeric literals, COLOR_LIBNAME for local variable names, COLOR_DEMNAME for called function names, COLOR_HIDNAME for type casts and function signatures, and COLOR_SYMBOL for punctuation and operators.

The sentinel bytes 0x01 through 0x04 share numeric values with color types COLOR_DEFAULT through COLOR_AUTOCMT. They are distinguished by position: sentinels appear as the first byte of a sequence, while color type bytes appear as the second byte after a sentinel.


## Parser Design

Single-pass, character-by-character, with a style stack. The actual implementation uses a buffer to batch consecutive characters with the same style into single `Text.append()` calls, flushing the buffer on each style transition.

```
i = 0
style_stack = []
buf = []
result = Text()

while i < len(line):
    ch = ord(line[i])

    if ch == 0x01:           # COLOR_ON
        tag = ord(line[i+1])
        i += 2
        if tag == 0x28:      # COLOR_ADDR: skip payload
            i += ADDR_WIDTH
        else:
            flush buf to result with current style
            style_stack.append(theme.get(tag, ""))

    elif ch == 0x02:         # COLOR_OFF
        i += 2
        flush buf to result with current style
        if style_stack: style_stack.pop()

    elif ch == 0x03:         # COLOR_ESC
        buf.append(line[i+1])
        i += 2

    elif ch == 0x04:         # COLOR_INV
        i += 1

    else:                    # visible character
        buf.append(line[i])
        i += 1

flush remaining buf
```

Current style is `style_stack[-1]` if non-empty, else `""` (no style). Truncated input (string ending mid-tag) terminates the loop gracefully via bounds checking before each `line[i+1]` access.


## Theme Mapping

The default theme is a `dict[int, str]` defined at module level. Each key is a color type byte value (e.g., `0x05` for COLOR_INSN), each value is a Rich style string. Lookup happens at COLOR_ON time and the resolved style string is pushed onto the stack.


## strip_tags Implementation

Same parser loop but appends visible characters to a `list[str]` and joins at the end. The two functions are simple enough that sharing the loop via a common iterator would add indirection without reducing total LOC.


## Dependencies

`rich` for the `Text` class (already a dependency of the broader project). No IDA modules at import or runtime.


## Testing Strategy

Tests construct tagged lines by hand using the known byte format, building strings with explicit `\x01`, `\x02`, etc. bytes. The realistic line test uses `bytes.fromhex(...).decode("latin-1")` from the hex dump in `lex_curline.py` to avoid transcription errors.

66 tests across three classes cover plain text, single and multiple tag pairs, nested tags (including triple nesting and visible outer styles), COLOR_ADDR payloads (64-bit, 32-bit, truncated, consecutive, addr_width mismatch), COLOR_ESC (including all sentinel bytes and escapes inside styled regions), COLOR_INV, empty input, custom themes, truncated input for all sentinel types, Unicode text, mismatched and extra OFF tags, and a parametrized invariant that `strip_tags(line) == render_tagged_line(line).plain` across all test inputs.
