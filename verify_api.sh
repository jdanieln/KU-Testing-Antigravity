#!/bin/bash

# This script attempts to simulate the login flow
# 1. It gets a custom token (simulated) - hard to do without client SDK
# Instead, we will making a direct request to the backend assuming we had a token
# But since we can't easily get a valid Firebase ID token from CLI without API Key interaction...
# We will just test the endpoint connectivity.

echo "Testing connectivity to backend..."
curl -v http://localhost:5001/api/health

echo "Testing OPTIONS preflight..."
curl -v -X OPTIONS http://localhost:5001/api/auth/sync \
-H "Origin: http://localhost:5173" \
-H "Access-Control-Request-Method: POST" \
-H "Access-Control-Request-Headers: Authorization, Content-Type"
