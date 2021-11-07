

def normalise_for_use_as_path(data_in):
    """Normalise the 'data_in' so it can be used as part of a path."""
    return data_in.replace('|', '_').replace('.', '_dot_')
