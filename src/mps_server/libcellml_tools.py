import types
from cellsolvertools.generate_code import return_generated_python_code, ModelGenerationError


def import_code(code_string, name):
    # create blank module
    module = types.ModuleType(name)
    # populate the module with code
    exec(code_string, module.__dict__)
    return module


def get_parameters_from_model(model_file):
    try:
        python_code = return_generated_python_code(model_file)
    except ModelGenerationError:
        return {}

    m = import_code(python_code, 'generated_model_python_code')

    parameter_info = {}
    state_info = m.STATE_INFO
    for s in state_info:
        if s['component'] in parameter_info:
            parameter_info[s['component']][s['name']] = 'STATE'
        else:
            parameter_info[s['component']] = {s['name']: 'STATE'}

    variable_info = m.VARIABLE_INFO
    for v in variable_info:
        if v['component'] in parameter_info:
            parameter_info[v['component']][v['name']] = v['type'].name
        else:
            parameter_info[v['component']] = {v['name']: v['type'].name}

    return parameter_info
