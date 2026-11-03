from odoo.tests import TransactionCase, tagged
from odoo.tools.safe_eval import safe_eval


@tagged("post_install", "-at_install")
class TestCommunityCatalog(TransactionCase):
    def test_apps_exclude_paid_modules(self):
        domain = safe_eval(self.env.ref("base.open_module_tree").domain or "[]")
        visible = self.env["ir.module.module"].search(domain)
        paid = visible.filtered(
            lambda module: module.to_buy or module.license in ("OEEL-1", "OPL-1")
        )
        self.assertFalse(paid, paid.mapped("name"))
        self.assertIn(self.env.ref("base.module_web"), visible)
        self.assertIn(self.env.ref("base.module_base"), visible)
