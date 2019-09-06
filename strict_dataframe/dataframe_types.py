# Enable Abstract Classes 
from abc import ABCMeta, abstractmethod
from .pymonad_types import * # <-- mypy typecheck doesn't seem to work with externally imported classes, 
                            #     copied pymonad content to a local file as temporary solution
import pandas as pd
import numpy as np

# __________________________________________________________________________________________
# MAKE IMPORTED CLASSES TYPE-CHECKABLE (HACK)
class DataFrame(pd.DataFrame): pass

# __________________________________________________________________________________________
# FUNCTIONAL DATA STRUCTURES
BasicType = Type[Union[str, int, float]]
TypeDict = Dict[str, BasicType]
StringList = List[str]
StringSet = Set[str]
StringTypeTupleList = List[Tuple[str, BasicType]]

# __________________________________________________________________________________________
# CLASS DEFINITIONS

class Printable:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __asString__(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__asString__()
    
    def __repr__(self):
        return self.__asString__()

class CumulativeMonoidSet(Printable, Monoid):
    # dictionary that implements following traits:
    # - keys exactly match the data type of corresponding value
    # - (implied) no duplicate keys can exist
    # - all values must be a Monoid
    def __init__(self, value: List[Monoid] = []) -> None:
        self.__value: Dict[str, Monoid] = self.__listToTypeSet(value)
    
    def __listToTypeSet(self, monoid_list: List[Monoid]) -> Dict[str, Monoid]:
        new_typeset: Dict[str, Monoid] = {}
        for monoid_value in monoid_list:
            # key = str(type(monoid_value))
            key = monoid_value.__class__.__name__
            existing_keys = new_typeset.keys()
            new_typeset[key] = new_typeset[key] + monoid_value if key in existing_keys else monoid_value
        return new_typeset

    def __asString__(self) -> str:
        data = self.getValue()
        if(len(data) == 0): return "<empty>"
        return "\n\n".join([str(type_key) + ":\n" + str(data[type_key]) for type_key in data.keys()])

    def getSet(self) -> Dict[str, Monoid]:
        return self.__value

    def getValue(self) -> Dict[str, Monoid]:
        return self.getSet()
    
    def getUntypedMonoidValue(self, key: str) -> Any:
        # NOTE: this is an insecure hack.
        # The Monoid values stored by a CumulativeMonoidSet is unlikely to be a pure Monoid;
        # they will be a class that inherits Monoidic properties.
        # It is also likley that those child classes will have their own unique properties and methods
        # that need to be accessed. However, since those unique properties are not attribute(s) of
        # a Monoid, Mypy will flag the reference as an error. There was no elegant way to overcome
        # this, so this method was created to simply 'ignore' any type checking.
        # It is strongly recommended that this method be only used to assign a value to a variable
        # that is explicitly typed as the expected class of value returned from this method
        return self.__value[key]

    def getValueAsList(self) -> List[Monoid]:
        return list(self.getValue().values())

    def append(self, other: 'CumulativeMonoidSet') -> 'CumulativeMonoidSet':
        if type(other) is CumulativeMonoidSet:
            return CumulativeMonoidSet(self.getValueAsList() + other.getValueAsList()) 
        else: 
            return CumulativeMonoidSet(self.getValueAsList())

    @staticmethod
    def mzero():
        return CumulativeMonoidSet()
        
    def mplus(self, other: 'CumulativeMonoidSet') -> 'CumulativeMonoidSet':
        return self.append(other)

class StrictDataFrame(Printable):
    
    # StrictDataFrame itself is kind of like a basic type
    # if it is to be implemented as Monad, it will have to be implemented in similar ways to List monad
    # but it can't really, because the types of each column is rigid and cannot host functions in its cells...
    # Could it be a Monoid?

    # Dataframe with immutable column names and colum data types
    # Purpose: construct a new type of dataframe that garuntees presensce of specific column names and data types

    def __init__(self, columns: StringTypeTupleList = [], dataframe: DataFrame = DataFrame()) -> None:

        # names: Union[StringSet, TypeDict] = set()
        # column_order: List[str] = []

        # init scenarios:
        # 0A. if no input is provided, empty named dataframe is created, which is totally useless
        # 0B. if no names are provided, but empty named dataframe is provided, these names will be used
        # 1. if only names are provided, named dataframe no values will be created
        # 2. if only values are provided, all names in provided dataframe will be used
        # 3. if both names and values are provided, all of the names will be used, 
        #    but only data with overlapping names will be kept

        # 'names' parameter:
        # names can be either a unique string set (StringSet) detailing only the names of the columns
        # (in which case data types per column is inferred) or a strict type dictionary (TypeDict) that
        # contians both the names of columns and the data type for each column, in which case the 
        # specified types will be enforced
        
        names: TypeDict = { name: datatype for name, datatype in columns}
        column_order: List[str] = [name for name, _ in columns]
        
        self.__value: DataFrame = dataframe  
        self.__index: TypeDict = self.__inferTypeDict(names=names, dataframe=dataframe) 
        
        if(len(names) == 0 and len(dataframe) == 0):
            # scenario 0A or 0B (same treatment)
            self.__value = dataframe
        elif(len(names) > 0 and len(dataframe) == 0):
            # scenario 1
            self.__value = self.__buildValueFromNames(index=self.__index)
        elif(len(names) == 0 and len(dataframe) > 0):
            # scenario 2
            self.__value = dataframe
        else:
            # scenario 3
            self.__value = self.__buildValueFromNamesAndDataframe(index=self.__index, dataframe=dataframe)
        
        if(len(column_order) > 0):
            # if column order is defined, sort columns of underlying dataframe
            ordered_names = list(filter(lambda colname: colname in list(names), column_order))
            remaining_names = np.setdiff1d(list(names),ordered_names).tolist()
            self.__value = self.__value.reindex(ordered_names + remaining_names, axis=1)

    def __indexToNames(self, index: TypeDict) -> StringSet:
        return set(index.keys())

    def __inferTypeDict(self, names: TypeDict, dataframe: DataFrame) -> TypeDict:

        if(len(names) == 0):
            # if names are not defined, infer names & types from dataframe
            # currently all types are set to 'str' by default
            # TODO: more sophisticated type inference
            return {name: str for name in list(dataframe.columns)}
        else:
            # is TypeDict, statically type name as TypeDict
            return names
    
    def __castColumnTypes(self, index: TypeDict, dataframe: DataFrame) -> DataFrame:
        for colname in index.keys():
            dataframe[[colname]] = dataframe[[colname]].apply(lambda ls: ls.astype(index[colname]))
        return dataframe

    def __buildValueFromNames(self, index: TypeDict) -> DataFrame:
        return self.__castColumnTypes(
            index = index, 
            dataframe = DataFrame(columns=self.__indexToNames(index))
        )
        
    def __buildValueFromNamesAndDataframe(self, index: TypeDict, dataframe: DataFrame) -> DataFrame:
        names: StringSet = self.__indexToNames(index)
        extracted_names = pd.Series(list(dataframe))
        matching_names = extracted_names[extracted_names.isin(names)]
        df_names = self.__castColumnTypes(
            index = index, 
            dataframe = self.__buildValueFromNames(index = index)
        )
        df_data = dataframe[matching_names] if len(matching_names) > 0 else DataFrame()
        return pd.concat([df_names,df_data], sort=True)
    
    def getIndex(self) -> TypeDict:
        return self.__index

    def getColumns(self) -> StringTypeTupleList:
        return [(name, self.__index[name]) for name in self.__index]

    def getNames(self) -> StringSet:
        return self.__indexToNames(self.__index)
    
    def getValue(self) -> DataFrame:
        return self.__value
    
    def append(self, other: 'StrictDataFrame') -> 'StrictDataFrame':
        # alwyas persist the column names of self
        return StrictDataFrame(
            columns = self.getColumns(), 
            dataframe = self.getValue().append(other.getValue(), sort=True)
        )
    
    def __asString__(self) -> str:
        return "StrictDataFrame:\n" + str(self.getValue())

class HasStrictDataframe(Printable):

    __metaclass__ = ABCMeta

    def __init__(self, classname: str, value: StrictDataFrame) -> None:
        self.__classname: str = classname
        self.__value: StrictDataFrame = value
    
    def getValue(self) -> DataFrame:
        return self.__value.getValue()

    def getIndex(self) -> TypeDict:
        return self.__value.getIndex()

    def getNames(self) -> StringSet:
        return self.__value.getNames()
    
    def __asString__(self) -> str:
        return self.__classname + ":\n" + str(self.getValue())

    def _appendInternal(self, other: 'HasStrictDataframe') -> DataFrame:
        return self.getValue().append(other.getValue(), sort=True)
    
    @abstractmethod
    def append(self, other):
        raise NotImplementedError