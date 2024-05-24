'''
Takes a list of of arguments (object) and executes them in parallel.

The arguments object must have the following attributes:
		- metadata: a dictionary of metadata (retries, etc.)
    - args: a list of process arguments (first element is the path to the executable)
    
Scheduler will create workers which will execute the arguments in parallel. It will then monitor the workers outputs
and exit codes. If a worker fails, it will be restarted (up to max. number of retries). If a worker fails too many times, it will be removed from the
pool of workers. Once all of the tasks have been completed, the scheduler will exit.

The worker will also dynamically scale the maximum number of workers based on the number of remaining tasks and
resource usage (CPU, memory, etc.).
'''

# TODO: cleanup of this file - added loads of functionality and it's a bit of a mess now

# Some parts of this code are still a little janky, but the core functionality works.
# Known issues:
# - REPL uses input() which halts the main thread and prevents the threads from joining and exiting (use exit command to exit (or Ctrl+C))

import os
import sys
import json
import time
import subprocess
import psutil
import threading
import queue
import argparse
from datetime import datetime
from typing import Callable, Optional

# Project imports
sys.path.append(os.getcwd())
from src.py.utils.logger import Logger

#
##  Constants and globals
#
# TODO load from config file
config = {}
filepath_config = "src/py/utils/scheduler/scheduler_config.json"  # this is the default path - can be changed with a named argument
filepath_tasks = "src/py/utils/scheduler/scheduler_tasks.json"  # this is the default path - can be changed in the config file
filepath_log = "logs/scheduler.log"
script_start_time = time.time()
tasks_finished_at = None
workers_max = 5
# Tasks can be loaded at runtime from a file (if given a named argument tasks={filepath})
task_list = []  # type: list[dict]
# task_dict is updated with data from workers and saved to a file after a worker finishes (key = task handle, value = task object with updated metadata)
# filepath of the task_dict is the same as the filepath of the task_list with .scheduler_ prefix
# at the start try to load the task_dict if it exists
# it can be used to resume a previous session
# task_dict = {}  # type: dict[str, dict]
tasks_completed = 0  # all exited workers count as completed, successful = tasks_completed - tasks_failed
tasks_failed = 0  # all failed workers count as failed (exit with 0 retries left)
tasks_skipped = 0  # number of tasks that were skipped (conditions from task_dict_task)
tasks_failed_handles = []  # list of failed task handles
state = "init"  # can be "init", "running", "paused", "stopped"
# TODO add metadata time_limit, etc.

# using psutils to monitor resource usage and adjust the number of workers accordingly
utilization_settings = {
    # psutil.cpu_percent()
    "cpu": {
        "scale_down_threshold": 95,  # 85
        "scale_up_threshold": 50,  # 50
    },
    # dict(psutil.virtual_memory()._asdict())["percent"]
    "memory": {
        "scale_down_threshold": 90,  # 85
        "scale_up_threshold": 50,  # 50
    }
}

# Init logger - default
logger = Logger({
    "filepath": filepath_log,
    "level": "DEBUG",
})


def load_config(filepath: str = filepath_config) -> dict:
	'''
		Loads the scheduler config file.
	'''
	global config
	global logger
	config = {}
	logger.say(f"Loding config file: {filepath}")
	with open(filepath, "r") as f:
		config = json.load(f)
	# Reinit logger with config settings if (if given)
	if "filepath_log" in config:
		global filepath_log
		filepath_log = config["filepath_log"]
		logger.say(
		    f"Log file path loaded from config and set to '{filepath_log}' - reinitializing logger there."
		)
		logger.stop()  # needed to close the file handle
		logger = Logger({
		    "filepath": filepath_log,
		    "level": "DEBUG",
		})
	logger.say(f"Loaded config settings: {json.dumps(config, indent=2)}")
	# Load more config settings with the new logger initialized (if given)
	if "workers_max" in config:
		global workers_max
		workers_max = config["workers_max"]
		logger.say(f"Max. number of workers set to '{workers_max}'.")
	if "filepath_tasks" in config:
		global filepath_tasks
		filepath_tasks = config["filepath_tasks"]
		global task_list
		with open(config["filepath_tasks"], "r") as f:
			task_list = json.load(f)
		logger.say(f"Loaded tasks from '{config['filepath_tasks']}'.")
		# logger.say(f"Loaded tasks: {json.dumps(task_list, indent=2)}")
	return config


def get_dummy_task_list(num_tasks: int) -> list[dict]:
	'''
		Returns a list of dummy tasks.
	'''
	task_list = []
	for i in range(num_tasks):
		i_str = str(i + 1)
		while len(i_str) < len(str(num_tasks)):
			i_str = "0" + i_str
		handle = f"handle_{i_str}"
		task_list.append({
		    "metadata": {
		        "handle": handle,
		        "retries": 1,  # 3
		        "can_handle_output": False,
		        "can_handle_error": False
		    },
		    "args": ["python", "src/py/utils/scheduler/dummy_task.py"]
		})
	return task_list


def generate_dummy_task_list(num_tasks: int,
                             filepath: str = filepath_tasks) -> None:
	'''
		Generates a list of dummy tasks and saves it to a file.
	'''
	task_list = get_dummy_task_list(num_tasks)
	with open(filepath, "w") as f:
		json.dump(task_list, f, indent=2)


# For testing purposes
# task_list = get_dummy_task_list(10)
# n_tasks = 10000
# print(f"Generating {n_tasks} dummy tasks...")
# generate_dummy_task_list(n_tasks)
# print(f"Exiting... Comment this to resume normal script execution.")
# exit()


def validate_task(task: dict) -> bool:
	'''
		Validates a task object.
	'''
	if "metadata" not in task:
		logger.say("Task is missing metadata.")
		return False
	if "retries" not in task["metadata"]:
		task["metadata"]["retries"] = 0
		# logger.say("Task is missing retries.")
		# return False
	if "handle" not in task["metadata"]:
		logger.say("Task is missing handle.")
		return False
	if "args" not in task:
		logger.say("Task is missing args.")
		return False
	return True


def validate_tasks(tasks: list[dict]) -> bool:
	'''
		Validates a list of task objects.
	'''
	handles = {}  # handles must be unique
	for task in tasks:
		if not validate_task(task):
			return False
		if task["metadata"]["handle"] in handles:
			logger.say(f"Task handle '{task['metadata']['handle']}' is not unique.")
			return False
		handles[task["metadata"]["handle"]] = True
	return True


# def generate_task_dict(tasks: list[dict]) -> dict:
# 	'''
# 		Generates a task dict from a list of tasks.
# 	'''
# 	task_dict = {}
# 	for task in tasks:
# 		task_dict[task["metadata"]["handle"]] = task
# 	return task_dict

# def load_task_dict() -> dict:
# 	'''
# 		Loads the task dict from a file.
# 	'''
# 	filepath = filepath_tasks.replace(".json", ".scheduler.json")
# 	task_dict = {}
# 	if os.path.isfile(filepath):
# 		with open(filepath, "r") as f:
# 			task_dict = json.load(f)
# 	logger.say(f"Loaded task dict: {json.dumps(task_dict, indent=2)}")
# 	# check if any tasks are missing (new tasks added to task_list)
# 	for task in task_list:
# 		handle = task["metadata"]["handle"]
# 		if handle not in task_dict:
# 			task_dict[handle] = task
# 			logger.say(f"Added missing task '{handle}' to task dict.")
# 	return task_dict

# def save_task_dict():
# 	'''
# 		Saves the task dict to a file.
# 	'''
# 	filepath = filepath_tasks.replace(".json", ".scheduler.json")
# 	with open(filepath, "w") as f:
# 		# indentation is slow - you can format the file (in VS Code) later if needed
# 		# json.dump(task_dict, f, indent=2, default=str)
# 		json.dump(task_dict, f, default=str)
# 	return True


def get_filepath_progress(task_handle: str) -> str:
	'''
		Returns the filepath of the progress file for a task.
	'''
	folderpath = os.path.dirname(filepath_tasks)
	filepath_progress = os.path.join(folderpath, "scheduler_data",
	                                 task_handle + ".json")
	return filepath_progress


def load_task_progress(task_handle: str) -> Optional[dict]:
	'''
		Loads the task progress from a file.
	'''
	try:
		filepath_progress = get_filepath_progress(task_handle)
		# load json to dict
		if os.path.isfile(filepath_progress):
			with open(filepath_progress, "r") as f:
				task_info = json.load(f)
				# logger.say(f"Loaded task progress for '{task_handle}'")
				return task_info
	except Exception as e:
		pass
	return None


def save_task_progress(task_options: dict) -> bool:
	'''
		Saves the task progress to a file.
	'''
	try:
		task_handle = task_options["metadata"]["handle"]
		# logger.say(f"Saving task progress for '{task_handle}'...")
		filepath_progress = get_filepath_progress(task_handle)
		# create folder if it doesn't exist
		folderpath = os.path.dirname(filepath_progress)
		if not os.path.isdir(folderpath):
			os.makedirs(folderpath)
		# save dict to json
		with open(filepath_progress, "w") as f:
			json.dump(task_options, f, indent=2, default=str)
			logger.say(f"Saved task progress for '{task_handle}'")
			return True
	except Exception as e:
		pass
	return False


def print_resource_utilization():
	'''
		Prints the resource utilization (overall - not just this process)
	'''
	logger.say("Resource utilization:")
	logger.say(
	    f" - CPU utilization: {psutil.cpu_percent()}% over {psutil.cpu_count()} cores"
	)
	logger.say(
	    f" - Memory utilization: {psutil.virtual_memory().percent}% ({round(psutil.virtual_memory().used / 1024 / 1024, 3)} MB / {round(psutil.virtual_memory().total / 1024 / 1024, 3)} MB)"
	)
	logger.say(
	    f" - Disk utilization: {psutil.disk_usage('/').percent}% ({round(psutil.disk_usage('/').used / 1024 / 1024, 3)} MB / {round(psutil.disk_usage('/').total / 1024 / 1024, 3)} MB)"
	)
	logger.say(
	    f" - Network utilization: {round(psutil.net_io_counters().bytes_recv / 1024 / 1024, 3)} MB down, {round(psutil.net_io_counters().bytes_sent / 1024 / 1024, 3)} MB up"
	)


def test_print_resource_utilization():
	'''
		Tests the print_resource_utilization function.
	'''
	while True:
		print_resource_utilization()
		time.sleep(0.5)


class Worker:
	'''
		Represents a worker process.
	'''

	def init_thread_stdout(self):
		'''
			Initializes the stdout thread.
		'''
		if self.options["metadata"]["can_handle_output"]:
			self.thread_stdout = threading.Thread(target=self.handle_output)
			self.thread_stdout.start()

	def init_thread_stderr(self):
		'''
			Initializes the stderr thread.
		'''
		if self.options["metadata"]["can_handle_error"]:
			self.thread_stderr = threading.Thread(target=self.handle_error)
			self.thread_stderr.start()

	def start_process(self):
		'''
			Starts the worker process.
		'''
		# Print start message
		logger.say(
		    f"{datetime.now()} [{self.options['metadata']['handle']}] START")
		# Start process
		self.process = subprocess.Popen(self.options["args"],
		                                stdout=subprocess.PIPE,
		                                stderr=subprocess.PIPE,
		                                shell=False,
		                                universal_newlines=True)
		self.time_start = time.time()
		# Start threads
		self.init_thread_stdout()
		self.init_thread_stderr()
		self.thread_exit = threading.Thread(target=self.handle_exit)
		self.thread_exit.start()

	def stop_process(self):
		'''
			Stops the worker process.
		'''
		# Wait for threads to finish
		try:
			self.thread_stdout.join()
		except:
			pass
		try:
			self.thread_stderr.join()
		except:
			pass
		try:
			self.thread_exit.join()
		except:
			pass
		# Kill process
		try:
			self.process.kill()
		except:
			pass

	def clean_line(self, line: str) -> str:
		'''
			Removes the single trailing newline character from a line.
		'''
		return line[:-1]

	def handle_output(self):
		'''
			Handles the worker process output.
		'''
		assert self.process.stdout
		for line in iter(self.process.stdout.readline, ''):
			if not self.options["metadata"]["can_handle_output"]:
				break
			logger.say(
			    f"{datetime.now()} [{self.options['metadata']['handle']}] OUT: {self.clean_line(line)}"
			)

	def handle_error(self):
		'''
			Handles the worker process error.
		'''
		assert self.process.stderr
		for line in iter(self.process.stderr.readline, ''):
			if not self.options["metadata"]["can_handle_output"]:
				break
			logger.say(
			    f"{datetime.now()} [{self.options['metadata']['handle']}] ERR: {self.clean_line(line)}"
			)

	def handle_exit(self):
		'''
			Handles the worker process exit code.
		'''
		self.process.wait()
		exit_code = self.process.returncode
		if exit_code != 0:
			logger.say(
			    f"{datetime.now()} [{self.options['metadata']['handle']}] EXIT: with non-zero code {exit_code}"
			)
			if self.options["metadata"]["retries"] > 0:
				self.options["metadata"]["retries"] -= 1
				logger.say(
				    f"{datetime.now()} [{self.options['metadata']['handle']}] RETRY: {self.options['metadata']['retries']} retries left"
				)
				self.start_process()
				return
			else:
				global tasks_failed
				tasks_failed += 1
				tasks_failed_handles.append(self.options["metadata"]["handle"])
				logger.say(
				    f"Task failed: {self.options['metadata']['handle']} ({tasks_failed} failed in total)"
				)
		self.time_end = time.time()
		duration = self.time_end - self.time_start
		global tasks_completed
		tasks_completed += 1
		# Remove worker from workers dict
		del workers[self.options["metadata"]["handle"]]
		logger.say(
		    f"{datetime.now()} [{self.options['metadata']['handle']}] EXIT (FINAL): with code {exit_code} in {duration} seconds"
		)
		if "workerdata" not in self.options:
			self.options["workerdata"] = {}
		self.options["workerdata"]["exit_code"] = exit_code
		self.options["workerdata"]["duration"] = duration
		# Save task dict
		try:
			# save_task_dict()
			# TODO: save progress for each exit
			save_task_progress(self.options)
		except:
			pass

	# def __del__(self):
	# 	'''
	# 		Stops the worker process.
	# 	'''
	# 	self.stop_process()

	def __init__(self, options: dict):
		self.options = options


class ReplThread(threading.Thread):
	'''
		Represents a thread that runs the REPL.
	'''

	def __init__(self, callback: Callable):
		self.callback = callback
		super(ReplThread, self).__init__()
		self.start()

	def run(self):
		'''
			Runs the REPL.
		'''
		while True:
			if not self.is_alive():
				break
			try:
				self.callback(input("> "))
			except KeyboardInterrupt:
				pass
			time.sleep(0.1)


def print_failed_tasks():
	'''
		Prints the failed tasks.
	'''
	logger.say(f"Failed tasks: ({len(tasks_failed_handles)})")
	for handle in tasks_failed_handles:
		logger.say(f"  - {handle}")


# WARNING: be very careful when using repl - any exception will crash the script
# even though it's inside a try block - this is because the REPL is running in a
# separate thread and the exception is not caught by the main thread
def repl(user_input: str):
	'''
	Pseudo REPL for executing commands and getting info while the script is running.
	'''
	global state
	try:
		if user_input == "exit":
			# TODO: use a dedicated method for clean exit (stopping workers, etc.)
			# TODO: use state variable to "signal" to other threads???
			exit(123)
		elif user_input == "help":
			logger.say("Available commands:")
			logger.say("  - exit: exit the script")
			logger.say("  - help: print this message")
			logger.say("  - status: print stats")
			logger.say("  - fails: print failed tasks")
			logger.say("  - pause: pause the script")
			logger.say("  - resume: resume the script")
			logger.say("  - top: print resource utilization")
			logger.say("  - list: list all workers")
			logger.say("  - worker")
			logger.say("		- <handle> stop: stop a worker")
			logger.say("    - <handle> stdout <on/off>: toggle stdout for a worker")
			logger.say("    - <handle> stderr <on/off>: toggle stderr for a worker")
		elif user_input == "pause":
			if state != "stopped":
				logger.say(
				    "Pausing script (not starting any new workers)...\nType 'status' to check the number of active workers.\nOnce it reaches 0, you can safely save the VM state and resume the scheduler later.\nType 'resume' to resume the script once you're ready."
				)
				state = "paused"
			else:
				logger.say("Script is already stopped.")
		elif user_input == "resume":
			if state != "stopped":
				logger.say("Resuming script...")
				state = "running"
			else:
				logger.say("Script is already stopped.")
		elif user_input.startswith("worker"):
			parts = user_input.split(" ")
			if len(parts) < 3:
				logger.say("Missing argument.")
				return
			handle = parts[1]
			command = parts[2]
			if handle not in workers:
				logger.say(f"Worker '{handle}' not found.")
				return
			worker = workers[handle]
			if command == "stop":
				worker.stop_process()
			elif command == "stdout":
				if len(parts) < 4:
					logger.say("Missing argument.")
					return
				if parts[3] == "on":
					worker.options["metadata"]["can_handle_output"] = True
					worker.init_thread_stdout()
				elif parts[3] == "off":
					worker.options["metadata"]["can_handle_output"] = False
				else:
					logger.say("Invalid argument.")
					return
			elif command == "stderr":
				if len(parts) < 4:
					logger.say("Missing argument.")
					return
				if parts[3] == "on":
					worker.options["metadata"]["can_handle_error"] = True
					worker.init_thread_stderr()
				elif parts[3] == "off":
					worker.options["metadata"]["can_handle_error"] = False
				else:
					logger.say("Invalid argument.")
					return
		elif user_input == "list":
			logger.say("Available workers:")
			for handle, worker in workers.items():
				logger.say(
				    f"  - {handle} ; uptime: {time.time() - worker.time_start}s")
		elif user_input == "start":
			logger.say("Starting worker...")
			# TODO
		elif user_input == "stop":
			logger.say("Stopping worker...")
			# TODO
		elif user_input == "status":
			logger.say("Status:")
			logger.say(f"  - active workers: {len(workers)}")
			logger.say(f"  - total tasks: {len(task_list)}")
			logger.say(f"  - tasks completed: {tasks_completed}")
			logger.say(f"  - tasks successful: {tasks_completed - tasks_failed}")
			logger.say(f"  - tasks failed: {tasks_failed}")
			logger.say(f"  - tasks skipped: {tasks_skipped}")
			logger.say(
			    f"  - tasks remaining: {len(task_list) - tasks_completed - tasks_skipped}"
			)
			logger.say(f"  - tasks in queue: {tasks.qsize()}")
			logger.say(
			    f"  - script uptime: {time.time() - script_start_time}s (started at {datetime.fromtimestamp(script_start_time)})"
			)
		elif user_input == "fails":
			print_failed_tasks()
		elif user_input == "top":
			print_resource_utilization()
		else:
			logger.say("Unknown command. Type 'help' for a list of commands.")
	except KeyboardInterrupt:
		logger.say("An error occurred while interpreting your command.")


def get_args():
	'''
		Parses command line arguments.
	'''
	parser = argparse.ArgumentParser()
	parser.add_argument(
	    "-c",
	    "--config",
	    help="Path to config file",
	    default=filepath_config,
	)
	# parser.add_argument(
	#     "-v",
	#     "--verbose",
	#     help="Enable verbose logging",
	#     action="store_true",
	# )
	# parser.add_argument(
	#     "-d",
	#     "--debug",
	#     help="Enable debug logging",
	#     action="store_true",
	# )
	return parser.parse_args()


def ask_for_confirmation() -> bool:
	'''
		Asks the user for confirmation before starting the run.
	'''
	user_choice = input(
	    "Are you sure you want to start the run? [y/N] ").lower().strip()
	if user_choice == "y":
		return True
	return False


def main():
	# Time the main function
	time_start = time.time()
	# Read command line arguments
	args = get_args()
	if args.config:
		global filepath_config
		filepath_config = args.config
	# Load config - new logger might be created here
	load_config(filepath_config)
	# Ask for confirmation
	all_good = ask_for_confirmation()
	if not all_good:
		logger.say("User choosing not to start the run - exiting.")
		exit(203)
	# Print resource utilization
	print_resource_utilization()
	# Globals
	global workers
	global tasks
	global tasks_finished_at
	global state
	# If task are not valid, exit
	if not validate_tasks(task_list):
		logger.say("Invalid tasks given. Exiting.")
		exit(1)

	tasks = queue.Queue()
	for task in task_list:
		tasks.put(task)

	# Keys are worker handles, values are Worker objects
	workers = {}

	# TODO: Make this optional via args / config
	# Turn off prints for all tasks (can be turned on via REPL)
	# for task in task_list:
	# 	task["metadata"]["can_handle_output"] = False
	# 	task["metadata"]["can_handle_error"] = False

	# Print some info - how many tasks
	logger.say(f"Loaded {len(task_list)} tasks.")

	# REPL
	# start REPL in a separate thread so it doesn't block the main thread
	repl_thread = None  # type: ignore # type: ReplThread
	try:
		repl_thread = ReplThread(repl)
	except Exception as e:
		logger.say(f"An error occurred in the REPL thread: {e}")

	# Set state to "running"
	state = "running"

	# Init workers from tasks
	while not tasks.empty():
		if state != "running":  # this enables pausing the script (not starting any new workers)
			time.sleep(0.1)
			continue
		# Don't load more tasks if low on resources
		cpu_percent = (psutil.cpu_percent() / psutil.cpu_count()
		              )  # is this per logical core or cumulative?
		mem_percent = psutil.virtual_memory().percent
		if cpu_percent > utilization_settings["cpu"][
		    "scale_down_threshold"] or mem_percent > utilization_settings[
		        "memory"]["scale_down_threshold"]:
			sleep_time = 1.0
			logger.say(
			    f"CPU or memory utilization is too high ({cpu_percent}% CPU, {mem_percent}% memory). Not starting any more workers. Sleeping for {sleep_time}s."
			)
			time.sleep(sleep_time)
			continue
		# if number of workers is smaller to the number of tasks, create a new worker
		# otherwise wait for a worker to finish
		if len(workers) < workers_max:
			task = tasks.get()
			handle = task["metadata"]["handle"]
			# task_dict_task = task_dict[handle]
			task_progress = load_task_progress(handle)
			# If task progress exists, use it instead of the task from the task list
			if task_progress:
				logger.say(f"Loaded task progress for '{handle}'.")
				task = task_progress
			# when loading from task dict, we can start a task if it has no workerdata
			# or if it has workerdata and it has exit code != 0 and retries > 0
			if "workerdata" not in task or ("workerdata" in task and
			                                (task["workerdata"]["exit_code"] != 0 and
			                                 task["metadata"]["retries"] > 0)):
				worker = Worker(task)
				workers[worker.options["metadata"]["handle"]] = worker
				worker.start_process()
			else:
				logger.say(f"Task '{handle}' has already been processed. Skipping...")
				global tasks_skipped
				tasks_skipped += 1
		else:
			time.sleep(0.01)
	logger.say("Task queue is empty. Waiting for workers to finish...")
	while len(workers) > 0:
		time.sleep(0.1)
	tasks_finished_at = time.time()
	# Set state to "stopped"
	state = "stopped"
	# Print some info
	logger.say("All workers are done.")
	logger.say(f"Total time: {tasks_finished_at - script_start_time}s")
	# TODO: print stats
	logger.say("Stats:")
	logger.say(f"  - total tasks: {len(task_list)}")
	logger.say(f"  - tasks completed: {tasks_completed}")
	logger.say(f"  - tasks successful: {tasks_completed - tasks_failed}")
	logger.say(f"  - tasks failed: {tasks_failed}")
	logger.say(f"  - tasks skipped: {tasks_skipped}")
	logger.say(
	    f"  - tasks remaining: {len(task_list) - tasks_completed - tasks_skipped}"
	)
	# Print failed tasks
	print_failed_tasks()
	logger.say(
	    "Waiting for REPL thread to finish... (type 'exit' in the REPL or press Ctrl+C to force exit)"
	)
	# close REPL thread
	# doesn't work because it still waits for input()... how to read user input non-blocking?
	assert repl_thread
	repl_thread.join()
	# Print resource utilization
	print_resource_utilization()
	# Print time
	time_end = time.time()
	logger.say(f"Total runtime: {time_end - time_start}s")


if __name__ == "__main__":
	main()
	logger.say("ALL DONE")
