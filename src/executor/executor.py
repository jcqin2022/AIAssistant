# create executor as a base class, in which, define a method list to include function name and method pointer of current class, and below methods are provided,
# get_prompt(): provide a prompt string to tell openai who are you and what you can do. for base class, just a common user enough.
# get_tool_definition(): provide the function definitions of all methods of current class for openai to call.
# execute(): it will get function name and arguments from input, then execute the target function by the function name.

class Executor:
    def __init__(self):
        self.methods = {
        }
        self.prompt = ""
        self.context = ""

    def get_prompt(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"错误: prompt文件 {file_path} 未找到")
    
    def get_context(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"错误：context文件 {file_path} 未找到")

    def get_tool_definition(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def execute(self, function_name, *args, **kwargs):
        if function_name in self.methods:
            return self.methods[function_name](*args, **kwargs)
        else:
            raise ValueError(f"Function '{function_name}' not found in methods.")
        
    async def aexecute(self, function_name, *args, **kwargs):
        if function_name in self.methods:
            return await self.methods[function_name](*args, **kwargs)
        else:
            raise ValueError(f"Function '{function_name}' not found in methods.")
        
    def get_function(self, function_name):
        return self.methods.get(function_name, None)
    
    def is_async(self):
        return False