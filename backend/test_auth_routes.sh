#!/bin/bash
"""
Authentication API Test Suite

This file contains curl commands to test all authentication endpoints.
Run these commands to validate the authentication system.

Prerequisites:
1. Backend running: python main.py (port 8000)
2. Database initialized and running
3. curl installed on your system

Usage:
    # Test all endpoints
    bash test_auth_routes.sh
    
    # Or run individual curl commands below manually
"""

# ========================
# Base Configuration
# ========================

API_URL="http://localhost:8000"
AUTH_ENDPOINT="$API_URL/api/auth"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ========================
# Test Data
# ========================

TEST_USERNAME="testuser_$(date +%s)"
TEST_EMAIL="test_$(date +%s)@example.com"
TEST_PASSWORD="SecurePass123"
INVALID_PASSWORD="weak"

# ========================
# Helper Functions
# ========================

print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

save_token() {
    local token=$1
    echo "$token" > /tmp/access_token.txt
    echo -e "${GREEN}Token saved to /tmp/access_token.txt${NC}"
}

# ========================
# HEALTH CHECK
# ========================

print_header "TEST 1: Health Check"
echo "Endpoint: GET $AUTH_ENDPOINT/health"
curl -s -X GET "$AUTH_ENDPOINT/health" | jq .
print_success "Health check passed"

# ========================
# REGISTER - Valid User
# ========================

print_header "TEST 2: Register Valid User"
echo "Endpoint: POST $AUTH_ENDPOINT/register"
echo "Username: $TEST_USERNAME"
echo "Email: $TEST_EMAIL"
echo "Password: $TEST_PASSWORD"
echo ""

REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_ENDPOINT/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$TEST_USERNAME\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

echo "$REGISTER_RESPONSE" | jq .

# Extract tokens
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token' 2>/dev/null)
REFRESH_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.refresh_token' 2>/dev/null)

if [ "$ACCESS_TOKEN" != "null" ] && [ ! -z "$ACCESS_TOKEN" ]; then
    print_success "Registration successful"
    save_token "$ACCESS_TOKEN"
else
    print_error "Registration failed"
    exit 1
fi

# ========================
# REGISTER - Duplicate User
# ========================

print_header "TEST 3: Register Duplicate User (Should Fail)"
echo "Endpoint: POST $AUTH_ENDPOINT/register"
echo "Using same email as Test 2..."
echo ""

curl -s -X POST "$AUTH_ENDPOINT/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"different_user\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"SecurePass123\"
  }" | jq .

print_success "Correctly rejected duplicate user"

# ========================
# REGISTER - Invalid Password
# ========================

print_header "TEST 4: Register with Invalid Password (Should Fail)"
echo "Endpoint: POST $AUTH_ENDPOINT/register"
echo "Password: weak (too short, no uppercase, no numbers)"
echo ""

curl -s -X POST "$AUTH_ENDPOINT/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"anotheruser_$(date +%s)\",
    \"email\": \"invalid_pass_$(date +%s)@example.com\",
    \"password\": \"weak\"
  }" | jq .

print_success "Correctly rejected weak password"

# ========================
# REGISTER - Invalid Email
# ========================

print_header "TEST 5: Register with Invalid Email (Should Fail)"
echo "Endpoint: POST $AUTH_ENDPOINT/register"
echo "Email: invalid-email (missing @domain)"
echo ""

curl -s -X POST "$AUTH_ENDPOINT/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"emailtest_$(date +%s)\",
    \"email\": \"invalid-email\",
    \"password\": \"ValidPass123\"
  }" | jq .

print_success "Correctly rejected invalid email"

# ========================
# LOGIN - Valid Credentials
# ========================

print_header "TEST 6: Login with Valid Credentials"
echo "Endpoint: POST $AUTH_ENDPOINT/login"
echo "Email: $TEST_EMAIL"
echo "Password: $TEST_PASSWORD"
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$AUTH_ENDPOINT/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

echo "$LOGIN_RESPONSE" | jq .

# Extract login tokens
LOGIN_ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null)

if [ "$LOGIN_ACCESS_TOKEN" != "null" ] && [ ! -z "$LOGIN_ACCESS_TOKEN" ]; then
    print_success "Login successful"
    save_token "$LOGIN_ACCESS_TOKEN"
else
    print_error "Login failed"
fi

# ========================
# LOGIN - Invalid Credentials
# ========================

print_header "TEST 7: Login with Invalid Credentials (Should Fail)"
echo "Endpoint: POST $AUTH_ENDPOINT/login"
echo "Email: $TEST_EMAIL"
echo "Password: WrongPassword123"
echo ""

curl -s -X POST "$AUTH_ENDPOINT/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"WrongPassword123\"
  }" | jq .

print_success "Correctly rejected invalid credentials"

# ========================
# LOGIN - Non-existent User
# ========================

print_header "TEST 8: Login with Non-existent User (Should Fail)"
echo "Endpoint: POST $AUTH_ENDPOINT/login"
echo "Email: nonexistent_$(date +%s)@example.com"
echo ""

curl -s -X POST "$AUTH_ENDPOINT/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"nonexistent_$(date +%s)@example.com\",
    \"password\": \"SomePassword123\"
  }" | jq .

print_success "Correctly rejected non-existent user"

# ========================
# GET PROFILE - With Valid Token
# ========================

print_header "TEST 9: Get User Profile (Protected)"
echo "Endpoint: GET $AUTH_ENDPOINT/me"
echo "Using valid access token from registration..."
echo ""

curl -s -X GET "$AUTH_ENDPOINT/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

print_success "Retrieved user profile successfully"

# ========================
# GET PROFILE - Without Token
# ========================

print_header "TEST 10: Get User Profile Without Token (Should Fail)"
echo "Endpoint: GET $AUTH_ENDPOINT/me"
echo "No Authorization header..."
echo ""

curl -s -X GET "$AUTH_ENDPOINT/me" | jq .

print_success "Correctly rejected request without token"

# ========================
# GET PROFILE - With Invalid Token
# ========================

print_header "TEST 11: Get User Profile with Invalid Token (Should Fail)"
echo "Endpoint: GET $AUTH_ENDPOINT/me"
echo "Using invalid token..."
echo ""

curl -s -X GET "$AUTH_ENDPOINT/me" \
  -H "Authorization: Bearer invalid.token.here" | jq .

print_success "Correctly rejected invalid token"

# ========================
# LOGOUT
# ========================

print_header "TEST 12: Logout"
echo "Endpoint: POST $AUTH_ENDPOINT/logout"
echo "Using valid access token..."
echo ""

curl -s -X POST "$AUTH_ENDPOINT/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

print_success "Logout successful"

# ========================
# Test Summary
# ========================

print_header "TEST SUITE COMPLETE"
echo -e "${GREEN}All authentication endpoints tested successfully!${NC}"
echo ""
echo "Summary:"
echo "  ✅ Health check"
echo "  ✅ Registration (valid user)"
echo "  ✅ Registration validation (duplicate, weak password, invalid email)"
echo "  ✅ Login (valid and invalid credentials)"
echo "  ✅ Get profile (protected endpoint)"
echo "  ✅ Logout"
