from typing import Dict, Union, List, Tuple
from strict_dataframe import StringTypeTupleList
import re
import os

code_dir:str = "./code_template"
code_template_files:List[str] = list(filter(lambda s: not s.startswith('.'), os.listdir(code_dir)))
code_template_names:List[str] = list(map(lambda s: s.replace(".py",""), code_template_files))
code_template:Dict = {template_name: open(code_dir + "/" + file_name, "r").read() for template_name, file_name in zip(code_template_names, code_template_files)}

def _toLowercaseName(uppercase_name:str) -> str:
    name = uppercase_name
    pattern = re.compile("[A-Z]")
    split_points:List[int] = [0]
    start = -1
    while True:
        m = pattern.search(name, start + 1) 
        if m == None:
            break
        start = m.start()
        if(start > 0):
            split_points.append(start)
    parts = [name[i:j] for i,j in zip(split_points, split_points[1:]+[None])]
    parts = [w.lower() for w in parts]
    
    return "_".join(parts)
class ParamDict:

    def __init__(self, value: Dict) -> None:
        self.__value: Dict = value

    def value(self):
        return self.__value

class DataframeDefinition(ParamDict):

    def __init__(self, name:str, contents:StringTypeTupleList) -> None:

        # Sample data structure:
        # {
        #     'global': {
        #         'dataframe_uppercase_name': 'BankAccounts',
        #         'dataframe_lowercase_name': 'bank_accounts'
        #         },
        #     '_list': {
        #         'columns': [
        #             {
        #                 'column_name': "bank", 
        #                 'data_type':'str'
        #             },
        #             {
        #                 'column_name': "client", 
        #                 'data_type':'int'
        #             }
        #         ]
        #     }
        # }
        value: Dict = {
            'global': {
                'dataframe_uppercase_name': name,
                'dataframe_lowercase_name': _toLowercaseName(name)
                },
            '_list': {
                'columns': [{'column_name': colname, 'data_type': datatype.__name__} for colname, datatype in contents]
            }
        }
        super(DataframeDefinition, self).__init__(value = value)


class DataframeCompoundDefinion(ParamDict):

    def __init__(self, name:str, contents:List[DataframeDefinition]) -> None:

        # Sample data structure:
        # {
        #     'global': {
        #         'compound_dataclass_uppercase_name': 'OnlineBankingData'
        #     },
        #     '_list': {
        #         'contents': [
        #             ...DataframeDefinition(s)...
        #         ]
        #     }
        # }
        
        value: Dict = {
            'global': {
                'compound_dataclass_uppercase_name': name
            },
            '_list': {
                'contents': [df.value() for df in contents]
            }
        }

        super(DataframeCompoundDefinion, self).__init__(value = value)

class DefinitionHelper:

    def __init__(self) -> None:
        self.strict_dataframe: List[DataframeDefinition] = []
        self.strict_dataframe_compound: List[DataframeCompoundDefinion] = []

    def strictDataframe(self, name: str, columns: StringTypeTupleList) -> DataframeDefinition:
        value: DataframeDefinition = DataframeDefinition(name = name, contents = columns)
        self.strict_dataframe.append(value)
        return value

    def strictDatafameCompound(self, name: str, contents: List[DataframeDefinition], suffix: str = "") -> DataframeCompoundDefinion:
        value: DataframeCompoundDefinion = DataframeCompoundDefinion(name = name, contents = contents)
        self.strict_dataframe_compound.append(value)
        return value

    def value(self):
        return {
            'strict_dataframe_compound': [x.value() for x in self.strict_dataframe_compound],
            'strict_dataframe': [x.value() for x in self.strict_dataframe]
        }

def resolveTemplate(template_name: str, template_params: ParamDict) -> str:

    template = code_template[template_name]
    params = template_params.value()

    # first, replace all direct-replacement-terms
    for key in params['global']:
        signature = "{{"+key+"}}"
        template = template.replace(signature, params['global'][key])

    # Now the only remaining terms are list_x() method terms

    # bracket capture strategy
    # 1. index positions of all '{{' and '}}'
    # 2. use counter to mark the brakets '{{' = +1, '}}' = -1
    # 3. mark the positions that have counter = 0 (replace them with unique special character that can be picked up)
    # 4. join the strings back and split by the marked closing brackets
    # 5. in each sub-string, look for the first opening bracket


    # i_open = re.finditer('{{', template)
    # print([x for x in i_open])

    print(template)
    return template

define = DefinitionHelper()

if __name__ == "__main__":


    params = define.strictDatafameCompound(
        name = "OnlineBankingData", 
        contents = [
            define.strictDataframe(name = "BankAccounts", 
                                columns = [
                                    ("bank", str), 
                                    ("client", int), 
                                    ("bsb", int), 
                                    ("account", int), 
                                    ("nickname", str), 
                                    ("balance", float), 
                                    ("fund", float), 
                                    ("link", str)
                                ]),
            define.strictDataframe(name = "BankTransactions", 
                                columns = [
                                    ("bank", str),
                                    ("client", int),
                                    ("bsb", int),
                                    ("account", int),
                                    ("date", str),
                                    ("description", str),
                                    ("amount", float),
                                    ("total", float)
                                ])
        ]
    )


    resolveTemplate(template_name = "compound_dataframe", template_params = params)

    # print(params.value())

    # template_name = 

    # data = open(template_name, "r").read()

    # print(data)


