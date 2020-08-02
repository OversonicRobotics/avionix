from avionix._process_utils import custom_check_output
from avionix.testing.helpers import parse_output_to_dataframe


def get_helm_installations(namespace: str = ""):
    command = "helm list"
    if namespace:
        command += f" -n {namespace}"
    output = custom_check_output(command)
    return parse_output_to_dataframe(output)
