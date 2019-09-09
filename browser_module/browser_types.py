# __________________________________________________________________________________________
# DEPENDENCIES
from sys import platform

# Enable Static Typing
# import typing as t

# from typing import *

# Enable Functional Programming
# import pymonad as f
# from pymonad import Container, Monoid, Functor, Applicative, Monad
# from pymonad.Reader import curry
# from pymonad_types import * # <-- mypy typecheck doesn't seem to work with externally imported classes, 
                            #     copied pymonad content to a local file as temporary solution


# Module Dependencies
import pandas as pd # <- import for namespace referencing during development

from enum import Enum

import selenium 
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as Expect
from selenium.webdriver.common.by import By as by

# Internal Imports
import strict_dataframe as sd # <- import for namespace referencing during development
from typing import TypeVar, Type, Dict, Set, Union, List, Generic, Any, Tuple, Callable
from strict_dataframe import CumulativeMonoidSet, HasStrictDataframe, StrictDataFrame, Monoid, Printable, Just, Nothing, DataFrame, Maybe, T, Monad

# from dataframe_types import *
# __________________________________________________________________________________________
# CLASS FORWARD REFERENCE DECLARATIONS
# uncomment below for python 3.7 and above. All forward reference must be un-quoted
# from __future__ import annotations

# __________________________________________________________________________________________
# MAKE IMPORTED CLASSES TYPE-CHECKABLE (HACK)
class By(by): pass
# class DataFrame(pd.DataFrame): pass # already defined by dataframe_types
class WebDriver(selenium.webdriver.remote.webdriver.WebDriver): pass
class WebElement(selenium.webdriver.remote.webelement.WebElement): pass

# __________________________________________________________________________________________
# FUNCTIONAL DATA STRUCTURES

BrowserValue = Tuple['SafeWebDriver', 'BrowserSessionLog', 'CumulativeMonoidSet', 'SafeWebElement']
WebElementSignature = Tuple[By, str]
# T = TypeVar("T")




class BrowserSessionLogsDataFrame(HasStrictDataframe):
    def __init__(self, dataframe: DataFrame = DataFrame()) -> None:
        super(BrowserSessionLogsDataFrame, self).__init__(
            classname = "BrowserSessionLogsDataFrame", 
            value = StrictDataFrame( dataframe = dataframe, columns = [("step", str),("log", str)] ))

    def append(self, other: 'BrowserSessionLogsDataFrame') -> 'BrowserSessionLogsDataFrame':
        return BrowserSessionLogsDataFrame(self._appendInternal(other))

class BrowserSessionLog(Monoid, Printable):
    def __init__(self, value: BrowserSessionLogsDataFrame = BrowserSessionLogsDataFrame()) -> None:
        self.__value: BrowserSessionLogsDataFrame = value

    def getValue(self) -> DataFrame:
        return self.__value.getValue()

    def append(self, other: 'BrowserSessionLog') -> 'BrowserSessionLog':
        return BrowserSessionLog(BrowserSessionLogsDataFrame(self.getValue().append(other.getValue(), sort=True)))
    
    def __asString__(self) -> str:
        return "BrowserSessionLog:\n\n" + str(self.__value)

    @staticmethod
    def mzero():
        return BrowserSessionLog()
        
    def mplus(self, other: 'BrowserSessionLog') -> 'BrowserSessionLog':
        return self.append(other)

class SafeWebDriver:
    def __init__(self, handle: WebDriver) -> None:
        self.__handle: WebDriver = handle
        self.__error: bool = False

    def apply(self, function: Callable[[WebDriver], T], ignore_error_flag: bool = False) -> Maybe[T]:
        if(self.isUsable(ignore_error = ignore_error_flag)): 
            try:
                return Just(function(self.__handle))
            except:
                self.__error = True
                return Nothing
        else:
            return Nothing

    def hasError(self) -> bool:
        return self.__error

    def isAlive(self) -> bool:
        # TODO: This function is subject to external conditions (what happens to the browser)
        #       hence violating the referential transperancy. This means function interacting
        #       with this class may return different outcome given same input. 
        #       better alternative is needed to make this module a pure function.
        #       perhaps override .quit() method of specific webdriver modules (e.g. Chrome)
        #       and track whether browser is open or closed. Note however, even if such 
        #       alternative is implemented, browser drivers are still subject to side-effects
        try:
            self.__handle.title
            return True
        except:
            return False
    
    def isUsable(self, ignore_error: bool = False) -> bool:
        if ignore_error:
            return self.isAlive()
        else:
            return self.isAlive() and not self.hasError()
    
    def setError(self, set_error_to: bool) -> None:
        self.__error = set_error_to

class ChromeWebDriver(SafeWebDriver):
    def __init__(self, use_headless_browser: bool = True, window_width: int = 800, window_height: int = 600, driver_path: str = None) -> None:
            
        browser_options = webdriver.ChromeOptions()
        browser_options.add_argument("window-size=" + str(window_width) + "x" + str(window_height)) # <- WARNING: large screen resolution crashes code in linux
        
        if use_headless_browser:
            browser_options.add_argument("headless")
        
        if platform == "linux":
            browser_options.add_argument('--no-sandbox')
            browser_options.add_argument('--disable-gpu')

        if driver_path is None:
            driver_path = "./driver/"+platform+"/chromedriver"
        
        super(ChromeWebDriver, self).__init__(handle = webdriver.Chrome(
            executable_path = driver_path, 
            chrome_options = browser_options
        ))

class SafeWebElement(Printable):
    def __init__(self, value: Maybe[WebElement]) -> None:
        self.__value: Maybe[WebElement] = value
    
    def __asString__(self) -> str:
        return str(self.__value.getValue())

    def apply(self, function: Callable[[WebElement],T]) -> Maybe[T]:
        if(self.__value != Nothing):
            return Just(function(self.__value.getValue()))
        else:
            return Nothing

class BrowserSession(Monad, Printable):
    def __init__(
        self, 
        driver: SafeWebDriver, 
        logs: BrowserSessionLog = BrowserSessionLog(), 
        data: CumulativeMonoidSet = CumulativeMonoidSet([]),
        element: SafeWebElement = SafeWebElement(Nothing)
    ) -> None:
        # self.__driver: SafeWebDriver = driver
        # self.__logs: List[str] = logs
        # self.__data: CumulativeMonoidSet = data
        self.__value: BrowserValue = (driver, logs, data, element)
    
    def getValue(self) -> BrowserValue:
        return self.__value
    
    # def applyToDriver(self, function: Callable[[WebDriver], None]) -> None:
    #     driver, _, _ = self.__value
    #     driver.apply(function)
    
    def hasError(self) -> bool:
        driver, _, _, _ = self.__value
        return driver.hasError()

    def isAlive(self) -> bool:
        driver, _, _, _ = self.__value
        return driver.isAlive()
    
    def getData(self) -> CumulativeMonoidSet:
        _, _, data, _ = self.__value
        return data
    
    def readData(self, classname: str) -> Any:
        _, _, data, _ = self.__value
        return data.getValue()[classname]

    def getLogs(self) -> BrowserSessionLog:
        _, logs, _, _ = self.__value
        return logs
    
    def getElement(self) -> SafeWebElement:
        _, _, _, element = self.__value
        return element

    def __asString__(self) -> str:
        driver, logs, data, element = self.getValue()
        header_str = "BrowserSession:\n\n" 
        driver_str = "Driver:\n" + str(driver) + "\nAlive: " + str(self.isAlive()) + "\nError: " + str(self.hasError())
        logs_str = "\n\nLogs:\n" + str(logs)
        data_str = "\n\nData:\n" + str(data)
        element_str = "\n\nElement:\n" + str(element)
        return header_str + driver_str + logs_str + data_str + element_str

    @classmethod
    def unit(cls, value: BrowserValue) -> 'BrowserSession':
        driver, logs, data, element = value
        return BrowserSession(driver, logs, data, element)

    def fmap(self, function: Callable[[BrowserValue], BrowserValue]) -> 'BrowserSession':        
        if self.hasError():
            return self
        else: 
            driver, logs, data, element = function(self.getValue())
            return BrowserSession(driver, logs, data, element)
    
    def bind(self, function: Callable[[BrowserValue], 'BrowserSession']) -> 'BrowserSession':
        return function(self.getValue())
    
    # def bind(self, function: Callable[[BrowserValue], 'BrowserSession']) -> 'BrowserSession':
    #     if self.hasError():
    #         return self
    #     else:
    #         return function(self.getValue())

