# Jamel — Odoo Community

The Apps catalog excludes Enterprise upgrade cards (`to_buy`) and modules
licensed `OEEL-1` or `OPL-1`. Community applications remain available.
This does not uninstall existing applications, delete their business data,
or remove optional paid services from otherwise free applications.

Set `ODOO_DATABASE` in `.env` to Jamel's Odoo database (default: `ahmed_db`).
`POSTGRES_DB` is PostgreSQL's bootstrap database and is separate.

Run `docker compose up -d` from this directory. At normal web startup,
`start-community.sh` installs `jamel_community_only` before serving requests.
Other clients do not mount this addon. Explicit Odoo commands passed with
`docker compose run --rm web odoo ...` bypass the startup initialization.

The addon test checks that the Apps action excludes paid modules while
keeping the free `base` and `web` modules visible. Run on a disposable database:

```sh
docker compose run --rm web odoo -d jamel_catalog_test \
  -i jamel_community_only --test-enable --test-tags /jamel_community_only \
  --stop-after-init --no-http --without-demo=all
```
