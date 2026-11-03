from odoo import models
from odoo.exceptions import AccessError

from .policy import role


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_create_invoice(self, attachment_ids=False):
        if role(self.env) in ("log", "super"):
            raise AccessError(self.env._("This role may order from suppliers but cannot create vendor bills."))
        return super().action_create_invoice(attachment_ids=attachment_ids)
