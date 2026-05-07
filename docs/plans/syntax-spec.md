# idawilli.syntax — Specification

This module converts IDA Pro's tagged disassembly lines into Rich `Text` objects for syntax-colored terminal output. IDA's line generation APIs return strings with embedded binary tags that encode color regions. The module parses those tags and translates them into Rich styles, producing renderable `Text` objects.


## Public Interface

`render_tagged_line(tagged_line: str, *, theme: Theme | None = None, addr_width: int = 16) -> rich.text.Text`
accepts a tagged line string and returns a styled `Text`. The `theme` maps IDA color codes (int) to Rich style strings; when omitted, `DEFAULT_THEME` is used. The returned object can be passed to `Console.print()` or composed into other Rich renderables.

`strip_tags(tagged_line: str, *, addr_width: int = 16) -> str`
removes all tag bytes and returns only the visible text. Equivalent to `ida_lines.tag_remove()` but without an IDA dependency.

`Theme` is a type alias for `dict[int, str]`.

`DEFAULT_THEME` provides reasonable defaults for dark terminals. Mnemonics (`COLOR_INSN`) render as `bold bright_blue`, registers as `cyan`, numeric constants as `bright_red`, strings as `green`, comments as `bright_black italic`, names/symbols as `yellow`, directives as `magenta`, and address prefixes as `bright_black`. Unmapped codes render as plain text. The full mapping covers all documented IDA color codes.

The `addr_width` parameter (keyword-only, default 16) controls how many characters are consumed for COLOR_ADDR payloads. Valid values are 8 and 16. Since idalib (IDA 9.0+) always uses 64-bit internal addressing, tagged text always embeds 16-character hex payloads regardless of the target binary's bitness. The default of 16 is therefore always correct for idalib. The `addr_width=8` path exists only for compatibility with legacy 32-bit IDA builds (pre-9.0). Passing a mismatched width causes address payload characters to leak into or be consumed from visible text.


## Usage

```python
from rich.console import Console
from idawilli.syntax import render_tagged_line

console = Console()
rich_text = render_tagged_line(tagged_line)
console.print(rich_text)
```

Override specific colors by merging into the default theme:
```python
from idawilli.syntax import render_tagged_line, DEFAULT_THEME

my_theme = {**DEFAULT_THEME, 0x05: "bold green"}
rich_text = render_tagged_line(tagged_line, theme=my_theme)
```


## Behavior

The module handles both disassembly and pseudocode (Hex-Rays decompiler) tagged lines. Both use the identical tag format and the same color code palette — the decompiler does not introduce any pseudocode-specific color codes. In pseudocode, COLOR_ADDR carries ctree item anchors rather than instruction addresses, but the format and consumption rules are identical.

The parser maintains a style stack. When tags nest (e.g., OPND1 wrapping NUMBER), the innermost active tag determines the style. After the inner tag closes, the outer tag's style resumes.

COLOR_ADDR (0x28) is consumed silently: the tag-on byte, type byte, and hex payload are all skipped with no visible text emitted and no COLOR_OFF expected. COLOR_ESC (0x03) causes the following byte to be emitted as literal visible text with the current style. COLOR_INV (0x04) is skipped entirely.

Unrecognized tag types are pushed onto and popped from the style stack normally but render with no style. Empty input returns an empty `Text()`. Truncated input (string ending mid-tag) causes the parser to stop gracefully without raising.

COLOR_OFF ignores its type byte and always pops the top of the style stack. This matches IDA's own behavior where OFF acts as a generic "end current region." In well-formed IDA output, the type byte always matches the most recent ON, so this is equivalent to matched popping.


## Design Decisions

All tag constants are defined inline so the module works without IDA installed. The single-pass character-by-character parser is simpler and more correct than regex approaches, especially with nested tags and variable-length address payloads. The style stack (rather than a single current-style variable) handles nesting correctly. The theme is a plain dict for maximum flexibility with minimum ceremony.
