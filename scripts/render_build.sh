#!/usr/bin/env bash
# Build de Render: dependencias con hashes, CSS de Tailwind y estáticos.
# Las migraciones corren aparte (preDeployCommand en render.yaml).
set -euo pipefail

python -m pip install --require-hashes -r requirements/base.txt
./scripts/build_css.sh
python manage.py collectstatic --noinput
