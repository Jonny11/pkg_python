class {{dataframe_uppercase_name}}DataFrame(df.HasStrictDataframe):

    def __init__(self, dataframe: df.DataFrame = df.DataFrame()) -> None:
        super({{dataframe_uppercase_name}}DataFrame, self).__init__(
            classname = "{{dataframe_uppercase_name}}DataFrame", 
            value = df.DataFrame(dataframe = dataframe, 
                                    columns   = [{{list_pattern(list="columns", pattern="('{{column_name}}', {{data_type}})", sep=",\n")}}]))

    def append(self, other: '{{dataframe_uppercase_name}}DataFrame') -> '{{dataframe_uppercase_name}}DataFrame':
        return {{dataframe_uppercase_name}}DataFrame(self._appendInternal(other))