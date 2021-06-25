from fission.core.jobs import PythonJob


class JoinJob(PythonJob):
    def run(self, operator, *args):
        try:
            args = [f" {str(arg)} " for arg in args]
            operation = operator.join(args)
            result = eval(operator.join(args))
            print(operation, "=", result)
        except:
            print(f"Operator {operator} is not valid.")
            result = "error"

        return (result, result, operator)

class ReduceJob(PythonJob):
    def run(self, L):
        _L = [value for value in L if not isinstance(value, str)]
        if len(_L) != len(L):
            print("Dropped strings.")
        result = sum(_L)
        print(f"Sum over {_L} = {result}")
        return result