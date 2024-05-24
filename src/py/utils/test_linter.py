from typing import Any, Callable, List, TypeVar, Tuple, Union

T = TypeVar('T')


def wrapper(func: Callable[..., T], *args: Any,
            **kwargs: Any) -> Union[Tuple[T, None], Tuple[None, Exception]]:
	try:
		result = func(*args, **kwargs)
		return result, None
	except Exception as e:
		return None, e


# Example for calling the wrapper function with a function that returns a list
# while preserving the type of the list (inferred from the function signature)
def return_str(items: List[str]) -> List[str]:
	if len(items) == 0:
		raise Exception("Empty list")
	return items


def add_int_1(items: Union[List[int], None]) -> List[int]:
	if items is None:
		raise Exception("Empty list")
	items_copy = items.copy()
	items_copy.append(42)
	return items_copy


def add_str_1(items: Union[List[str], None]) -> List[str]:
	if items is None:
		raise Exception("Empty list")
	items_copy = items.copy()
	items_copy.append('42')
	return items_copy


def add_str_2(items: List[str]) -> List[str]:
	items_copy = items.copy()
	items_copy.append('42')
	return items_copy


# Call the return_str function using the wrapper
# result_tuple_1 inferred return type: (variable) result: Tuple[List[str], None] | Tuple[None, Exception]
# Here we see the correctly inferred List[str] type
result_tuple_1 = wrapper(return_str, ['apple', 'banana', 'cherry'])
result_1, error_1 = result_tuple_1
result_tuple_2 = wrapper(return_str, [])
result_2, error_2 = result_tuple_2
# Check the type of the result variable
print(type(result_1))  # <class 'list'>
print(type(result_2))  # <class 'NoneType'>
# Check the type of the error variable ((variable) error: None | Exception)
print(type(error_1))  # <class 'NoneType'>
print(type(error_2))  # <class 'Exception'>
# Check if we get a linter warning
added_list = add_int_1(result_1)  # Linter warning
# Check if we get a linter warning
added_list = add_str_1(result_1)  # No linter warning
# Check if we get a linter warning
added_list = add_str_2(result_1)  # Linter warning
if added_list == None:
	added_list = []
# Check if we get a linter warning again
added_list = add_str_2(result_1)  # Still a lint warning...
# Solve with a type check
if type(result_1) == list:
	added_list = add_str_2(result_1)
# Solve with an assert
assert type(result_1) == list
added_list = add_str_2(result_1)
# Solve with an ignore
added_list = add_str_2(result_1)  # type: ignore
