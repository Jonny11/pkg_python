# strict_dataframe::monoidic_strict_dataframe_compound
# TODO: This file is auto-generated by a CLI helper tool 'strict_dataframe' and never modified manually

import typing as t
from strict_dataframe import pymonad_types as m
import strict_dataframe as df

{{list_template(template="named_strict_dataframe", sep="\n\n")}}

class {{compound_dataclass_uppercase_name}}(df.Printable, m.Monoid):
    def __init__(self, {{list_pattern(pattern="df_{{dataframe_lowercase_name}}: {{dataframe_uppercase_name}}DataFrame = {{dataframe_uppercase_name}}DataFrame()", sep=", ")}}) -> None:
        {{list_pattern(pattern="self.__{{dataframe_lowercase_name}}: {{dataframe_uppercase_name}}DataFrame = df_{{dataframe_lowercase_name}}", sep="\n")}}

    {{list_template(template="dataframe_getter", sep="\n\n")}}
    
    def getValue(self) -> t.Tuple[{{list_pattern(pattern="{{dataframe_uppercase_name}}DataFrame", sep=", ")}}]:
        return ({{list_pattern(pattern="self.get{{dataframe_uppercase_name}}()", sep=", ")}})

    def append(self, other: '{{compound_dataclass_uppercase_name}}') -> '{{compound_dataclass_uppercase_name}}':
        return {{compound_dataclass_uppercase_name}}(
            {{list_pattern(pattern="df_{{dataframe_lowercase_name}} = {{dataframe_uppercase_name}}DataFrame(self.get{{dataframe_uppercase_name}}().append(other.get{{dataframe_uppercase_name}}()))", sep=",\n")}}
        )
    
    def __asString__(self) -> str:
        return "{{compound_dataclass_uppercase_name}}:\n\n" + {{list_pattern(pattern="str(self.__{{dataframe_lowercase_name}})", sep=" + '\n\n' + ")}}

    @staticmethod
    def mzero():
        return {{compound_dataclass_uppercase_name}}()
        
    def mplus(self, other: '{{compound_dataclass_uppercase_name}}') -> '{{compound_dataclass_uppercase_name}}':
        return self.append(other)


