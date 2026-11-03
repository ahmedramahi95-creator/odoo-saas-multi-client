from odoo import api, models
from odoo.exceptions import AccessError, ValidationError

from .policy import ROLES, role


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.constrains("group_ids")
    def _check_jamel_role(self):
        markers = self.env["res.groups"].browse([
            group.id for name in ROLES
            if (group := self.env.ref("jamel_access_roles.group_" + name, raise_if_not_found=False))
        ])
        forbidden = self.env.ref("base.group_system") | self.env.ref("base.group_erp_manager")
        for user in self:
            if len(user.all_group_ids & markers) > 1:
                raise ValidationError(self.env._("Choose exactly one Jamel role for each user."))
            if user.all_group_ids & markers and user.all_group_ids & forbidden:
                raise ValidationError(self.env._("Jamel roles cannot be combined with user or security administration."))

    @api.model_create_multi
    def create(self, vals_list):
        if role(self.env) == "prof":
            raise AccessError(self.env._("The prof role cannot create users."))
        return super().create(vals_list)

    def write(self, vals):
        if role(self.env) == "prof" and (
            self != self.env.user or set(vals) & {"group_ids", "all_group_ids", "company_ids", "company_id", "active", "login"}
        ):
            raise AccessError(self.env._("The prof role cannot administer users or permissions."))
        return super().write(vals)

    def unlink(self):
        if role(self.env) == "prof":
            raise AccessError(self.env._("The prof role cannot delete users."))
        return super().unlink()


class ResGroups(models.Model):
    _inherit = "res.groups"

    @api.model_create_multi
    def create(self, vals_list):
        if role(self.env) == "prof":
            raise AccessError(self.env._("The prof role cannot administer permissions."))
        return super().create(vals_list)

    def write(self, vals):
        if role(self.env) == "prof":
            raise AccessError(self.env._("The prof role cannot administer permissions."))
        return super().write(vals)

    def unlink(self):
        if role(self.env) == "prof":
            raise AccessError(self.env._("The prof role cannot administer permissions."))
        return super().unlink()
