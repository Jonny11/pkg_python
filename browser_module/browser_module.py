# __________________________________________________________________________________________
# DEPENDENCIES
# from pymonad_types import *
from strict_dataframe import curry
from typing import TypeVar, Callable, Tuple, Dict, List
from .browser_types import WebDriver, WebElement, SafeWebDriver, BrowserSessionLog, CumulativeMonoidSet, SafeWebElement \
    , BrowserValue, BrowserSession, Nothing, Printable, WebElementSignature, Just, WebDriverWait, BrowserSessionLogsDataFrame \
    , DataFrame

from functools import reduce
import time

import selenium
# from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as Expect
from selenium.webdriver.common.by import By as by

# __________________________________________________________________________________________
# MAKE IMPORTED CLASSES TYPE-CHECKABLE (HACK)
# # Wrap By via inheritence so that the individual attributes
# used can be statically type-checked
# class By(by): pass # <- satisfied by browser_types
# class WebDriver(selenium.webdriver.remote.webdriver.WebDriver): pass # <- satisfied by browser_types
# class WebElement(selenium.webdriver.remote.webelement.WebElement): pass # <- satisfied by browser_types 
# __________________________________________________________________________________________
# NAMED TYPES
Seconds = int
R = TypeVar('R')
DriverFunction = Callable[[WebDriver], R]
ElementFunction = Callable[[WebElement], R]
BrowserFunction = Callable[[SafeWebDriver, BrowserSessionLog, CumulativeMonoidSet, SafeWebElement], BrowserValue]
MonadicBrowserFunction = Callable[[BrowserValue], BrowserSession]
BlankSafeWebElement = SafeWebElement(Nothing)
FunctionDictionary = Dict[str, Callable]

# class DriverFunction(Generic[T]):
#     pass


# __________________________________________________________________________________________
# FUNCTIONS
def _browserSessionLogEntry(step: str, log: str) -> BrowserSessionLog:
    return BrowserSessionLog(
        BrowserSessionLogsDataFrame(
            DataFrame.from_dict({
                'step': [step],
                'log': [log]}
            )
        )
    )

def _compose(functions: List[MonadicBrowserFunction]) -> MonadicBrowserFunction:
    def __compose(f1: MonadicBrowserFunction, f2: MonadicBrowserFunction) -> MonadicBrowserFunction:
        return lambda browser_value: f1(browser_value) >> f2
    return reduce(__compose, functions + [BrowserSession.unit])

def _driverFunction_to_browserFunction(function: DriverFunction[SafeWebElement]) -> BrowserFunction:
    def __impure__applyDriverFunction(
        driver: SafeWebDriver, 
        logs: BrowserSessionLog, 
        data: CumulativeMonoidSet, 
        element: SafeWebElement
    ) -> BrowserValue:
        new_element = driver.apply(function)
        next_element = SafeWebElement(Nothing) if(new_element == Nothing) else new_element.getValue()
        return (driver, logs, data, next_element) 
     
    return __impure__applyDriverFunction

def _elementFunction_to_browserFunction(function: ElementFunction[SafeWebElement]) -> BrowserFunction:
    def __impure__applyDriverFunction(
        driver: SafeWebDriver, 
        logs: BrowserSessionLog, 
        data: CumulativeMonoidSet, 
        element: SafeWebElement
    ) -> BrowserValue:
        new_element = element.apply(function)
        next_element = SafeWebElement(Nothing) if(new_element == Nothing) else new_element.getValue()
        return (driver, logs, data, next_element) 
     
    return __impure__applyDriverFunction

def _asLoggedBrowserAction(name: str, function: BrowserFunction, ignore_error_flag: bool = False) -> MonadicBrowserFunction:

    def __impure__browserAction(browser_value: BrowserValue) -> BrowserSession:
        driver, logs, data, element = browser_value
        driver_was_usable = driver.isUsable()
        driver_was_effectively_usable = driver.isUsable(ignore_error=ignore_error_flag)
        driver, logs, data, element = function(driver, logs, data, element)
 
        if driver_was_usable == driver.isUsable():
            new_log_message = "Complete" if driver_was_effectively_usable else "Skipped"  
        else: 
            new_log_message = "Browser became unusable"

        print(name + "..." + new_log_message)
        
        new_log = _browserSessionLogEntry(step=name, log=new_log_message)
        return BrowserSession(driver = driver, logs = logs + new_log, data = data, element = element)

    return __impure__browserAction

def _closeBrowser(driver: SafeWebDriver, logs: BrowserSessionLog, data: CumulativeMonoidSet, element: SafeWebElement) -> BrowserValue:
    driver.apply(function = lambda handle: Just(handle.quit()), ignore_error_flag = True)
    return (driver, logs, data, SafeWebElement(Nothing))

def _disregardError(driver: SafeWebDriver, logs: BrowserSessionLog, data: CumulativeMonoidSet, element: SafeWebElement) -> BrowserValue:
    driver.setError(set_error_to = False)
    return (driver, logs, data, element) 

def _doNothing(this: WebElementSignature) -> MonadicBrowserFunction:
    # this function does nothing, it exists to be used as save default value of 'then' monadic functions
    def __doNothing(browser_value: BrowserValue) -> BrowserSession:
        driver, logs, data, element = browser_value
        return BrowserSession(driver, logs, data, element)
    return __doNothing

def _getSafeWebElement(find: WebElementSignature, using: WebDriver) -> SafeWebElement:
    # use 'find_elements' as safe way of searching for unique element
    results = using.find_elements(by=find[0], value=find[1])
    if(len(results) != 1):
        # either no matching element found, or non unique results found
        return SafeWebElement(Nothing)
    else:
        return SafeWebElement(Just(results[0]))

def _buildDriverFunction_goToUrl(url: str) -> DriverFunction[SafeWebElement]:
    def __impure__goToUrl(driver: WebDriver) -> SafeWebElement:
        driver.get(url)
        return BlankSafeWebElement
    return __impure__goToUrl

def _debug_unwrapSafeElementValue(safe_element: SafeWebElement) -> WebElement:
    def __extractElement(element: WebElement) -> WebElement:
        return element
    return safe_element.apply(__extractElement).getValue()


# __________________________________________________________________________________________
# EXPORT SELECT UTILITY FUNCTIONS

compose = _compose 

build: Dict[str, FunctionDictionary] = {
    'driver_function': {
        'go_to_url': _buildDriverFunction_goToUrl
    }
}

class Do:

    # NON-PARAMETRIC FUNCTIONS
    closeBrowser = _asLoggedBrowserAction(name="closeBrowser", function=_closeBrowser, ignore_error_flag=True)
    disregardError = _asLoggedBrowserAction(name = "disregardError", function = _disregardError)

    # PARAMETRIC FUNCTIONS
    @staticmethod
    def goToUrl(url: str) -> MonadicBrowserFunction:
        return _asLoggedBrowserAction(
            name = "goToUrl("+url+")", 
            function = _driverFunction_to_browserFunction(_buildDriverFunction_goToUrl(url))
        )

    @staticmethod
    @curry
    def sendKeys(keys: str, to: WebElementSignature) -> MonadicBrowserFunction:
        # TODO: should return element to which the keys were sent?
        def __impure__sendKeysViaElement(elem: WebElement) -> None:
            elem.send_keys(keys)
        def __impure__sendKeysViaDriver(driver: WebDriver) -> SafeWebElement:
            input_element = _getSafeWebElement(find=to, using=driver)
            input_element.apply(__impure__sendKeysViaElement)
            return input_element
        return _asLoggedBrowserAction(
            name = "sendKeys(" + str(to) + ")", 
            function = _driverFunction_to_browserFunction(__impure__sendKeysViaDriver)
        )

    @staticmethod
    def wait(seconds: int) -> MonadicBrowserFunction:
        def __impure__wait(driver: WebDriver) -> SafeWebElement:
            time.sleep(seconds)
            return BlankSafeWebElement
        return _asLoggedBrowserAction(name="wait("+str(seconds)+")", function=_driverFunction_to_browserFunction(__impure__wait))  

    @staticmethod
    def click(this: WebElementSignature) -> MonadicBrowserFunction:
        # TODO: should return element that was clicked?
        def __clickViaElement(elem: WebElement) -> None:
            elem.click()
        def __impure__clickViaDriver(driver: WebDriver) -> SafeWebElement:
            clickable_element = _getSafeWebElement(find=this, using=driver)
            clickable_element.apply(__clickViaElement)
            return clickable_element
        return _asLoggedBrowserAction(
            name = "click(" + str(this) + ")", 
            function = _driverFunction_to_browserFunction(__impure__clickViaDriver)
        )

    @staticmethod
    def switchToFrame(this: WebElementSignature) -> MonadicBrowserFunction:
        def __impure__switchToFrame(driver: WebDriver) -> SafeWebElement:
            def __impure__applySwitchToFrame(frame_element: WebElement) -> None:
                driver.switch_to.frame(frame_element)
            frame_element = _getSafeWebElement(find=this, using=driver)
            frame_element.apply(__impure__applySwitchToFrame)
            return frame_element
        return _asLoggedBrowserAction(
            name = "switchToFrame(" + str(this) + ")", 
            function = _driverFunction_to_browserFunction(__impure__switchToFrame)
        )
    
    @staticmethod
    def find(this: WebElementSignature, within_element: bool = True) -> MonadicBrowserFunction:
        def __find_element(element: WebElement) -> SafeWebElement:
                return SafeWebElement(Just(element.find_element(by=this[0], value=this[1])))      
        def __impure__find_from_anywhere(driver: WebDriver) -> SafeWebElement:
            return _getSafeWebElement(find=this, using=driver)
        fn_find_from_element = _elementFunction_to_browserFunction(__find_element)
        fn_find_from_anywhere = _driverFunction_to_browserFunction(__impure__find_from_anywhere) 
        return _asLoggedBrowserAction(
            name = "find(" + str(this) + ", " + str(within_element) + ")", 
            function = fn_find_from_element if within_element else fn_find_from_anywhere
        )

    @staticmethod
    def waitUntil(this: WebElementSignature, becomes: Expect, within: Seconds = 3, then: Callable[[WebElementSignature], MonadicBrowserFunction] = _doNothing) -> MonadicBrowserFunction:
        # TODO: should DEFINITELY return the element that was waiting for
        def __impure__waitUntil(driver: WebDriver) -> SafeWebElement:
            web_element = _getSafeWebElement(find=this, using=driver)
            WebDriverWait(driver, within).until(becomes(this))
            return web_element
        return _compose([
            _asLoggedBrowserAction(
                name = "waitUntil(" + str(this) + ", " + str(becomes) + ", " + str(then) + ")", 
                function = _driverFunction_to_browserFunction(__impure__waitUntil)
            ), 
            then(this)
        ])
        
    @staticmethod
    def handleErrorWithDriverFunction() -> MonadicBrowserFunction:
        pass

    @staticmethod
    def handleErrorWithElementFunction() -> MonadicBrowserFunction:
        pass

    @staticmethod
    def handleErrorWithBrowserFunction() -> MonadicBrowserFunction:
        pass

    @staticmethod
    def customDriverFunction(function: DriverFunction[SafeWebElement]) -> MonadicBrowserFunction:
       return _asLoggedBrowserAction(
            name = "customDriverFunction(" + str(function.__code__.co_name) + ")", 
            function = _driverFunction_to_browserFunction(function)
        )

    @staticmethod
    def customElementFunction(function: ElementFunction[SafeWebElement]) -> MonadicBrowserFunction:
       return _asLoggedBrowserAction(
            name = "customElementFunction(" + str(function.__code__.co_name) + ")", 
            function = _elementFunction_to_browserFunction(function)
        )

    @staticmethod
    def customBrowserFunction(function: BrowserFunction) -> MonadicBrowserFunction:
        return _asLoggedBrowserAction(
            name = "customBrowserFunction(" + str(function.__code__.co_name) + ")", 
            function = function
        )
