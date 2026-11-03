from odoo import Command, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestJamelRoles(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.jo")
        cls.env["account.chart.template"].try_loading("jo_standard", cls.env.company)
        cls.users = {}
        for role in ("prof", "fan", "log", "super"):
            cls.users[role] = cls.env["res.users"].with_context(
                no_reset_password=True, mail_create_nosubscribe=True
            ).create({
                "name": "Test " + role,
                "login": "jamel_test_" + role,
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.set(cls.env.ref("jamel_access_roles.group_" + role).ids)],
            })
        cls.partner = cls.env["res.partner"].create({"name": "Jamel role test contact"})
        cls.product = cls.env["product.product"].create({
            "name": "Jamel role test product", "type": "consu", "is_storable": True,
        })
        cls.invoice = cls.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": cls.partner.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [Command.create({
                "name": "Test invoice line", "product_id": cls.product.id,
                "quantity": 1, "price_unit": 100, "tax_ids": [Command.clear()],
            })],
        })
        cls.bill = cls.env["account.move"].create({
            "move_type": "in_invoice", "partner_id": cls.partner.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [Command.create({
                "name": "Test bill line", "product_id": cls.product.id,
                "quantity": 1, "price_unit": 50, "tax_ids": [Command.clear()],
            })],
        })
        cls.journal = cls.env["account.journal"].search([
            ("company_id", "=", cls.env.company.id), ("type", "=", "general")
        ], limit=1)
        cls.entry = cls.env["account.move"].create({"move_type": "entry", "journal_id": cls.journal.id})

    def test_fan_contacts_and_journals_but_no_invoices_or_orders(self):
        user = self.users["fan"]
        self.partner.with_user(user).write({"phone": "12345"})
        self.entry.with_user(user).write({"ref": "fan allowed"})
        self.assertEqual(self.entry.with_user(user).read(["ref"])[0]["ref"], "fan allowed")
        for document in (self.invoice, self.bill):
            with self.assertRaises(AccessError):
                document.with_user(user).read(["name"])
            with self.assertRaises(AccessError):
                document.invoice_line_ids.with_user(user).read(["name"])
        self.assertFalse(self.env["account.move"].with_user(user).search([("move_type", "!=", "entry")]))
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env["account.move"].with_user(user).create({"move_type": "out_invoice", "partner_id": self.partner.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env["purchase.order"].with_user(user).create({"partner_id": self.partner.id})
        self.assertTrue(self.env["account.tax"].with_user(user).search([], limit=1))

    def test_invoice_readers_cannot_mutate_or_access_journals(self):
        for role in ("log", "super"):
            user = self.users[role]
            self.assertEqual(self.invoice.with_user(user).read(["move_type"])[0]["move_type"], "out_invoice")
            self.assertTrue(self.invoice.invoice_line_ids.with_user(user).read(["name", "price_subtotal"]))
            with self.assertRaises(AccessError):
                self.entry.with_user(user).read(["name"])
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.invoice.with_user(user).write({"ref": "forbidden"})
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.invoice.with_user(user).action_post()
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.invoice.with_user(user).unlink()
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.env["account.move"].with_user(user).create({"move_type": "out_invoice", "partner_id": self.partner.id})
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.invoice.invoice_line_ids.with_user(user).write({"price_unit": 1})
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.env["account.payment"].with_user(user).create({"amount": 1, "partner_id": self.partner.id})
            self.assertFalse(self.env["account.move"].with_user(user).search([("move_type", "=", "entry")]))

    def test_invoice_printing_and_financial_reports(self):
        for role in ("log", "super"):
            reports = self.env["ir.actions.report"].with_user(self.users[role])
            content, kind = reports._render_qweb_html("jamel_access_roles.action_invoice_pdf", self.invoice.ids)
            self.assertEqual(kind, "html")
            self.assertIn(b"Test invoice line", content)
            with self.assertRaises(AccessError):
                reports._render_qweb_html("account.action_report_account_hash_integrity", self.env.company.ids)
        with self.assertRaises(AccessError):
            self.env["ir.actions.report"].with_user(self.users["fan"])._render_qweb_html(
                "account.account_invoices_without_payment", self.invoice.ids
            )
        with self.assertRaises(AccessError):
            self.env["ir.actions.report"].with_user(self.users["fan"]).sudo()._render_qweb_html(
                "account.account_invoices_without_payment", self.invoice.ids
            )

    def test_actual_invoice_pdf_for_print_roles(self):
        for role in ("log", "super"):
            content, kind = self.env["ir.actions.report"].with_user(self.users[role]).with_context(
                force_report_rendering=True, report_pdf_no_attachment=True
            )._render_qweb_pdf("jamel_access_roles.action_invoice_pdf", self.invoice.ids)
            self.assertEqual(kind, "pdf")
            self.assertTrue(content.startswith(b"%PDF"))

    def test_fan_can_create_and_post_entry(self):
        expense = self.bill.invoice_line_ids.account_id
        revenue = self.invoice.invoice_line_ids.account_id
        entry = self.env["account.move"].with_user(self.users["fan"]).create({
            "move_type": "entry", "journal_id": self.journal.id,
            "line_ids": [
                Command.create({"name": "fan debit", "account_id": expense.id, "debit": 10}),
                Command.create({"name": "fan credit", "account_id": revenue.id, "credit": 10}),
            ],
        })
        entry.action_post()
        self.assertEqual(entry.state, "posted")

    def test_super_supplier_orders_but_no_vendor_bills(self):
        user = self.users["super"]
        self.partner.with_user(user).write({"phone": "super contact"})
        order = self.env["purchase.order"].with_user(user).create({
            "partner_id": self.partner.id,
            "order_line": [Command.create({
                "product_id": self.product.id, "name": self.product.name,
                "product_qty": 1, "price_unit": 50, "date_planned": fields.Datetime.now(),
            })],
        })
        order.button_confirm()
        self.assertEqual(order.state, "purchase")
        with self.assertRaises(AccessError):
            order.action_create_invoice()

    def test_log_completes_receipt_delivery_and_transfer(self):
        user = self.users["log"]
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        supplier = self.env.ref("stock.stock_location_suppliers")
        customer = self.env.ref("stock.stock_location_customers")
        secondary = self.env["stock.location"].create({"name": "Role test shelf", "usage": "internal", "location_id": warehouse.view_location_id.id})
        operations = (
            (warehouse.in_type_id, supplier, warehouse.lot_stock_id),
            (warehouse.out_type_id, warehouse.lot_stock_id, customer),
            (warehouse.int_type_id, warehouse.lot_stock_id, secondary),
        )
        for picking_type, source, destination in operations:
            picking = self.env["stock.picking"].with_user(user).create({
                "picking_type_id": picking_type.id, "location_id": source.id,
                "location_dest_id": destination.id,
                "move_ids": [Command.create({
                    "product_id": self.product.id, "product_uom_qty": 1,
                    "uom_id": self.product.uom_id.id,
                    "location_id": source.id, "location_dest_id": destination.id,
                })],
            })
            picking.action_confirm()
            picking.move_ids.write({"quantity": 1, "picked": True})
            picking.with_context(skip_backorder=True).button_validate()
            self.assertEqual(picking.state, "done")
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env["res.partner"].with_user(user).create({"name": "Not allowed"})

    def test_prof_business_admin_without_user_or_security_admin(self):
        user = self.users["prof"]
        for group in ("account.group_account_manager", "stock.group_stock_manager", "purchase.group_purchase_manager"):
            self.assertTrue(user.has_group(group))
        for group in ("base.group_system", "base.group_erp_manager"):
            self.assertFalse(user.has_group(group))
        self.invoice.with_user(user).write({"ref": "prof allowed"})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env["res.users"].with_user(user).create({"name": "Forbidden", "login": "forbidden"})
        with self.assertRaises(AccessError), self.cr.savepoint():
            user.with_user(user).write({"group_ids": [Command.link(self.env.ref("base.group_system").id)]})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env.ref("jamel_access_roles.group_prof").with_user(user).write({"implied_ids": [Command.link(self.env.ref("base.group_system").id)]})
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env["ir.access"].with_user(user).create({"name": "Forbidden", "model_id": self.env.ref("base.model_res_users").id, "group_id": self.env.ref("base.group_user").id, "operation": "crud"})

    def test_roles_cannot_be_combined_or_self_elevated(self):
        user = self.users["super"]
        with self.assertRaises(ValidationError), self.cr.savepoint():
            user.write({"group_ids": [Command.link(self.env.ref("jamel_access_roles.group_fan").id)]})
        for role, user in self.users.items():
            with self.assertRaises(AccessError), self.cr.savepoint():
                user.with_user(user).write({"group_ids": [Command.link(self.env.ref("base.group_erp_manager").id)]})

    def test_invoice_accounting_lines_are_hidden(self):
        ledger_lines = self.invoice.line_ids - self.invoice.invoice_line_ids
        self.assertTrue(ledger_lines)
        for role in ("log", "super"):
            with self.assertRaises(AccessError):
                ledger_lines.with_user(self.users[role]).read(["debit", "credit", "account_id"])

    def test_fan_cannot_read_invoice_analytics(self):
        report = self.env["account.invoice.report"]
        self.assertTrue(report.search([("move_id", "=", self.invoice.id)]))
        self.assertFalse(report.with_user(self.users["fan"]).search([("move_id", "=", self.invoice.id)]))

    def test_text_reports_cannot_bypass_whitelist(self):
        self.env["ir.ui.view"].create({
            "name": "Jamel forbidden report test", "type": "qweb",
            "key": "jamel_access_roles.test_forbidden_report",
            "arch": '<t t-name="jamel_access_roles.test_forbidden_report"><p>Restricted financial report</p></t>',
        })
        report = self.env["ir.actions.report"].create({
            "name": "Forbidden report fixture", "model": "res.company",
            "report_type": "qweb-text", "report_name": "jamel_access_roles.test_forbidden_report",
        })
        for role in ("log", "super"):
            with self.assertRaises(AccessError):
                self.env["ir.actions.report"].with_user(self.users[role])._render_qweb_text(report, self.env.company.ids)
