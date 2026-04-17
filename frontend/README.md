# React + Vite

## Linea Base UI/UX + Prompt

Estandar operativo para evolucion frontend (compatibilidad, i18n, accesibilidad, IA UX y checklist de PR):

- [../docs/internal/FRONTEND_LINEA_BASE_Y_PROMPT.md](../docs/internal/FRONTEND_LINEA_BASE_Y_PROMPT.md)
- [../docs/internal/SMART3AI_FRONTEND_BASELINE_UNIFICADA.md](../docs/internal/SMART3AI_FRONTEND_BASELINE_UNIFICADA.md)

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## E2E I18N Smoke

Runtime multilingual smoke test for login, dashboard, and onboarding:

```bash
npm run test:i18n:smoke
```

Expected environment:

- Frontend reachable at `BASE_URL` (default `http://127.0.0.1:3001`)
- Backend auth endpoints available through `/api` proxy
- Credentials via env vars (defaults):
	- `TEST_EMAIL=admin@isosmart.local`
	- `TEST_PASSWORD=Admin@123456`

Install Playwright browser if needed:

```bash
npm run test:e2e:install
```
