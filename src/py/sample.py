from datetime import datetime


def sum(a: int, b: int) -> int:
	return a + b


def get_time() -> datetime:
	return datetime.now()


def main() -> None:
	print(f"Time is {get_time()}")
	print(f"Sum of 1 and 2 is {sum(1, 2)}")


if __name__ == "__main__":
	main()
	print("ALL DONE:^)")
