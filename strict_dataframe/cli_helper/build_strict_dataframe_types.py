from strict_dataframe.cli_helper.main import define, resolveTemplate

if __name__ == "__main__":

    resolveTemplate(template_name = "compound_dataframe", 
                    template_params = define.strictDatafameCompound(
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
    )