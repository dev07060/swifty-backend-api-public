#!/usr/bin/env python3
"""
Test script for Toss Auth API endpoints
Run this to verify your local backend is working correctly
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_auth_request():
    """Test Step 1: Request authentication"""
    print_section("TEST 1: Request Authentication")
    
    url = f"{BASE_URL}/api/toss-auth/request"
    print(f"POST {url}")
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data.get('txId')
        else:
            print(f"❌ Failed!")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_auth_status(tx_id):
    """Test Step 2: Check authentication status"""
    print_section("TEST 2: Check Auth Status")
    
    if not tx_id:
        print("⚠️  Skipping - no txId available")
        return
    
    url = f"{BASE_URL}/api/toss-auth/status/{tx_id}"
    print(f"GET {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Failed!")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

def test_auth_result(tx_id):
    """Test Step 3: Get authentication result"""
    print_section("TEST 3: Get Auth Result")
    
    if not tx_id:
        print("⚠️  Skipping - no txId available")
        return
    
    url = f"{BASE_URL}/api/toss-auth/result/{tx_id}"
    print(f"POST {url}")
    print("⚠️  Note: This will fail if user hasn't completed auth in Toss app yet")
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif response.status_code == 400:
            print(f"⏳ Expected - auth not completed yet")
            print(response.text)
        else:
            print(f"❌ Failed!")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health_check():
    """Test if backend is running"""
    print_section("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Backend is running on http://localhost:8080")
            print(f"   API Docs: {BASE_URL}/docs")
            return True
        else:
            print(f"⚠️  Backend returned status {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Backend is not running!")
        print("   Start it with: uvicorn main:app --reload --port 8080")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║          Toss Auth API - Local Test Script              ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check if backend is running
    if not test_health_check():
        return
    
    # Test 1: Request auth and get txId
    tx_id = test_auth_request()
    
    if tx_id:
        print(f"\n📝 Received txId: {tx_id}")
        print("   You can now use this txId in the mobile app!")
        
        # Wait a bit before checking status
        time.sleep(1)
        
        # Test 2: Check status
        test_auth_status(tx_id)
        
        # Test 3: Try to get result (will likely fail since user hasn't completed)
        test_auth_result(tx_id)
    
    print_section("Summary")
    print("✅ Test 1: Request Auth - Check if endpoint returns txId")
    print("✅ Test 2: Check Status - Verify status endpoint works")
    print("⚠️  Test 3: Get Result - Expected to fail until user completes auth")
    print("\nℹ️  To complete the flow:")
    print("   1. Use the txId in your mobile app")
    print("   2. Complete authentication in Toss app")
    print("   3. Run Test 3 again to get user data")
    print()

if __name__ == "__main__":
    main()
