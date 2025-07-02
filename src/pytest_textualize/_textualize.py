from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Literal
from typing import NoReturn
from typing import Optional
from typing import Self
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError
from rich import box
from rich.console import Console
from rich.console import render_markup
from rich.panel import Panel
from rich.scope import render_scope
from rich.text import Text

from pytest_textualize import assert_never

if TYPE_CHECKING:
    from pytest_textualize.typist import TextualizeSettingsType
    from pytest_textualize.typist import PathLike
    from pytest_textualize.typist import VerboseLoggerType
    from pytest_textualize.typist import TextAlias
    from rich.text import TextType
    from rich.style import StyleType

logger = logging.getLogger("textualize")
_CLICK_AFTER = chr(0x2B84) + " click"
_CLICK_BEFORE = "click " + chr(0x2B86)


def is_markup(string: str) -> bool:
    if string:
        text = render_markup(string)
        return len(text.spans) > 0
    return False


class ConsoleMessage:

    def __init__(self, text: str, debug=False) -> None:
        self.text = text
        self.debug = debug

    @property
    def stripped(self) -> str:
        if is_markup(self.text):
            txt = Text.from_markup(self.text)
            return txt.plain
        return self.text

    def style(self, name: str) -> Self:
        if self.text:
            self.text = f"[{name}]{self.text}[/{name}]"
            pass
        return self

    def indent(self, indent: str) -> ConsoleMessage:
        if self.text:
            self.text = f"\n{indent}".join(self.text.splitlines()).strip()
            self.text = f"{indent}{self.text}"
        return self

    def make_section(self, title: str, indent: str = "", style: str | None = None) -> Self:
        if not self.text:
            return self.text

        if self.text:
            section = [f"[b]{title}:[/b]"] if title else []
            if style:
                self.style(style)
            section.extend(self.text.splitlines())
            self.text = f"\n{indent}".join(section).strip()

        return self


class Textualize:

    def __init__(self, config: pytest.Config) -> None:
        self.config = config

    # @staticmethod
    # def theme_factory() -> ThemeFactoryType:
    #     from pytest_textualize.factories.theme_factory import ThemeFactory
    #     return ThemeFactory()

    @staticmethod
    def settings(config: pytest.Config) -> TextualizeSettingsType:
        return Textualize.init_settings(config)

    @staticmethod
    def init_settings(config: pytest.Config) -> TextualizeSettingsType | None:
        from dotenv import load_dotenv
        from pathlib import Path
        from pytest_textualize.plugin import settings_key
        from pytest_textualize.settings import TextualizeSettings
        from pytest_textualize.plugin.base import BaseTextualizePlugin

        settings = config.stash.get(settings_key, None)
        if settings:
            return settings

        # loading environment variable fro file, based on ini value env_file, skipped if not exists
        ini_env_file = config.getini("env_file")
        if Path(ini_env_file).is_file():
            load_dotenv(ini_env_file, verbose=True)

        try:
            ts = TextualizeSettings(pytestconfig=config)
            settings = BaseTextualizePlugin.validate_settings(ts)
            config.stash[settings_key] = ts
        except ValidationError as exc:
            print("")
            c = Console(color_system="truecolor", force_terminal=True, stderr=True)
            for err in exc.errors(include_url=False):
                sys.stderr.write(str(err) + "\n\n")
                c.print(
                    render_scope(err, title="[traceback.exc_type]ValidationError"),
                    style="traceback.error",
                    justify="left",
                )
                c.print(
                    "Please check the configuration, calling pytest.exit()",
                    style="traceback.error",
                    highlight=False,
                )
            del c

        def cleanup() -> None:
            del ts.logging_settings
            del ts.pytestconfig
            del ts.console_settings
            del ts.tracebacks_settings

        config.add_cleanup(cleanup)

        return settings

    @staticmethod
    def print_pytest_textualize_sessionstart_header(console: Console) -> None:
        from importlib import metadata

        version = metadata.version("pytest_textualize")
        panel = Panel(
            Text(
                "A pytest plugin using Rich for beautiful test result formatting.",  # noqa: E501
                justify="center",
                style="txt.header.version",
            ),
            title="[txt.header.title]pytest.textualize plugin[/]",
            title_align="center",
            subtitle=f"[txt.header.content]v{version}[/]",
            subtitle_align="center",
            box=box.DOUBLE,
            style="txt.header.border",
            padding=2,
            expand=True,
            highlight=False,
            safe_box=True,
        )

        console.print("", style="reset", end="")
        console.print(panel, new_line_start=True)
        return None

    @staticmethod
    def logging_config(config: pytest.Config):
        from pytest_textualize.textualize.logging import LoggingConfig

        settings = Textualize.init_settings(config)
        return LoggingConfig(settings)

    # @staticmethod
    # def model() -> ModelFactoryType:
    #     from pytest_textualize.factories.model_factory import ModelFactory
    #     return ModelFactory()

    @staticmethod
    def console_factory(
        config: pytest.Config, instance: Literal["<stdout>", "<stderr>", "buffer", "null"]
    ) -> Console | NoReturn:
        from pytest_textualize.factories.console_factory import ConsoleFactory
        from pytest_textualize.textualize.logging import TextualizeLogRender

        match instance:
            case "<stdout>":
                c = ConsoleFactory().console_stdout(config)
                TextualizeLogRender.override_log_render(console=c)
                return c

            case "<stderr>":
                c = ConsoleFactory().console_stderr(config)
                TextualizeLogRender.override_log_render(console=c)
                return c

            case "buffer":
                return ConsoleFactory().console_buffer(config)

            case "null":
                return ConsoleFactory().console_null(config)

            case _:
                assert_never(instance)
        return None

    @staticmethod
    def verbose_logger(config: pytest.Config) -> VerboseLoggerType:
        from pytest_textualize.textualize.logging import VerboseLogger

        return VerboseLogger(config)

    @staticmethod
    def to_pathlib(filepath: str) -> Path:
        assert isinstance(filepath, str), "input type is not str"
        return Path(filepath)

    @staticmethod
    def relative_path(filepath: PathLike) -> Path:
        from pytest_textualize import TS_BASE_PATH

        assert isinstance(filepath, str) or isinstance(
            filepath, Path
        ), "input type is not PathLike (str | Path)"
        if isinstance(filepath, str):
            filepath = Textualize.to_pathlib(filepath)
        try:
            return Path(filepath).relative_to(TS_BASE_PATH)
        except ValueError as e:
            e.add_note(
                f"handled: on {Textualize.__module__}.{Textualize.__qualname__}.relative_path"
            )
            # todo: ConsoleMessage + RuntimeError
            logger.error(str(e))
            raise e from e

    @staticmethod
    def is_gettrace() -> bool:
        return False if getattr(sys, "gettrace", None) is None else True

    @staticmethod
    def hook_msg(
        hookname: str,
        info: Optional[TextType] = None,
    ) -> tuple[TextAlias, TextAlias, TextAlias]:

        level = Text("\u2bc0", style="pyest.hook.prefix")
        hookname = Text(hookname.ljust(30), style="pyest.hook.name")
        msg = Text("hook:".ljust(6), style="pyest.hook.tag").append_text(hookname)
        if info:
            info_text = Text()
            if isinstance(info, str):
                if is_markup(info):
                    info_text.append(Text.from_markup(info, end=""))
                else:
                    info_text.append(Text(info))
            else:
                info_text.append_text(info)

        return msg, info, level

    @staticmethod
    def keyval_msg(
        key: str,
        value: TextType = "",
        *,
        kv_separator: Optional[str] = None,
        level: Optional[str] = None,
        value_style: Optional[StyleType] = None,
        highlight: bool = False,
    ) -> tuple[TextAlias, TextAlias, TextAlias]:
        from pytest_textualize.textualize.console import KeyValueMessage

        kvm = KeyValueMessage(
            key,
            value,
            kv_separator=kv_separator,
            level=level,
            value_style=value_style,
            highlight=highlight,
        )
        return kvm()

    @staticmethod
    def stage_rule(
        console: Console,
        stage: Literal["session", "collection", "error", "execution"],
        time_str: str,
        start: bool = True,
    ) -> None:
        msg = "started" if start else "ended"
        title = (
            f"[txt.stage_title][b]{stage.capitalize()}[/] {msg} at[/] [txt.stage_time]{time_str}[/]"
        )

        console.line()
        console.rule(title, characters="=", style="#c562af")
        console.line()

    @staticmethod
    def create_link(
        link_path: PathLike,
        lineno: int,
        isatty: bool,
        *,
        use_click: bool = False,
        click_location: Literal["before", "after"] = "before",
    ) -> Text:
        from rich.console import render_markup

        if isinstance(link_path, str):
            link_path = Textualize.to_pathlib(link_path)

        relative = Textualize.relative_path(link_path)
        if isatty and use_click and click_location == "after":
            return render_markup(
                f"[blue][link={str(relative)}:{lineno}]{relative.name}:{lineno}[/link] {_CLICK_AFTER}[/]"
            )
        elif isatty and use_click and click_location == "before":
            return render_markup(
                f"[blue]{_CLICK_BEFORE} [link={str(relative)}:{lineno}]{relative.name}:{lineno}[/link][/]"
            )
        elif isatty and use_click is False:
            return render_markup(f"[link={str(relative)}:{lineno}]{relative.name}:{lineno}[/link]")
        else:
            return Text(f"File {relative.as_posix()}:{lineno}")

    # @staticmethod
    # def runtime_error(
    #         reason: str, exc_typename: str, messages: Iterable[ConsoleMessageType]
    # ) -> TextualizeRuntimeError:
    #     from pytest_textualize.plugin.exceptions import TextualizeRuntimeError
    #
    #     messages = messages or []
    #     rte = TextualizeRuntimeError(
    #         reason=reason, exc_typename=exc_typename, messages=messages
    #     )
    #     pass
    #
    # @staticmethod
    # def runtime_error_create(
    #         reason: str, exc_value: BaseException,
    #         info: list[str | ConsoleMessageType] | str | ConsoleMessageType| None = None
    # ) -> TextualizeRuntimeError:
    #     from pytest_textualize.plugin.exceptions import TextualizeRuntimeError
    #     return TextualizeRuntimeError.create(reason, exc_value, info=info)
