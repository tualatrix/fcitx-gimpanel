import os
import logging
import StringIO
import traceback

from gimpanel.common import CONFIG_ROOT

#The terminal has 8 colors with codes from 0 to 7
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#These are the sequences need to get colored output
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ =  "\033[1m"

#The background is set with 40 plus the number of the color,
#and the foreground with 30
COLORS = {
    'WARNING':  COLOR_SEQ % (30 + YELLOW) + 'WARNING' + RESET_SEQ,
    'INFO':     COLOR_SEQ % (30 + WHITE) + 'INFO' + RESET_SEQ,
    'DEBUG':    COLOR_SEQ % (30 + BLUE) + 'DEBUG' + RESET_SEQ,
    'CRITICAL': COLOR_SEQ % (30 + YELLOW) + 'CRITICAL' + RESET_SEQ,
    'ERROR':    COLOR_SEQ % (30 + RED) + 'ERROR' + RESET_SEQ,
}

def log_traceback(log):
    output = StringIO.StringIO()
    exc = traceback.print_exc(file=output)

    log.error(output.getvalue())

class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        if self.use_color:
            record.levelname = COLORS.get(record.levelname, record.levelname)
        return logging.Formatter.format(self, record)


class GimPanelLogger(logging.Logger):
    COLOR_FORMAT = "[%(asctime)s]" + "[" + BOLD_SEQ + "%(name)s" + RESET_SEQ + \
                   "][%(levelname)s] %(message)s (" + BOLD_SEQ + \
                   "%(filename)s" + RESET_SEQ + ":%(lineno)d)"
    NO_COLOR_FORMAT = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s " \
                      "(%(filename)s:%(lineno)d)"
    LOG_FILE_HANDLER = None

    def __init__(self, name):
        logging.Logger.__init__(self, name)

        #Add two handlers, a stderr one, and a file one
        color_formatter = ColoredFormatter(GimPanelLogger.COLOR_FORMAT)
        no_color_formatter = ColoredFormatter(GimPanelLogger.NO_COLOR_FORMAT,
                                              False)

        #create the single file appending handler
        if GimPanelLogger.LOG_FILE_HANDLER == None:
            filename = os.path.join(CONFIG_ROOT, 'fcitx-gimpanel.log')
            GimPanelLogger.LOG_FILE_HANDLER = logging.FileHandler(filename, 'w')
            GimPanelLogger.LOG_FILE_HANDLER.setFormatter(no_color_formatter)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(GimPanelLogger.LOG_FILE_HANDLER)
        self.addHandler(console)
        return


def enable_debugging():
    logging.getLogger().setLevel(logging.DEBUG)


def disable_debugging():
    logging.getLogger().setLevel(logging.INFO)


def disable_logging():
    logging.getLogger().setLevel(logging.CRITICAL + 1)

logging.setLoggerClass(GimPanelLogger)

def log_func(log):
    def wrap(func):
        def func_wrapper(*args, **kwargs):
            log.debug("%s:" % func)
            for i, arg in enumerate(args):
                log.debug("\targs-%d: %s" % (i + 1, arg))
            for k, v in enumerate(kwargs):
                log.debug("\tdict args-%d: %s: %s" % (k, v, kwargs[v]))
            return func(*args, **kwargs)
        return func_wrapper
    return wrap
