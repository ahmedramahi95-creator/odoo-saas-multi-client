from odoo import api, models

from .policy import check_financial_mutation


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model_create_multi
    def create(self, vals_list):
        check_financial_mutation(self.env)
        return super().create(vals_list)

    def write(self, vals):
        check_financial_mutation(self.env)
        return super().write(vals)

    def unlink(self):
        check_financial_mutation(self.env)
        return super().unlink()

    def action_post(self):
        check_financial_mutation(self.env)
        return super().action_post()

    def button_draft(self):
        check_financial_mutation(self.env)
        return super().button_draft()

    def button_cancel(self):
        check_financial_mutation(self.env)
        return super().button_cancel()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        check_financial_mutation(self.env)
        return super().create(vals_list)

    def write(self, vals):
        check_financial_mutation(self.env)
        return super().write(vals)

    def unlink(self):
        check_financial_mutation(self.env)
        return super().unlink()

    def reconcile(self):
        check_financial_mutation(self.env)
        return super().reconcile()

    def remove_move_reconcile(self):
        check_financial_mutation(self.env)
        return super().remove_move_reconcile()
