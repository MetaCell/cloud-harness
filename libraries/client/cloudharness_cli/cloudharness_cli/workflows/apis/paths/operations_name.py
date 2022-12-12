from cloudharness_cli.workflows.paths.operations_name.get import ApiForget
from cloudharness_cli.workflows.paths.operations_name.delete import ApiFordelete


class OperationsName(
    ApiForget,
    ApiFordelete,
):
    pass
