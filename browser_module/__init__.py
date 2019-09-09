__all__ = [
	
	# selenium
	'By',
	'Expect',

	# browser_types
	'WebDriver',
	'WebElement',
	'BrowserValue',
	'WebElementSignature',
	'BrowserSessionLogsDataFrame',
	'BrowserSessionLog',
	'SafeWebDriver',
	'ChromeWebDriver',
	'SafeWebElement',
	'BrowserSession',

	# browser_module
	'Seconds',
	'R',
	'DriverFunction',
	'ElementFunction',
	'BrowserFunction',
	'MonadicBrowserFunction',
	'BlankSafeWebElement',
	'FunctionDictionary',
	'compose',
	'build',
	'Do'
]

# Let users know if they're missing any of our hard dependencies
hard_dependencies = ("typing", "functools", "selenium", "sys", "pandas", "enum", "strict_dataframe")
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

# Internal Imports
from .browser_types import *
from .browser_module import *
