# Frontend Auth Security - ISO Smart

Date: 2026-07-03

## Current Risk

The frontend stores JWT tokens in `localStorage`. This is accepted only for controlled demo and limited paid pilot use. It blocks formal production because successful XSS could read bearer tokens.

## Pilot Mitigations

- Logout clears access and refresh tokens.
- Refresh/auth failures must clear stale tokens.
- Tokens must never be logged.
- CSP must be enabled in staging/pilot.
- Only trusted pilot users and authorized pilot data are allowed.
- Local auth bypass and local fallback flags must stay disabled outside development/demo.

## Recommended CSP

```text
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' https://adminapps.example.com https://isosmart.example.com;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

## Future Plan

Move token handling to HttpOnly, Secure, SameSite cookies with CSRF protection for unsafe methods. Bearer-token compatibility should remain only for development during the migration window.

## Release Position

This risk does not block a controlled demo or limited paid pilot with disclosure. It blocks formal production and regulated production.

