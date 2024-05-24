# This file is used to simulate a heavy task that will be executed by the scheduler.
# It will run for a long time and consume a lot of CPU and RAM and have a small chance to end.
# Used for testing the scheduler's ability to adjust / limit the number of workers based on the load.

import random
import psutil

bignum = 0
huge_memory_dump = [42.0, 42.0]
chance_to_break = 0.0000001
ram_limit = 85  # 85
time_to_end = False

while True:
	# CPU
	for i in range(1000):
		bignum += 1
		# small chance to break
		if random.random() < chance_to_break:
			time_to_end = True
			break

	if time_to_end:
		break

	# RAM (basic)
	if psutil.virtual_memory().percent < ram_limit:
		huge_memory_dump.extend([42.0] * 10000 * 5)

	# RAM (extreme)
	# if psutil.virtual_memory().percent < ram_limit:
	# 	huge_memory_dump.append([huge_memory_dump[:],
	# 	                         random.randint(1, 1000000)])  # type: ignore

	# RAM (extreme)
	# if psutil.virtual_memory().percent < ram_limit:
	# 	# arr_to_add is half of the current huge_memory_dump
	# 	arr_to_add = huge_memory_dump[:len(huge_memory_dump)//2]
	# 	huge_memory_dump.extend(arr_to_add)

print(f"bignum: {bignum}")
print(f"len(huge_memory_dump): {len(huge_memory_dump)}")