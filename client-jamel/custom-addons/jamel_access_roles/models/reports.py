from odoo import models
from odoo.exceptions import AccessError

from .policy import role


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _jamel_check_report(self, report_ref, res_ids):
        current_role = role(self.env)
        if not current_role:
            return False
        report = self._get_report(report_ref)
        restricted_invoice = False
        if current_role in ("log", "super"):
            invoice = report.model == "account.move" and report.report_name == "account.report_invoice"
            stock = current_role == "log" and (report.model.startswith("stock.") or report.model in ("product.product", "product.template"))
            purchase = current_role == "super" and report.model == "purchase.order"
            if not (invoice or stock or purchase):
                raise AccessError(self.env._("This report is not available for your role."))
            restricted_invoice = invoice
        if report.model == "account.move" and res_ids:
            records = self.env[report.model].with_user(self.env.uid).browse(res_ids)
            records.check_access("read")
        if restricted_invoice and not res_ids:
            raise AccessError(self.env._("Select an invoice to print."))
        return restricted_invoice

    def _get_rendering_context(self, report, docids, data):
        self._jamel_check_report(report, docids)
        return super()._get_rendering_context(report, docids, data)

    def _render_qweb_html(self, report_ref, docids, data=None):
        if self._jamel_check_report(report_ref, docids):
            # Only the validated invoice IDs reach the trusted standard template.
            return super(IrActionsReport, self.sudo())._render_qweb_html(report_ref, docids, data={})
        return super()._render_qweb_html(report_ref, docids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if self._jamel_check_report(report_ref, res_ids):
            report = self.with_context(report_pdf_no_attachment=True).sudo()
            return super(IrActionsReport, report)._render_qweb_pdf(report_ref, res_ids=res_ids, data={})
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _render_qweb_text(self, report_ref, docids, data=None):
        if self._jamel_check_report(report_ref, docids):
            return super(IrActionsReport, self.sudo())._render_qweb_text(report_ref, docids, data={})
        return super()._render_qweb_text(report_ref, docids, data=data)
