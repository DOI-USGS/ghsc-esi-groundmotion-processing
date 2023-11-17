"""Module for handling logging."""

import logging
import logging.config


def setup_logger(args=None, level="info", log_file=None, error_dict={}):
    """Setup the logger options.

    This is written to handle a few different situations. It is called by
    command line programs that will hand off the args object. However, it
    may also be used for interactive sessions/notebooks where we want to
    suppress warnings, especially those from dependencies that are out of
    our control. For this, the args object is not available and will be None,
    and we then control the logging verbosity with the level argument (only
    used if args is None).

    Args:
        args (argparse):
            Must contain logging options in gmprocess.args.add_shared_args.
        level (str):
            String indicating logging level; either 'info', 'debug', or
            'error'. Only used if args in None.
        log_file (str):
            Path to send logging to.

    """
    # Have the logger capture anything from the 'warnings' package,
    # which many libraries use.
    logging.captureWarnings(True)

    if log_file == "external":
        return

    fmt = "%(levelname)s %(asctime)s | " "%(module)s.%(funcName)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    # create a console handler, with verbosity setting chosen by user
    if args is not None:
        if args.debug:
            loglevel = logging.DEBUG
        elif args.quiet:
            loglevel = logging.ERROR
        else:
            loglevel = logging.INFO
    else:
        if level == "debug":
            loglevel = logging.DEBUG
        elif level == "info":
            loglevel = logging.INFO
        elif level == "error":
            loglevel = logging.ERROR
        else:
            raise ValueError("Not valid level.")

    logdict = {
        "version": 1,
        "formatters": {"standard": {"format": fmt, "datefmt": datefmt}},
        "loggers": {"": {"handlers": [], "level": loglevel, "propagate": True}},
    }
    if log_file is None:
        logdict["handlers"] = {
            "stream": {
                "level": loglevel,
                "formatter": "standard",
                "class": "logging.StreamHandler",
            }
        }
        logdict["loggers"][""]["handlers"] = ["stream"]
    else:
        logdict["handlers"] = {
            "event_file": {
                "filename": log_file,
                "level": loglevel,
                "formatter": "standard",
                "class": "logging.FileHandler",
            }
        }
        logdict["loggers"][""]["handlers"] = ["event_file"]

    # handle smtp logging
    if "mail_host" in error_dict and error_dict["mail_host"] != "None":
        smtp_handler_key = "error_notification"
        smtp_handler = {
            "level": "CRITICAL",
            "formatter": "standard",
            "class": "logging.handlers.SMTPHandler",
            "mailhost": error_dict["mail_host"],
            "fromaddr": error_dict["from_address"],
            "toaddrs": error_dict["to_addresses"],
            "subject": error_dict["subject"],
        }
        logdict["handlers"][smtp_handler_key] = smtp_handler
        logdict["loggers"][""]["handlers"].append(smtp_handler_key)

    logging.config.dictConfig(logdict)
