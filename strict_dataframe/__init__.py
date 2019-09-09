__all__ = [
	# generic_types 
	'T',

	# # typing
	# 'TypeVar',
	# 'Type',
	# 'Dict',
	# 'Set',
	# 'Union',
	# 'List',
	# 'Generic',
	# 'Any',
	# 'Tuple',
	# 'Callable',

	# pymonad_types
	'Container',
	'Functor',
	'Applicative',
	'Monad',
	'Reader',
	'curry',
	'Monoid',
	'Maybe',
	'Just',
	'Nothing',
	'First',
	'Last',

	# dataframe_types
	'DataFrame',
	'BasicType',
	'TypeDict',
	'StringList',
	'StringSet',
	'StringTypeTupleList',
	'Printable',
	'CumulativeMonoidSet',
	'StrictDataFrame',
	'HasStrictDataframe'
]


# Let users know if they're missing any of our hard dependencies
hard_dependencies = ("typing", "abc", "pandas", "numpy")
missing_dependencies = []

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append("{0}: {1}".format(dependency, str(e)))

if missing_dependencies:
    raise ImportError(
        "Unable to import required dependencies:\n" + "\n".join(missing_dependencies)
    )
del hard_dependencies, dependency, missing_dependencies

from .generic_types import *
from .pymonad_types import *
from .dataframe_types import *