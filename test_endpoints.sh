#!/bin/bash
set -e

TOKEN=$(curl -s -X POST "http://127.0.0.1:8001/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@isosmart.local","password":"Admin@123456"}' | jq -r '.access')

echo "TOKEN: $TOKEN"
echo ""
echo "=== TEST: Update Language ==="
curl -s -X POST "http://127.0.0.1:8001/api/settings/update_language/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"organization_id": 1, "preferred_language": "en"}' -w "\nHTTP Status: %{http_code}\n"
