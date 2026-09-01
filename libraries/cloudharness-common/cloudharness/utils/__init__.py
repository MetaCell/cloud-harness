import collections


def __getattr__(name):
    # Backwards compatibility: cloudharness.utils.server was renamed to
    # flask_server. Import lazily - flask_server pulls in flask/connexion and
    # cloudharness.applications, which would be a circular import here.
    if name == "server":
        from . import flask_server
        return flask_server
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def dict_merge(dct, merge_dct, add_keys=True, merge_none=True):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.

    This version will return a copy of the dictionary and leave the original
    arguments untouched.

    The optional argument ``add_keys``, determines whether keys which are
    present in ``merge_dict`` but not ``dct`` should be included in the
    new dict.

    Args:
        dct (dict) onto which the merge is executed
        merge_dct (dict): dct merged into dct
        add_keys (bool): whether to add new keys

    Returns:
        dict: updated dict
    """
    dct = dct.copy()
    if not add_keys:
        merge_dct = {
            k: merge_dct[k]
            for k in set(dct).intersection(set(merge_dct))
        }

    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict) and
                isinstance(merge_dct[k], collections.abc.Mapping)):
            dct[k] = dict_merge(dct[k], merge_dct[k], add_keys=add_keys)
        elif merge_none or (merge_dct[k] is not None):
            dct[k] = merge_dct[k]

    return dct


__all__ = ["dict_merge", "server"]
