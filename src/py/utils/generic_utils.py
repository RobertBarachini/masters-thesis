# Generic utility functions

from typing import Any, Callable, TypeVar, Tuple, Union

T = TypeVar('T')


def wrapper(func: Callable[..., T], *args: Any,
            **kwargs: Any) -> Tuple[T, None] | Tuple[None, Exception]:
	'''
	Wrapper function for catching exceptions
	:param func: Function to call
	:param args: Arguments to pass to the function
	:param kwargs: Keyword arguments to pass to the function
	:return: Tuple with the result of the function call and the exception

	Example:
	>>> def return_str(items: List[str]) -> List[str]:
	...     if len(items) == 0:
	...         raise Exception("Empty list")
	...     return items
	...
	>>> result_tuple_1 = wrapper(return_str, ['apple', 'banana', 'cherry'])
	>>> result_1, error_1 = result_tuple_1
	>>> result_tuple_2 = wrapper(return_str, [])
	>>> result_2, error_2 = result_tuple_2
	>>> print(type(result_1))  # <class 'list'>
	>>> print(type(result_2))  # <class 'NoneType'>
	>>> print(type(error_1))  # <class 'NoneType'>
	>>> print(type(error_2))  # <class 'Exception'>
	
	For more details see:
	test_linter.py
	'''
	try:
		result = func(*args, **kwargs)
		return result, None
	except Exception as e:
		return None, e


# Example usage (typing is supported):
# import requests
# google_response, google_error = wrapper(requests.get, 'https://google.com')
