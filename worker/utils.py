def fmt(raw_string, **mapping):
    result = raw_string
    for k, v in mapping.items():
        result = result.replace('{' + k + '}', v)

    return result
