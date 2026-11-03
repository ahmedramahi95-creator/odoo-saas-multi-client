from odoo.exceptions import AccessError


ROLES = ("prof", "fan", "log", "super")


def role(env):
    for name in ROLES:
        group = env.ref("jamel_access_roles.group_" + name, raise_if_not_found=False)
        if group and group in env.user.all_group_ids:
            return name
    return None


def check_financial_mutation(env):
    if not env.su and role(env) in ("log", "super"):
        raise AccessError(env._("This role may read and print invoices, but cannot change financial documents."))
