# Project : pytest-textualize
# File Name : console_handler.py
# Dir Path : src/pytest_textualize/textualize/logging
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
import logging

from rich._log_render import LogRender
from rich._null_file import NullFile
from rich.logging import RichHandler
from rich.text import Text

if TYPE_CHECKING:
    from typing import Iterable
    from rich.console import Console
    from rich.console import ConsoleRenderable
    from rich.table import Table
    from rich.console import RenderableType
    from rich.text import TextType
    from rich._log_render import FormatTimeCallable


class TextualizeConsoleHandler(RichHandler):
    def __init__(self, level: int | str = logging.NOTSET, console: Console | None = None, **kwargs) -> None:
        super().__init__(level, console, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:

        if isinstance(self.console.file, NullFile):
            return None

        message = self.format(record)
        traceback = None
        if self.rich_tracebacks and record.exc_info and record.exc_info != (None, None, None):
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None

            from .tracebacks import TextualizeTraceback

            traceback = TextualizeTraceback.from_exception(
                exc_type,
                exc_value,
                exc_traceback,
                width=self.tracebacks_width,
                code_width=self.tracebacks_code_width,
                extra_lines=self.tracebacks_extra_lines,
                theme=self.tracebacks_theme,
                word_wrap=self.tracebacks_word_wrap,
                show_locals=self.tracebacks_show_locals,
                locals_max_length=self.locals_max_length,
                locals_max_string=self.locals_max_string,
                suppress=self.tracebacks_suppress,
                max_frames=self.tracebacks_max_frames,
            )
            message = record.getMessage()
            if self.formatter:
                record.message = record.getMessage()
                formatter = self.formatter
                if hasattr(formatter, "usesTime") and formatter.usesTime():
                    record.asctime = formatter.formatTime(record, formatter.datefmt)
                message = formatter.formatMessage(record)

        message_renderable = self.render_message(record, message)
        log_renderable = self.render(
            record=record, traceback=traceback, message_renderable=message_renderable
        )
        try:
            self.console.print(log_renderable)
        except Exception as e:
            self.handleError(record)

    def get_level_text(self, record: logging.LogRecord) -> Text:
        level_name = record.levelname
        level_text = Text.styled(level_name.lower().ljust(8), f"logging.level.{level_name.lower()}")
        return level_text


class TextualizeConsoleLogRender(LogRender):

    def __call__(
            self,
            console: Console,
            renderables: Iterable[ConsoleRenderable],
            log_time: datetime | None = None,
            time_format: str | FormatTimeCallable | None = None,
            level: TextType = "",
            path: str | None = None,
            line_no: int | None = None,
            link_path: str | None = None,
    ) -> Table:
        from rich.containers import Renderables
        from rich.table import Table

        output = Table.grid(padding=(0, 1))
        output.expand = True
        if self.show_time:
            output.add_column(style="log.time")
        if self.show_level:
            output.add_column(style="log.level", width=self.level_width)
        output.add_column(ratio=1, style="log.message", overflow="fold")
        if self.show_path and path:
            output.add_column(style="log.path")
        row: list[RenderableType] = []
        if self.show_time:
            log_time = log_time or console.get_datetime()
            time_format = time_format or self.time_format
            if callable(time_format):
                log_time_display = time_format(log_time)
            else:
                log_time_display = Text(log_time.strftime(time_format))
            if log_time_display == self._last_time and self.omit_repeated_times:
                row.append(Text(" " * len(log_time_display)))
            else:
                row.append(log_time_display)
                self._last_time = log_time_display
        if self.show_level:
            row.append(level)

        row.append(Renderables(renderables))

        if link_path:
            link_path = Path(link_path).as_posix()

        if self.show_path and path:
            path_text = f"link file://{link_path}" if link_path else ""
            if sys.stdout.isatty():
                path_text = path
            if line_no:
                link = f"{path}:{line_no}"
                if sys.stdout.isatty():
                    link = f"[link={link_path}:{line_no}]{path}:{line_no}[/link]"
                path_text = (
                    link
                    if link_path
                    else f"{path}:{line_no}"
                )
            row.append(Text.from_markup(path_text, style="blue"))
        output.add_row(*row)
        return output
