import os
import shutil
from typing import Optional

path_trash = "~/.trash"


def can_move_file(path: str) -> bool:
	'''
		Checks whether the file can be moved to the trash folder
	'''
	return os.path.isfile(path)


def get_trash_path(path: str) -> str:
	'''
		Returns the path of the file in the trash folder
	'''
	# Expand both paths
	path_expanded = os.path.expanduser(path)
	path_trash_expanded = os.path.expanduser(path_trash)
	# Get absolute paths
	path_absolute = os.path.abspath(path_expanded)
	path_trash_absolute = os.path.abspath(path_trash_expanded)
	# Remove / from the start of path_absolute if it exists
	if path_absolute.startswith("/"):
		path_absolute = path_absolute[1:]
	path_trash_final = os.path.join(str(path_trash_absolute), str(path_absolute))
	return path_trash_final


def move_to_trash(path: str) -> Optional[Exception]:
	'''
		Moves the file to the trash folder

		Currently only files are supported for safety reasons
	'''
	if not can_move_file(path):
		return Exception(f"File '{path}' does not exist")
	try:
		path_extended = get_trash_path(path)
		path_extended_dirname = os.path.dirname(path_extended)
		if not os.path.exists(path_extended_dirname):
			os.makedirs(path_extended_dirname)
		shutil.move(path, path_extended)
		return None
	except Exception as e:
		return e


def create_trash_file():
	with open("TRASH_FILE.txt", "w") as f:
		from datetime import datetime
		f.write(f"This is a trash file created at: {datetime.now()}")


def test_move_to_trash():
	print("Testing move_to_trash()")
	print("Creating trash file...")
	create_trash_file()
	print("Moving trash file to trash folder...")
	err = move_to_trash("TRASH_FILE.txt")
	if err:
		print(err)
		return
	print("Trash file moved successfully")


if __name__ == "__main__":
	test_move_to_trash()
	print("All done!")
