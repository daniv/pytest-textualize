from __future__ import annotations

import inspect
import logging
import os
import sys
from datetime import datetime
from typing import Annotated
from typing import Any
from typing import NamedTuple
from typing import NotRequired
from typing import Optional
from typing import TYPE_CHECKING
from typing import TypedDict
from typing import Unpack

import pytest
from annotated_types import MaxLen
from annotated_types import MinLen
from pydantic import BaseModel
from pydantic import TypeAdapter
from pydantic_core import PydanticCustomError

# noinspection PyProtectedMember
from rich._log_render import LogRender

# noinspection PyProtectedMember
from rich._null_file import NullFile
from rich.logging import RichHandler
from rich.segment import Segment
from rich.styled import Styled
from rich.table import Table
from rich.text import Text

from pytest_textualize import Verbosity
from rich.scope import render_scope
from rich.containers import Renderables

if TYPE_CHECKING:
    from types import FrameType
    from types import TracebackType
    from collections.abc import Iterator
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Mapping
    from pytest_textualize.typist import TextualizeSettingsType
    from pytest_textualize.typist import TableType
    from rich.console import Console
    from pytest_textualize.typist import TextAlias
    from pytest_textualize.typist import DictStrAny
    from rich.text import TextType
    from rich.style import StyleType
    from rich.console import JustifyMethod
    from rich.console import RenderableType
    from rich.console import ConsoleRenderable


class TextualizeHandler(RichHandler):
    def __init__(
        self, level: int | str = logging.NOTSET, console: Console | None = None, **kwargs
    ) -> None:
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

            from .tracebacks import RichTraceback

            traceback = RichTraceback.from_exception(
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

    def get_level_text(self, record: logging.LogRecord) -> TextAlias:
        from rich.text import Text

        level_name = record.levelname
        level_text = Text.styled(level_name.lower().ljust(8), f"logging.level.{level_name.lower()}")
        return level_text


class TextualizeLogRender(LogRender):

    def __call__(
        self,
        console: Console,
        renderables: Iterable[ConsoleRenderable],
        log_time: Optional[datetime] = None,
        time_format: str = "[%x %X]",
        level: TextType = "",
        path: str | None = None,
        line_no: int | None = None,
        link_path: str | None = None,
    ) -> TableType:
        output = Table.grid(padding=(0, 1))
        output.expand = True
        if self.show_time:
            output.add_column(style="log.time")
        if self.show_level:
            output.add_column(
                style="log.level",
                # width=self.level_width,
                # max_width=10,
                justify="center",
            )
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
        if self.show_path and path:
            path_text = Text()
            if sys.stdout.isatty():
                path_text_str = f"[link={link_path}][blue]{path}[/][/link]"
                if line_no:
                    path_text_str = f"[link={link_path if link_path else ""}:{line_no}][blue]{path}:{line_no}[/][/link]"
                row.append(path_text_str)
            else:
                path_text.append(path)
                if line_no:
                    path_text.append(":")
                    path_text.append(f"{line_no}")
                row.append(path_text)
        output.add_row(*row)
        return output

    @classmethod
    def override_log_render(cls, console: Console) -> Console:
        log_render: LogRender = getattr(console, "_log_render", None)
        log_render = TextualizeLogRender(
            level_width=log_render.level_width,
            time_format=log_render.time_format,
            omit_repeated_times=log_render.omit_repeated_times,
            show_path=log_render.show_path,
            show_level=log_render.show_level,
            show_time=log_render.show_time,
        )
        setattr(console, "_log_render", log_render)
        return console


class LoggingConfig:

    def __init__(self, settings: TextualizeSettingsType) -> None:
        self.settings = settings

    @staticmethod
    def reset_logging() -> None:
        # -- Remove all handlers from the root logger
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)
        # -- Reset logger hierarchy, this clears the internal dict of loggers
        logging.Logger.manager.loggerDict.clear()

    @staticmethod
    def override_log_render(console: Console) -> Console:
        renderer = TextualizeLogRender(show_time=False, show_path=True, show_level=False)
        console._log_render = renderer
        return console

    def configure_logging(self) -> None:
        from rich.console import Console

        logging_console = Console(color_system="truecolor", force_terminal=True)
        logging_options = self.settings.logging_settings.model_dump(
            exclude_unset=True, exclude={"level", "log_format", "log_time_format"}
        )
        handler_level = self.settings.logging_settings.level
        log_format = self.settings.logging_settings.log_format
        log_time_format = self.settings.logging_settings.log_time_format

        try:
            LoggingConfig.reset_logging()
            handler = TextualizeHandler(handler_level, logging_console, **logging_options)
            log_render: LogRender = getattr(handler, "_log_render", None)
            if log_render:
                show_time = log_render.show_time
                show_level = log_render.show_level
                show_path = log_render.show_path
                time_format = log_render.time_format
                omit_repeated_times = log_render.omit_repeated_times
                level_width = None
                new_log_render = TextualizeLogRender(
                    show_time=show_time,
                    show_level=show_level,
                    show_path=show_path,
                    time_format=time_format,
                    omit_repeated_times=omit_repeated_times,
                    level_width=level_width,
                )
                setattr(handler, "_log_render", new_log_render)
            logging.basicConfig(
                level=logging.NOTSET,
                format=str(log_format),
                datefmt=log_time_format,
                handlers=[TextualizeHandler(handler_level, logging_console, **logging_options)],
            )
            logging.captureWarnings(True)

        except ValueError as e:
            if str(e).startswith("Unknown level"):
                from pytest import UsageError

                raise UsageError(
                    f"'{handler_level}' is not recognized as a logging level name for "
                    f"'log_level'. Please consider passing the logging level num instead."
                ) from e
            raise e from e


class VerboseLogRecord(NamedTuple):
    sep: str
    end: str
    level: int
    highlight: bool
    markup: bool
    level_text: TextAlias
    filename: str
    line_no: int
    log_locals: bool
    style: StyleType
    renderables: Iterable[RenderableType]
    exc_info: ExcInfoType
    justify: JustifyMethod
    locals: DictStrAny


VerboseLogRecord.__doc__ = "Stores the information of the logging instance"
type SysExcInfoType = tuple[type[BaseException], BaseException, TracebackType | None] | tuple[
    None, None, None
]
type ExcInfoType = None | bool | SysExcInfoType | BaseException


class ConsoleValidator(BaseModel, arbitrary_types_allowed=True):
    console: Console


from rich.console import Console

ConsoleValidator.model_rebuild()


class MypyTypeDict(TypedDict):
    highlight: NotRequired[bool]
    sep: NotRequired[str]
    end: NotRequired[str]
    justify: NotRequired[JustifyMethod]
    style: NotRequired[StyleType]
    markup: NotRequired[bool]
    log_locals: NotRequired[bool]


class VerboseLogger:
    def __init__(self, config: pytest.Config) -> None:
        from collections.abc import MutableMapping
        from pytest_textualize.plugin import settings_key

        settings = config.stash.get(settings_key, None)
        if settings is None:
            raise RuntimeError(
                "Expecting that config.stash[settings_key] was already initialized, but is None"
            )

        self._prefix: str = "\u2bc8"
        self._disabled: bool = False
        self._verbosity = Verbosity(config.option.verbose)
        self._consoles: MutableMapping[str, Console] = {}
        self.show_locals = settings.tracebacks_settings.show_locals
        self.raise_exceptions = True
        self._log_render = TextualizeLogRender(
            level_width=3,
            show_path=True,
            show_level=True,
            show_time=False,
        )

    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, value: str) -> None:
        self._prefix = TypeAdapter(Annotated[str, MaxLen(1), MinLen(1)]).validate_python(
            value, strict=True
        )

    def add_console(self, name: str, console: Console) -> tuple[bool, str]:
        if console is None or not isinstance(console, Console):
            raise PydanticCustomError(
                "is_instance_of",
                "arg 'console' should be an instance of {instance} not {input_type}",
                {"input_type": type(console), "instance": Console.__name__},
            )
        if not self._consoles:
            self._consoles[name] = console
            return True, f"Console {name} added successfully."
        else:
            if name in self._consoles:
                raise NameError(f"Duplicate console name: {name}")
            for n, c in self._consoles.items():
                if c.file is console.file:
                    return False, f"Console exists with different name -> '{n}'"
            self._consoles[name] = console
        return True, f"Console {name} added successfully."

    def remove_console(self, name: str) -> bool:
        if name not in self._consoles:
            return False
        del self._consoles[name]
        return True

    def remove_all_consoles(self) -> None:
        self._consoles.clear()
        return None

    def has_console(self, name: str) -> bool:
        return name in self._consoles

    @property
    def is_disabled(self) -> bool:
        return self._disabled

    @property
    def is_enabled(self) -> bool:
        return not self._disabled

    def set_disabled(self, disabled: bool) -> None:
        self._disabled = disabled

    @property
    def effective_verbose(self) -> Verbosity:
        return self._verbosity

    @property
    def console_count(self) -> int:
        return len(self._consoles)

    @property
    def consoles(self) -> Mapping[str, Console]:
        return self._consoles

    def iter_consoles(self) -> Iterator[tuple[str, Console]]:
        for n, c in iter(self._consoles.items()):
            yield n, c

    def debug(self, *objects: Any, **kwargs: Unpack[MypyTypeDict]) -> None:
        if self._is_enabled_for(Verbosity.DEBUG):
            self._log(*objects, level=logging.DEBUG, style="dim", **kwargs)
        return None

    def info(self, *objects: Any, **kwargs: Unpack[MypyTypeDict]) -> None:
        if self._is_enabled_for(Verbosity.VERY_VERBOSE):
            self._log(*objects, level=logging.INFO, **kwargs)
        return None

    def warning(self, *objects: Any, **kwargs: Unpack[MypyTypeDict]) -> None:
        if self._is_enabled_for(Verbosity.VERBOSE):
            self._log(*objects, level=logging.WARNING, **kwargs)

    def error(self, *objects: Any, **kwargs: Unpack[MypyTypeDict]) -> None:
        if self._is_enabled_for(Verbosity.NORMAL):
            self._log(*objects, level=logging.ERROR, style="#ff4242", **kwargs)

    def critical(self, *objects: Any, **kwargs: Unpack[MypyTypeDict]) -> None:
        if self._is_enabled_for(Verbosity.QUIET):
            self._log(*objects, level=logging.CRITICAL, style="textualize.log.critical", **kwargs)

    def log(
        self,
        *objects: Any,
        level_text: TextAlias,
        verbosity: Verbosity = Verbosity.VERBOSE,
        **kwargs: Unpack[VerboseLogRecord],
    ) -> None:
        if self._is_enabled_for(verbosity):
            self._log(*objects, level=logging.NOTSET, level_text=level_text, **kwargs)

    def _log(
        self,
        *objects: Any,
        level: int,
        sep: str = " ",
        end: str = "\n",
        justify: JustifyMethod = "left",
        style: StyleType = "none",
        markup: bool = True,
        highlight: bool = True,
        log_locals: bool = False,
        exc_info: ExcInfoType | None = None,
        level_text: TextAlias | None = None,
    ) -> None:
        filename, line_no, f_locals = self._caller_frame_info(2)
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()

        level_str = logging.getLevelName(level).lower()
        if level_text is None:
            level_text = Text(self.prefix, style=f"textualize.log.{level_str.lower()}", end="")

        record = VerboseLogRecord(
            renderables=objects,
            exc_info=exc_info,
            level_text=level_text,
            filename=filename,
            line_no=line_no,
            locals=f_locals,
            level=level,
            sep=sep,
            end=end,
            justify=justify,
            style=style,
            markup=markup,
            highlight=highlight,
            log_locals=log_locals,
        )
        self.handle(record)

    def handle(self, record: VerboseLogRecord) -> None:
        try:
            logged = False
            for name, console in self.iter_consoles():

                if record.level >= logging.ERROR and console.stderr:
                    self.process_record(console, record)
                    logged = True
                    break
                if record.level < logging.ERROR and console.stderr is False:
                    self.process_record(console, record)
                    logged = True
                    break
            else:
                if record.exc_info:
                    pass

            if record.level >= logging.ERROR and not logged:
                sys.stderr.write(
                    "No stderr consoles could be found, generating message via standard logging module\n"
                )
            elif record.level < logging.ERROR and not logged:
                sys.stderr.write("No consoles could be found, log message is omitted\n")
        except (KeyboardInterrupt, SystemExit, Exception) as e:
            pass

    def process_record(self, console: Console, record: VerboseLogRecord) -> None:
        if not record.renderables:
            return None

        render_hooks = getattr(console, "_render_hooks")[:]
        with console:
            renderables: list[ConsoleRenderable] = getattr(console, "_collect_renderables")(
                record.renderables,
                record.sep,
                record.end,
                justify=record.justify,
                markup=record.markup,
                highlight=record.highlight,
            )
            if record.style is not None:
                renderables = [Styled(renderable, record.style) for renderable in renderables]
            link_path = (
                None if record.filename.startswith("<") else os.path.abspath(record.filename)
            )
            path = record.filename.rpartition(os.sep)[-1]
            if self.show_locals:
                locals_map = {
                    key: value for key, value in record.locals.items() if not key.startswith("__")
                }
                renderables.append(render_scope(locals_map, title="[i]locals[/]"))
            renderables = [
                self._log_render(
                    console,
                    renderables,
                    level=record.level_text,
                    path=path,
                    line_no=record.line_no,
                    link_path=link_path,
                )
            ]
            for hook in render_hooks:
                renderables = hook.process_renderables(renderables)
            new_segments: list[Segment] = []
            extend = new_segments.extend
            render = console.render
            render_options = console.options
            for renderable in renderables:
                extend(render(renderable, render_options))
            buffer_extend = getattr(console, "_buffer").extend
            for line in Segment.split_and_crop_lines(new_segments, console.width, pad=False):
                buffer_extend(line)
        return None

    def _is_enabled_for(self, verbosity: Verbosity) -> bool:
        """Is this logger enabled for level 'level'?"""
        if self._disabled:
            return False
        return self.effective_verbose >= verbosity

    @staticmethod
    def _caller_frame_info(
        offset: int,
        currentframe: Callable[[], Optional[FrameType]] = inspect.currentframe,
    ) -> tuple[str, int, dict[str, Any]]:
        offset += 1

        frame = currentframe()
        if frame is not None:
            # Use the faster currentframe where implemented
            while offset and frame is not None:
                frame = frame.f_back
                offset -= 1
            assert frame is not None
            return frame.f_code.co_filename, frame.f_lineno, frame.f_locals
        else:
            # Fallback to the slower stack
            frame_info = inspect.stack()[offset]
            return frame_info.filename, frame_info.lineno, frame_info.frame.f_locals
