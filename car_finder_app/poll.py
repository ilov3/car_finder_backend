# -*- coding: utf-8 -*-
# Owner: Bulat <bulat.kurbangaliev@cinarra.com>
import logging

__author__ = 'ilov3'

import time
from functools import partial

logger = logging.getLogger(__name__)


class TimeoutException(BaseException):
    pass


class StopPoll(BaseException):
    pass


class Poll(object):
    def __init__(self,
                 func,
                 failed_answer=False,
                 max_time=60,
                 propagate=True,
                 return_attempts_count=False,
                 args=None, kwargs=None,
                 strict_failed_answer=True,
                 poll_delay=1,
                 msg=None,
                 min_time=0):
        """
        Polling function with lots of options:

        :param (func) func: function object to be polled
        :param (str|int|bool) failed_answer: value which is used to know function failed or not (used only when strict_failed_answer=True,
                                             otherwise to boolean converting is used)
        :param (int) max_time: number of iterations to wait until non failed answer
        :param (bool) propagate: Changes behaviour when max_time exceeded (raises exception if True)
        :param (bool) return_attempts_count: If True: returns dict {'ret': function result, 'attempt': number of attempts}
                                             If False: returns function result
        :param (tuple) args: args to be passed into function
        :param (dict) kwargs: kwargs to be passed into function
        :param (bool) strict_failed_answer: If True: use failed_answer to test the function result
                                            If False: convert to boolean function result
        :param (int|float) poll_delay: how often to poll in seconds
        :param (str) msg: helper message describing whats we waiting for
        :param (int) min_time: minimal number of iterations to make before return
        :return: {'ret': function result, 'attempt': number of attempts} or function result or None
        """
        self.args = args if args else ()
        self.kwargs = kwargs if kwargs else {}
        self.counter = 0
        self.func = func
        self.failed_answer = failed_answer
        self.strict_failed_answer = strict_failed_answer
        self.poll_delay = poll_delay
        self.max_time = max_time
        self.min_time = min_time
        self.propagate = propagate
        self.return_attempts_count = return_attempts_count
        self.msg = msg
        self.exit = False
        self.start = None
        self.func_info = self._get_func_info()
        self.init_time = time.time()

    @staticmethod
    def shortenizer(s):
        return s if len(s) <= 15 else f'{s[:15]}...'

    def _get_func_info(self):
        pattern = '{name}{varnames} loc:{filename},{line}'
        func = self.func
        args = [self.shortenizer(str(a)) for a in self.args]
        kwargs = {key: self.shortenizer(str(value)) for key, value in self.kwargs.items()}
        if isinstance(func, partial) and hasattr(func, 'func'):
            func = func.func
        if hasattr(func, '__code__'):
            filename = func.__code__.co_filename
            filename = filename.split('/')[-1] if '/' in filename else filename
            return pattern.format(name=func.__qualname__,
                                  varnames=func.__code__.co_varnames,
                                  args=args, kwargs=kwargs,
                                  filename=filename, line=func.__code__.co_firstlineno)

    def _is_func_failed(self, func_ret):
        ret = func_ret[0] if isinstance(func_ret, tuple) else func_ret
        return (self.strict_failed_answer and ret == self.failed_answer) or (not self.strict_failed_answer and not ret)

    def poll(self):
        message = f'Polling func: {self.func_info}'
        message = f'Waiting for {self.msg}. {message}' if self.msg else message
        logger.info(message)
        func_ret = None
        if self.min_time > 0:
            for _ in range(self.min_time):
                start = time.time()
                try:
                    self.func(*self.args, **self.kwargs)
                except:
                    pass
                time_to_wait = self.poll_delay - time.time() + start
                if self.poll_delay > time_to_wait > 0:
                    time.sleep(time_to_wait)

        while not self.exit:
            self.start = time.time()
            try:
                self.counter += 1
                func_ret = self.func(*self.args, **self.kwargs)
            except StopPoll as exception:
                self.exit = True
                self._continue_or_fail(exception)

            except Exception as exception:
                self._continue_or_fail(exception)
            else:
                if self._is_func_failed(func_ret):
                    if not self.return_attempts_count:
                        func_ret = None
                    self._continue_or_fail()
                else:
                    msg = f'Success. Iter:{self.counter}::{time.time() - self.init_time:.2f}sec. Result:{self.shortenizer(str(func_ret))}'
                    logger.info(msg)
                    self.exit = True
        return {'ret': func_ret, 'attempt': self.counter} if self.return_attempts_count else func_ret

    def _continue_or_fail(self, exception=None):
        self.end = time.time()
        if self.counter >= self.max_time or isinstance(exception, StopPoll):
            if self.propagate:
                msg = f'Fail. Iter:{self.counter}::{time.time() - self.init_time:.2f}sec Func:{self.func_info}'
                msg = f'Failed to wait {self.msg}. {msg}' if self.msg else msg
                if exception:
                    msg = f'{msg}. Error: {exception}'
                    raise StopPoll(msg) if isinstance(exception, StopPoll) else TimeoutException(msg) from exception
                else:
                    raise TimeoutException(msg)
            else:
                if exception:
                    logger.exception(exception)
                msg = f'Waited for {self.counter} iterations but still incorrect result returned for {self.func_info}'
                msg = f'Failed to wait "{self.msg}". {msg}' if self.msg else msg
                logger.warning(msg)
                self.exit = True
                return
        time_to_wait = self.poll_delay - self.end + self.start
        if self.poll_delay > time_to_wait > 0:
            time.sleep(time_to_wait)


def poll(func, failed_answer=False, max_time=60, propagate=True,
         return_attempts_count=False, args=None, kwargs=None, strict_failed_answer=True, poll_delay=1, msg=None, min_time=0):
    p = Poll(func, failed_answer=failed_answer, max_time=max_time, propagate=propagate, return_attempts_count=return_attempts_count, args=args,
             kwargs=kwargs, strict_failed_answer=strict_failed_answer, poll_delay=poll_delay, msg=msg, min_time=min_time)
    return p.poll()


def old_poll(func, failed_answer=False, max_time=60, propagate=False, return_attempts_count=True, args=None, kwargs=None,
             strict_failed_answer=False):
    p = Poll(func, failed_answer, max_time, propagate, return_attempts_count, args, kwargs, strict_failed_answer)
    return p.poll()
