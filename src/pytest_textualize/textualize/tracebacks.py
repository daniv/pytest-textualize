from __future__ import annotations

from typing import TYPE_CHECKING

# noinspection PyProtectedMember
from _pytest._code import ExceptionInfo

# noinspection PyProtectedMember
from _pytest._code import code as pytest_code
from rich.columns import Columns
from rich.console import group
from rich.syntax import Syntax
from rich.traceback import Frame
from rich.traceback import Stack
from rich.traceback import Trace
from rich.traceback import Traceback as RichTraceback

from pytest_textualize import Textualize

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from pytest_textualize.typist import PytestExceptionInfoType
    from rich.console import RenderResult
    from rich.console import ConsoleRenderable


class RichTraceback(RichTraceback):
    def __init__(self, trace: Trace | None = None, **kwargs) -> None:
        super().__init__(trace, **kwargs)

    @group()
    def _render_stack(self, stack: Stack) -> RenderResult:
        from rich.console import render_markup
        import linecache
        from rich.scope import render_scope
        from rich.text import Text

        # path_highlighter = PathHighlighter()
        theme = self.theme

        def render_locals(f: Frame) -> Iterable[ConsoleRenderable]:
            if f.locals:
                yield render_scope(
                    f.locals,
                    title="locals",
                    indent_guides=self.indent_guides,
                    max_length=self.locals_max_length,
                    max_string=self.locals_max_string,
                )

        exclude_frames: range | None = None
        if self.max_frames != 0:
            exclude_frames = range(
                self.max_frames // 2,
                len(stack.frames) - self.max_frames // 2,
            )

        excluded = False
        for frame_index, frame in enumerate(stack.frames):
            if exclude_frames and frame_index in exclude_frames:
                excluded = True
                continue

            if excluded:
                assert exclude_frames is not None
                yield Text(
                    f"\n... {len(exclude_frames)} frames hidden ...",
                    justify="center",
                    style="traceback.error",
                )
                excluded = False

            first = frame_index == 0
            frame_filename = frame.filename
            suppressed = any(frame_filename.startswith(path) for path in self.suppress)

            frame_filename_path = Textualize.to_pathlib(frame.filename)

            if frame_filename_path.exists():
                posix = frame_filename_path.as_posix()
                content = f"{frame.filename}:{frame.lineno} in {frame.name}"
                text = render_markup(
                    f"[blue bold][link={posix}:{frame.lineno}]{content}[/link][/]",
                    style="pygments.text",
                )
            else:
                text = Text.assemble(
                    "in ",
                    (frame.name, "pygments.function"),
                    (":", "pygments.text"),
                    (str(frame.lineno), "pygments.number"),
                    style="pygments.text",
                )
            if not frame.filename.startswith("<") and not first:
                yield ""
            yield text
            if frame.filename.startswith("<"):
                yield from render_locals(frame)
                continue
            if not suppressed:
                try:
                    code_lines = linecache.getlines(frame.filename)
                    code = "".join(code_lines)
                    if not code:
                        continue
                    lexer_name = self._guess_lexer(frame.filename, code)
                    syntax = Syntax(
                        code,
                        lexer_name,
                        theme=theme,
                        line_numbers=True,
                        line_range=(
                            frame.lineno - self.extra_lines,
                            frame.lineno + self.extra_lines,
                        ),
                        highlight_lines={frame.lineno},
                        word_wrap=self.word_wrap,
                        code_width=self.code_width,
                        indent_guides=self.indent_guides,
                        dedent=False,
                    )
                    yield ""
                except Exception as error:
                    yield Text.assemble(
                        (f"\n{error}", "traceback.error"),
                    )
                else:
                    if frame.last_instruction is not None:
                        from rich.traceback import _iter_syntax_lines

                        start, end = frame.last_instruction
                        for line1, column1, column2 in _iter_syntax_lines(start, end):
                            try:
                                if column1 == 0:
                                    line = code_lines[line1 - 1]
                                    column1 = len(line) - len(line.lstrip())
                                if column2 == -1:
                                    column2 = len(code_lines[line1 - 1])
                            except IndexError:
                                continue

                            syntax.stylize_range(
                                style="traceback.error_range",
                                start=(line1, column1),
                                end=(line1, column2),
                            )
                    yield (
                        Columns(
                            [
                                syntax,
                                *render_locals(frame),
                            ],
                            padding=1,
                        )
                        if frame.locals
                        else syntax
                    )


class TextualizeTracebacks:

    @staticmethod
    def get_repr(
        showlocals: bool = False,
        style: pytest_code.TracebackStyle = "long",
        abspath: bool = False,
        tb_filter: (
            bool | Callable[[PytestExceptionInfoType[BaseException]], pytest_code.Traceback]
        ) = True,
        func_args: bool = False,
        truncate_locals: bool = True,
        truncate_args: bool = True,
        chain: bool = True,
    ) -> pytest_code.ReprExceptionInfo:
        pass

    @staticmethod
    def from_exception(exception: BaseException) -> ExceptionInfo[BaseException]:
        return ExceptionInfo.from_exception(exception)

    @staticmethod
    def from_current(exprinfo: str | None = None) -> ExceptionInfo[BaseException]:
        pass
