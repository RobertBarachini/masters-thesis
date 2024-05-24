# Script for testing the scheduler

import sys
import random
import time
from datetime import datetime

# TODO source from args
loops = 20
chance_to_error = 0.5  # chance to print to stderr
chance_to_exit = 0.056  # 0 to never get an exception, default 0.056
wait_bounds_lower = (0.01, 0.1)
wait_bounds_upper = (0.2, 0.7)

print(f"loops: {loops}")
print(f"chance_to_error: {chance_to_error}")
print(f"chance_to_exit: {chance_to_exit}")
print(f"wait_bounds_lower: {wait_bounds_lower}")
print(f"wait_bounds_upper: {wait_bounds_upper}")


def warmup():
	# warm up the random number generator
	for i in range(1000):
		random.random()


def get_random_float_between(lower: float, upper: float):
	return random.random() * (upper - lower) + lower


def get_wait_time():
	lower_bound = get_random_float_between(*wait_bounds_lower)
	upper_bound = get_random_float_between(*wait_bounds_upper)
	return get_random_float_between(lower_bound, upper_bound)


def loop(n: int):
	for i in range(n):
		if random.random() < chance_to_error:
			# print to stderr
			print(f"ERR loop {i} at {datetime.now()}", file=sys.stderr)
		else:
			# print to stdout
			print(f"OUT loop {i} at {datetime.now()}")
		time.sleep(get_wait_time())
		if random.random() < chance_to_exit:
			a = 0
			# raise an exception
			raise Exception("Something went wrong")


def main():
	warmup()
	loop(loops)


if __name__ == "__main__":
	main()
	print("ALL DONE")