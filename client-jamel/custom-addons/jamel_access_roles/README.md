# Jamel access roles

Odoo 20 Community roles, enforced using native `ir.access` restrictions and
targeted model/report guards. Role markers are mutually exclusive and cannot
be combined with Settings or Access Rights administration.

| Role | Allowed | Excluded |
| --- | --- | --- |
| prof | Accounting, inventory, purchase and product administration; contacts | User, group, security and technical administration |
| fan | Contacts, accounting setup, financial reports, journal entries | Invoices, invoice analytics, supplier/customer orders |
| log | Read/print invoices; receive, deliver and transfer inventory | Invoice changes, payments, ledger entries, financial reports, contact creation |
| super | Contacts, read/print invoices, supplier RFQs and purchase orders | Invoice changes, vendor-bill creation, payments, ledger entries and financial reports |

Invoice readers can read printable product/section/note lines, but cannot query
receivable, payable or tax journal lines. The standard invoice report receives
only invoice IDs validated against the real user's read permissions; its
trusted rendering can access internal lines needed to produce the PDF. Report
validation covers HTML, PDF and text, including sudoed report-controller calls.

The addon depends on Community `account`, `l10n_jo`, and `purchase_stock`.
Install or upgrade it with `-i jamel_access_roles` / `-u jamel_access_roles`, then
restart the web service. Assign exactly one role marker to each account and
set its allowed companies explicitly. Credentials are never stored in the addon.

Validation on a disposable Odoo 20 database: 12 tests passed. The suite covers
real PDF generation, confirmed supplier orders, completed warehouse movements,
journal posting, forbidden CRUD, analytical/report bypasses and self-elevation.

```sh
odoo -d disposable_roles_test -i jamel_access_roles --test-enable \
  --test-tags /jamel_access_roles --stop-after-init --no-http --without-demo=all
```
