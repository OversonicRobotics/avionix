import re


def post_uninstall_handle_error(message):
    return HelmError(message)


class ErrorFactory:
    def __init__(self, message: str):
        self._message = message

    def get_error(self):
        if re.match(r"Error: Kubernetes cluster unreachable.*", self._message):
            return ClusterUnavailableError(self._message)
        if re.match(r"Error: cannot re-use a name that is still in use", self._message):
            return ChartAlreadyInstalledError(self._message)
        if re.match(
            r"Error:.*unable to create new content in namespace \w+ because "
            r"it is being terminated",
            self._message,
        ):
            return NamespaceBeingTerminatedError(self._message)
        return None


class AvionixError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class ClusterUnavailableError(AvionixError):
    pass


class ChartAlreadyInstalledError(AvionixError):
    pass


class HelmError(AvionixError):
    pass


class NamespaceBeingTerminatedError(AvionixError):
    pass
