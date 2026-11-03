#!/bin/bash
set -euo pipefail

if [[ "$#" -eq 1 && "$1" == "odoo" ]]; then
    /entrypoint.sh odoo --database "${ODOO_DATABASE:?Set ODOO_DATABASE to the Jamel database}" \
        --init jamel_community_only --stop-after-init --no-http
fi

exec /entrypoint.sh "$@"
