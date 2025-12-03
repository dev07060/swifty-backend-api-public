#!/bin/bash
# Test script for Toss Auth API endpoints using curl
# Make sure your backend is running on port 8080

BASE_URL="http://localhost:8080"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║          Toss Auth API - Local Test Script              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo "============================================================"
echo "  Health Check"
echo "============================================================"
echo ""
echo "Checking if backend is running..."
if curl -s -f "$BASE_URL/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running on $BASE_URL${NC}"
    echo "   API Docs: $BASE_URL/docs"
else
    echo -e "${RED}❌ Backend is not running!${NC}"
    echo "   Start it with: uvicorn main:app --reload --port 8080"
    exit 1
fi

# Test 2: Request Authentication
echo ""
echo "============================================================"
echo "  TEST 1: Request Authentication"
echo "============================================================"
echo ""
echo "POST $BASE_URL/api/toss-auth/request"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/toss-auth/request" \
  -H "Content-Type: application/json")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "Status Code: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ Success!${NC}"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    
    # Extract txId
    TX_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['txId'])" 2>/dev/null)
    
    if [ -n "$TX_ID" ]; then
        echo ""
        echo -e "${BLUE}📝 Received txId: $TX_ID${NC}"
        echo "   You can now use this txId in the mobile app!"
        
        # Save txId to file for later use
        echo "$TX_ID" > /tmp/toss_tx_id.txt
        
        # Test 3: Check Status
        echo ""
        echo "============================================================"
        echo "  TEST 2: Check Auth Status"
        echo "============================================================"
        echo ""
        echo "GET $BASE_URL/api/toss-auth/status/$TX_ID"
        echo ""
        
        sleep 1
        
        STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/toss-auth/status/$TX_ID")
        STATUS_CODE=$(echo "$STATUS_RESPONSE" | tail -n 1)
        STATUS_BODY=$(echo "$STATUS_RESPONSE" | sed '$d')
        
        echo "Status Code: $STATUS_CODE"
        echo ""
        
        if [ "$STATUS_CODE" -eq 200 ]; then
            echo -e "${GREEN}✅ Success!${NC}"
            echo "$STATUS_BODY" | python3 -m json.tool 2>/dev/null || echo "$STATUS_BODY"
        else
            echo -e "${RED}❌ Failed!${NC}"
            echo "$STATUS_BODY"
        fi
        
        # Test 4: Get Result (will likely fail)
        echo ""
        echo "============================================================"
        echo "  TEST 3: Get Auth Result"
        echo "============================================================"
        echo ""
        echo "POST $BASE_URL/api/toss-auth/result/$TX_ID"
        echo -e "${YELLOW}⚠️  Note: This will fail if user hasn't completed auth in Toss app yet${NC}"
        echo ""
        
        RESULT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/toss-auth/result/$TX_ID" \
          -H "Content-Type: application/json")
        RESULT_CODE=$(echo "$RESULT_RESPONSE" | tail -n 1)
        RESULT_BODY=$(echo "$RESULT_RESPONSE" | sed '$d')
        
        echo "Status Code: $RESULT_CODE"
        echo ""
        
        if [ "$RESULT_CODE" -eq 200 ]; then
            echo -e "${GREEN}✅ Success! User data retrieved:${NC}"
            echo "$RESULT_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESULT_BODY"
        elif [ "$RESULT_CODE" -eq 400 ]; then
            echo -e "${YELLOW}⏳ Expected - Authentication not completed yet${NC}"
            echo "$RESULT_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESULT_BODY"
        else
            echo -e "${RED}❌ Failed!${NC}"
            echo "$RESULT_BODY"
        fi
    fi
else
    echo -e "${RED}❌ Failed!${NC}"
    echo "$BODY"
fi

# Summary
echo ""
echo "============================================================"
echo "  Summary"
echo "============================================================"
echo ""
echo "✅ Test 1: Request Auth - Check if endpoint returns txId"
echo "✅ Test 2: Check Status - Verify status endpoint works"
echo "⚠️  Test 3: Get Result - Expected to fail until user completes auth"
echo ""
echo "ℹ️  To complete the flow:"
echo "   1. Use the txId in your mobile app"
echo "   2. Complete authentication in Toss app"
echo "   3. Run this script again or manually test:"
echo "      curl -X POST $BASE_URL/api/toss-auth/result/\$TX_ID"
echo ""

if [ -f /tmp/toss_tx_id.txt ]; then
    echo "💾 TxId saved to: /tmp/toss_tx_id.txt"
    echo ""
fi
