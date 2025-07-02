from __future__ import annotations

import sys
from io import StringIO
from typing import TYPE_CHECKING
from typing import Sized
from typing import TypeVar
import pytest
from boltons.tbutils import ExceptionInfo
from boltons.tbutils import TracebackInfo
from boltons.tbutils import fix_print_exception
from boltons.tbutils import print_exception

from pytest import param
from pytest import mark
from hamcrest import assert_that
from hamcrest import equal_to

if TYPE_CHECKING:
    pass

parameterize = pytest.mark.parametrize
SizedT = TypeVar("SizedT", bound=Sized)

def test_exception_info():
    # test ExceptionInfo and TracebackInfo and hooks, via StringIOs
    builtin_exc_hook = sys.excepthook
    fix_print_exception()
    tbi_str = ''

    fake_stderr1 = StringIO()
    fake_stderr2 = StringIO()
    sys.stderr = fake_stderr1

    def raise_value_error():
        raise ValueError('yay fun')

    try:
        raise_value_error()
    except:
        exc, _, exc_traceback = sys.exc_info()
        tbi = TracebackInfo.from_traceback(exc_traceback)
        exc_info = ExceptionInfo.from_exc_info(*sys.exc_info())
        exc_info2 = ExceptionInfo.from_current()
        tbi_str = str(tbi)
        print_exception(*sys.exc_info(), file=fake_stderr2)
        new_exc_hook_res = fake_stderr2.getvalue()
        builtin_exc_hook(*sys.exc_info())
        builtin_exc_hook_res = fake_stderr1.getvalue()
    finally:
        sys.stderr = sys.__stderr__
