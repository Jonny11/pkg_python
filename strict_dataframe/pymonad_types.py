# --------------------------------------------------------
# (c) Copyright 2014 by Jason DeLaat. 
# Licensed under BSD 3-clause licence.
# --------------------------------------------------------

# from pymonad.Container import *
# from pymonad.Reader import curry
from typing import TypeVar, Type, Dict, Set, Union, List, Generic, Any, Tuple, Callable

from .generic_types import *

class Container(object):
	""" Represents a wrapper around an arbitrary value and a method to access it. """

	def __init__(self, value):
		""" 
		Wraps the given value in the Container. 
		
		'value' is any arbitrary value of any type including functions.

		"""
		self.value = value
	
	def getValue(self):
		""" Returns the value held by the Container. """
		return self.value

	def __eq__(self, other):
		return self.value == other.value

class Functor(Container):
	""" Represents a type of values which can be "mapped over." """

	def __init__(self, value):
		""" Stores 'value' as the contents of the Functor. """
		super(Functor, self).__init__(value)

	def fmap(self, function): 
		""" Applies 'function' to the contents of the functor and returns a new functor value. """
		raise NotImplementedError("'fmap' not defined.")
	
	def __rmul__(self, aFunction):
		""" 
		The 'fmap' operator.
		The following are equivalent:

			aFunctor.fmap(aFunction)
			aFunction * aFunctor

		"""
		
		return self.fmap(aFunction)

	@classmethod
	def unit(cls, value):
		""" Returns an instance of the Functor with 'value' in a minimum context.  """
		raise NotImplementedError

def unit(aClass, value):
	""" Calls the 'unit' method of 'aClass' with 'value'.  """
	return aClass.unit(value)

class Applicative(Functor):
	"""
	Represents a functor "context" which contains a function as a value rather than
	a type like integers, strings, etc.

	"""

	def __init__(self, function):
		""" Stores 'function' as the functors value. """
		super(Applicative, self).__init__(function)

	def amap(self, functorValue):
		""" 
		Applies the function stored in the functor to the value inside 'functorValue'
		returning a new functor value.

		"""
		raise NotImplementedError

	def __and__(self, functorValue):
		""" The 'amap' operator. """
		return self.amap(functorValue)

class Monad(Applicative):
	"""
	Represents a "context" in which calculations can be executed.

	You won't create 'Monad' instances directly. Instead, sub-classes implement
	specific contexts. Monads allow you to bind together a series of calculations
	while maintaining the context of that specific monad.

	"""

	def __init__(self, value):
		""" Wraps 'value' in the Monad's context. """
		super(Monad, self).__init__(value)

	def bind(self, function):
		""" Applies 'function' to the result of a previous monadic calculation. """
		raise NotImplementedError

	def __rshift__(self, function):
		""" 
		The 'bind' operator. The following are equivalent:
			monadValue >> someFunction
			monadValue.bind(someFunction)

		"""
		if callable(function): 
			result = self.bind(function)
			if not isinstance(result, Monad): raise TypeError("Operator '>>' must return a Monad instance.")
			return result
		else:
			if not isinstance(function, Monad): raise TypeError("Operator '>>' must return a Monad instance.")
			return self.bind(lambda _: function)



# CurriedFunction = Callable[[Any],Any]

class Reader(Monad):
	""" Represents a Functor for functions allowing authors to map functions over other functions. """

	def __init__(self, functionOrValue) -> None:
		""" 
		Stores or creates a function as the Functor's value.

		If 'functionOrValue' is a function, it is stored directly.
		However, if it is a value -- 7 for example -- then a function taking a single argument
		which always returns that value is created and that function is stored as the Functor's 
		value.

		In general, you won't create 'Reader' instances directly. Instead use the @curry
		decorator when defining functions. 'Reader' may not function as expected if 
		non-curried functions are used.

		"""
		func: Callable

		if (callable(functionOrValue)):
			func = functionOrValue
		else:
			func = lambda _: functionOrValue

		super(Reader, self).__init__(func)

	def __call__(self, *args):
		"""
		Applies arguments to the curried function.

		Returns the result of the function if all arguments are passed. If fewer than
		the full argument set is passed in, returns a curried function which expects the
		remaining arguments. For example, a function 'func' which takes 3 arguments can be
		called in any of the following ways:
			func(1, 2, 3)
			func(1, 2)(3)
			func(1)(2, 3)
			func(1)(2)(3)

		"""
		value: Callable = self.getValue()
		# numArgs = len(args)

		# print(value.__code__.co_name)
		# print(value.__code__.co_argcount)
		# print(value.__code__.co_varnames)
		# print(value.__annotations__)
		# print(args)
		# print(value)
		for a in args:
			try: 
				value = value(a)
			except TypeError:
				raise TypeError("Too many arguments supplied to curried function.")

		if (callable(value)): 
			# if value is a function, it is a partially applied function
			return Reader(value)
		else: 
			# otherwise it's a value returned by a fully applied function
			return value

	def __mul__(self, func):
		return func.fmap(self)

	def fmap(self, aFunction):
		""" 
		Maps 'aFunction' over the function stored in the Functor itself.

		Mapping a function over another function is equivalent to function composition.
		In other words,
			composedFunc = curriedFunc1 * curriedFunc2
			composedFunc(parameter)
		is equivalent to
			composedFunc = lambda x: curriedFunc1(curriedFunc2(x))
			composedFunc(parameter)

		Both 'curriedFunc1' and 'curriedFunc2' must take only a single argument
		but either, or both, can be partially applied so they have only a single argument
		remaining.

		"""
		return Reader(lambda x: aFunction(self.getValue()(x)))
	
	def amap(self, functorValue):
		""" Applies function stored in the functor to 'functorValue' creating a new function. """
		return Reader(lambda x: self(x)(functorValue(x)))

	def bind(self, function):
		""" Threads a single value through multiple function calls. """
		return Reader(lambda x: function(self.getValue()(x))(x))

	@classmethod
	def unit(cls, value):
		return Reader(lambda _: value)

# def curry(aFunction: Callable[[]]) -> Callable[[]]:
def curry(aFunction: Callable):
	""" 
	Turns a normal python function into a curried function.

	Most easily used as a decorator when defining functions:
		@curry
		def add(x, y): return x + y

	"""
	# funcName = aFunction.__code__.co_name
	# numArgs = aFunction.__code__.co_argcount
	argTypes = aFunction.__annotations__
	argNames = aFunction.__code__.co_varnames 
	# print(argTypes)
	# print(argNames)
	def buildReader(argValues, numArgs): #argTypes
		if (numArgs == 0): 
			# if all arguments have been collected, 
			# call the original function (captured in closure) 
			# with the accumulated arguments (argValues):
			return aFunction(*argValues) 
		else:
			# else return a function that takes one function,
			# that partially applies function and returns a reader monad
			# that progressively asks for the remaining arguments:
			return lambda x: buildReader(argValues + [x], numArgs - 1)

	return Reader(buildReader(
			argValues = [], 
			numArgs   = aFunction.__code__.co_argcount
			# argTypes  = aFunction.__annotations__
	))


class Monoid(Container):
	"""
	Represents a data type which conforms to the following conditions:
	   1. Has an operation (called 'mplus') which combines two values of this type.
	   2. Has a value (called 'mzero') such that mplus(mzero, value) == mplus(value, mzero) = value.
	      In other words, mzero acts as an identity element under the mplus operation.
	   3. mplus is associative: mplus(a, mplus(b, c)) == mplus(mplus(a, b), c)

	   For instance, integers can be monoids in two ways: With mzero = 0 and mplus = + (addition)
	   or with mzero = 1 and mplus = * (multiplication).
	   In the case of strings, mzero = "" (the empty string) and mplus = + (concatenation).

	"""

	def __init__(self, value):
		""" Initializes the monoid element to 'value'.  """
		super(Monoid, self).__init__(value)
	
	def __add__(self, other):
		""" The 'mplus' operator.  """
		return self.mplus(other)

	@staticmethod
	def mzero():
		"""
		A static method which simply returns the identity value for the monoid type.
		This method must be overridden in subclasses to create custom monoids.
		See also: the mzero function.

		"""
		raise NotImplementedError

	def mplus(self, other):
		"""
		The defining operation of the monoid. This method must be overridden in subclasses
		and should meet the following conditions.
		   1. x + 0 == 0 + x == x
		   2. (x + y) + z == x + (y + z) == x + y + z
		Where 'x', 'y', and 'z' are monoid values, '0' is the mzero (the identity value) and '+' 
		is mplus.

		"""
		raise NotImplementedError

@curry
def mzero(monoid_type):
	"""
	Returns the identity value for monoid_type. Raises TypeError if monoid_type is not a valid monoid.

	There are a number of builtin types that can operate as monoids and they can be used as such
	as is. These "natural" monoids are: int, float, str, and list.
	While thee mzero method will work on monoids derived from the Monoid class,
	this mzero function will work for *all* monoid types, including the "natural" monoids.
	For this reason it is preferable to call this function rather than calling the mzero method directly
	unless you know for sure what type of monoid you're dealing with.

	"""
	try:
		return monoid_type.mzero()
	except AttributeError:
		if isinstance(monoid_type, int) or isinstance(monoid_type, float) or monoid_type == int or monoid_type == float:
			return 0
		elif isinstance(monoid_type, str) or monoid_type == str:
			return ""
		elif isinstance(monoid_type, list) or monoid_type == list:
			return []
		else:
			raise TypeError(str(monoid_type) + " is not a Monoid.")

@curry
def mconcat(monoid_list):
	"""
	Takes a list of monoid values and reduces them to a single value by applying the
	mplus operation to each all elements of the list.

	"""
	result = mzero(monoid_list[0])
	for value in monoid_list:
		result += value
	return result

class Maybe(Monad, Monoid, Generic[T]):
	""" 
	Represents a calculation which may fail. An alternative to using Exceptions. 
	'Maybe' is an abstract type and should not be instantiated directly. There are two types
	of 'Maybe' values: Just(something) and Nothing. 

	"""

	def __init__(self, value) -> None:
		"""
		Raises a NotImplementedError. 
		Do not create 'Maybe' values directly, use Just or Nothing instead.

		"""
		raise NotImplementedError("Can't create objects of type Maybe: use Just(something) or Nothing.")

	def __eq__(self, other):
		if not isinstance(other, Maybe): raise TypeError("Can't compare two different types.")

	@classmethod
	def unit(cls, value):
		""" Injects 'value' into the Maybe monad.  """
		return Just(value)

	@staticmethod
	def mzero():
		""" Returns the identity element (Nothing) for the Maybe Monoid.  """
		return Nothing

class Just(Maybe[T]):
	""" The 'Maybe' type used to represent a calculation that has succeeded. """

	def __init__(self, value:T) -> None:
		"""
		Creates a Just value representing a successful calculation.
		'value' can be any type of value, including functions.

		"""
		super(Maybe, self).__init__(value)

	def __str__(self):
		return "Just " + str(self.getValue())

	def __eq__(self, other):
		super(Just, self).__eq__(other)
		if isinstance(other, _Nothing): return False
		elif (self.getValue() == other.getValue()): return True
		else: return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def fmap(self, function):
		""" Applies 'function' to the 'Just' value and returns a new 'Just' value. """
		return Just(function(self.getValue()))

	def amap(self, functorValue):
		""" 
		Applies the function stored in the functor to the value of 'functorValue',
		returning a new 'Just' value.

		"""
		return self.getValue() * functorValue

	def bind(self, function):
		""" Applies 'function' to a 'Just' value.
		'function' must accept a single argument and return a 'Maybe' type,
		either 'Just(something)' or 'Nothing'.

		"""
		return function(self.getValue())

	def mplus(self, other):
		"""
		Combines Maybe monoid values into a single monoid value.
		The Maybe monoid works when the values it contains are also monoids
		with a defined mzero and mplus. This allows you do things like:
			Just(1) + Just(9) == Just(10)
			Just("Hello ") + Just("World") == Just("Hello World")
			Just([1, 2, 3]) + Just([4, 5, 6]) == Just([1, 2, 3, 4, 5, 6])
		etc. 

		The identity value is 'Nothing' so:
			Just(1) + Nothing == Just(1)

		"""
		if other == Nothing: return self
		else: return Just(self.value + other.value)

class _Nothing(Maybe):
	""" The 'Maybe' type used to represent a calculation that has failed. """
	def __init__(self, value=None):
		super(Maybe, self).__init__(value)

	def __str__(self):
		return "Nothing"

	def __eq__(self, other):
		super(_Nothing, self).__eq__(other)
		if isinstance(other, _Nothing): return True
		else: return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def fmap(self, _):
		""" Returns 'Nothing'. """
		return self

	def amap(self, _):
		""" Returns 'Nothing'. """
		return self

	def bind(self, _):
		""" Returns 'Nothing'. """
		return self

	def mplus(self, other):
		"""
		Combines Maybe monoid values into a single monoid value.
		The Maybe monoid works when the values it contains are also monoids
		with a defined mzero and mplus. This allows you do things like:
			Just(1) + Just(9) == Just(10)
			Just("Hello ") + Just("World") == Just("Hello World")
			Just([1, 2, 3]) + Just([4, 5, 6]) == Just([1, 2, 3, 4, 5, 6])
		etc. 

		The identity value is 'Nothing' so:
			Just(1) + Nothing == Just(1)

		"""
		return other

Nothing = _Nothing()

class First(Monoid):
	"""
	A wrapper around 'Maybe' values, 'First' is a monoid intended to make it easy to
	find the first non-failure value in a collection of values which may fail.

	"""
	def __init__(self, value):
		"""
		Only accepts instances of the 'Maybe' monad for value. Raises 'TypeError' if
		any other type of value is passed.

		"""
		if not isinstance(value, Maybe): raise TypeError
		else: super(First, self).__init__(value)
	
	def __str__(self):
		return str(self.value)

	@staticmethod
	def mzero():
		""" Returns the identity element (First(Nothing)) for the Maybe Monoid.  """
		return First(Nothing)

	def mplus(self, other):
		"""
		Returns the first encountered non-failure value if it exists. Returns 
		First(Nothing) otherwise.

		"""
		if isinstance(self.value, Just): return self
		else: return other

class Last(Monoid):
	"""
	A wrapper around 'Maybe' values, 'Last' is a monoid intended to make it easy to
	find the final non-failure value in a collection of values which may fail.

	"""
	def __init__(self, value):
		"""
		Only accepts instances of the 'Maybe' monad for value. Raises 'TypeError' if
		any other type of value is passed.

		"""
		if not isinstance(value, Maybe): raise TypeError
		else: super(Last, self).__init__(value)
	
	def __str__(self):
		return str(self.value)

	@staticmethod
	def mzero():
		""" Returns the identity element (Last(Nothing)) for the Maybe Monoid.  """
		return First(Nothing)

	def mplus(self, other):
		"""
		Returns the last non-failure value encountered if it exists. Returns 
		Last(Nothing) otherwise.

		"""
		if isinstance(other.value, Just): return other
		else: return self
