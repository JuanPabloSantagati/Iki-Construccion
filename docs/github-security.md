# Configuración manual de GitHub

Estas opciones no se pueden versionar en el repo: las activa el dueño desde
**Settings** de `JuanPabloSantagati/Iki-Construccion`. Marcar cada una al hacerla.

## Acceso

- [ ] **Collaborators**: invitar al otro socio con rol *Write* (no *Admin*, salvo que haga falta).
- [ ] Ambos con **2FA** activado en su cuenta de GitHub.

## Rama `main` (Settings → Rules → Rulesets → New branch ruleset)

Target: `main` · Enforcement: *Active*.

- [ ] Restrict deletions
- [ ] Block force pushes
- [ ] Require a pull request before merging
  - [ ] Required approvals: **1**
  - [ ] Dismiss stale pull request approvals when new commits are pushed
  - [ ] Require conversation resolution before merging
- [ ] Require status checks to pass (después de la primera corrida de CI aparecen):
  `Lint (ruff)`, `Detección de secretos (gitleaks)`, `Tests + check --deploy`,
  `Vulnerabilidades en dependencias (pip-audit)`
  - [ ] Require branches to be up to date before merging
- [ ] Sin *bypass list* (las reglas aplican también a los admins)

## General (Settings → General → Pull Requests)

- [ ] Permitir solo **Squash merging** (desactivar merge commits y rebase)
- [ ] **Automatically delete head branches**

## Code security (Settings → Advanced Security / Code security)

- [ ] Dependency graph
- [ ] **Dependabot alerts**
- [ ] **Dependabot security updates**
- [ ] (Las *version updates* las define `.github/dependabot.yml`)
- [ ] **Secret scanning**
- [ ] **Push protection** (bloquea el push si detecta un secreto)
- [ ] **Private vulnerability reporting** (lo usa `SECURITY.md`)
- [ ] CodeQL default setup (opcional, gratis en repos públicos)

## Actions (Settings → Actions → General)

- [ ] Actions permissions: *Allow JuanPabloSantagati, and select non-JuanPabloSantagati,
      actions* → solo **Allow actions created by GitHub** (hoy solo usamos `actions/*`)
- [ ] **Require approval for all external contributors** en workflows de forks
- [ ] Workflow permissions: **Read repository contents** (no read/write)
- [ ] Desactivar *Allow GitHub Actions to create and approve pull requests*

## Secrets

- El CI actual **no usa secretos**. Si en el futuro se agrega un deploy desde Actions:
  usar **Environments** (`production`) con *required reviewers*, nunca exponer secretos a
  workflows disparados por PRs, y nunca usar `pull_request_target`.
