import os
import logging
import json
from typing import Optional


def get_logger(options: dict) -> logging.Logger:
	if "filepath" not in options:
		raise Exception("Missing filepath in options")
	if not os.path.exists(os.path.dirname(options["filepath"])):
		os.makedirs(os.path.dirname(options["filepath"]))
	if "level" not in options:
		options["level"] = "INFO"
	if "formatter" not in options:
		options["formatter"] = logging.Formatter(
		    '%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
		    datefmt='%Y-%m-%d %H:%M:%S')
	handler = logging.FileHandler(options["filepath"],
	                              mode="a+",
	                              encoding="utf-8")
	handler.setFormatter(options["formatter"])
	logger = logging.getLogger(options["filepath"])
	logger.setLevel(options["level"])
	logger.addHandler(handler)
	logger.info("=============================================================")
	logger.info(
	    f"Starting logger with options: {json.dumps(options, indent=2, sort_keys=True, default=str)}"
	)
	return logger


def stop_logger(logger: logging.Logger):
	for handler in logger.handlers[:]:
		try:
			handler.close()
			logger.removeHandler(handler)
		except Exception as e:
			print(f"Exception while closing logger handler: {e}")


def say(message: str, logger: logging.Logger, level: Optional[str] = "INFO"):
	if level is None:
		level = "INFO"
	level = level.upper()
	if level == "INFO":
		logger.info(message)
	elif level == "DEBUG":
		logger.debug(message)
	elif level == "WARNING":
		logger.warning(message)
	elif level == "ERROR":
		logger.error(message)
	elif level == "CRITICAL":
		logger.critical(message)
	else:
		logger.info(message)
	print(message, flush=True)


def test_get_logger():
	options = {
	    "filepath":
	        "logs/test.log",
	    "level":
	        "DEBUG",
	    "formatter":
	        logging.Formatter(
	            '%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
	            datefmt='%Y-%m-%dT%H:%M:%S')
	}
	logger = get_logger(options)
	logger.info("(LOGGER 1) INFO message")
	logger.debug("(LOGGER 1) DEBUG message")
	# only need to stop the logger when you're done with the logger and want to reuse it (in the same file)
	stop_logger(logger)
	logger = get_logger({"filepath": "logs/test.log"})
	logger.info("(LOGGER 2) INFO message")
	logger.debug("(LOGGER 2) DEBUG message (option 2)")


def test_say():
	logger = get_logger({"filepath": "logs/test.log", "level": "DEBUG"})
	say("(SAY) INFO message 1", logger)
	say("(SAY) INFO message 2", logger, "INFO")
	say("(SAY) DEBUG message", logger, "DEBUG")
	say("(SAY) WARNING message", logger, "WARNING")
	say("(SAY) ERROR message", logger, "ERROR")
	say("(SAY) CRITICAL message", logger, "CRITICAL")


class Logger():
	'''Logger class that wraps the logger and provides a methods for convenience'''

	def __init__(self, options: dict):
		# pass in "typeinit" to skip the init
		# (useful when you want to set it as a placeholder variable so that type hinting works)
		if "typeinit" in options:
			return
		self.options = options
		self.logger = get_logger(options)

	def say(self, message: str, level: Optional[str] = "INFO"):
		say(message, self.logger, level)

	def info(self, message: str):
		self.say(message, "INFO")

	def error(self, message: str):
		self.say(message, "ERROR")

	def debug(self, message: str):
		self.say(message, "DEBUG")

	def warning(self, message: str):
		self.say(message, "WARNING")

	def critical(self, message: str):
		self.say(message, "CRITICAL")

	def stop(self):
		stop_logger(self.logger)

	# def __del__(self):
	# 	self.stop()


def test_Logger():
	logger = Logger({"filepath": "logs/test.log", "level": "DEBUG"})
	logger.say("(LOGGER) INFO message 1")
	logger.say("(LOGGER) INFO message 2", "INFO")
	logger.say("(LOGGER) DEBUG message", "DEBUG")
	logger.say("(LOGGER) WARNING message", "WARNING")
	logger.say("(LOGGER) ERROR message", "ERROR")
	logger.say("(LOGGER) CRITICAL message", "CRITICAL")
	logger.stop()
	logger = Logger({"filepath": "logs/test.log"})
	logger.say("(LOGGER 2) INFO message 1")
	logger.say("(LOGGER 2) INFO message 2", "INFO")
	logger.say("(LOGGER 2) DEBUG message", "DEBUG")
	logger.say("(LOGGER 2) WARNING message", "WARNING")
	logger.say("(LOGGER 2) ERROR message", "ERROR")
	logger.say("(LOGGER 2) CRITICAL message", "CRITICAL")
	logger.stop()
	logger = Logger({"filepath": "logs/test.log", "level": "DEBUG"})
	logger.say("(LOGGER 3) SAY message 1")
	logger.info("(LOGGER 3) INFO message 1")
	logger.debug("(LOGGER 3) DEBUG message 1")
	logger.warning("(LOGGER 3) WARNING message 1")
	logger.error("(LOGGER 3) ERROR message 1")
	logger.critical("(LOGGER 3) CRITICAL message 1")


if __name__ == "__main__":
	# print(f"Testing get_logger()")
	# test_get_logger()
	# print(f"Testing say()")
	# test_say()
	print(f"Testing Logger()")
	test_Logger()
	print("ALL DONE")