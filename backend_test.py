import requests
import sys
import json
from datetime import datetime

class RitualsAPITester:
    def __init__(self, base_url="https://mystic-services-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_get_rituais(self):
        """Test getting all rituais"""
        success, response = self.run_test("Get All Rituais", "GET", "rituais", 200)
        
        if success and response:
            print(f"   Found {len(response)} rituais")
            expected_rituais = ["amarracao-forte", "volta-do-amor", "desamarre", "protecao-espiritual"]
            found_ids = [r.get('id') for r in response]
            
            for expected_id in expected_rituais:
                if expected_id in found_ids:
                    print(f"   ✅ Found ritual: {expected_id}")
                else:
                    print(f"   ❌ Missing ritual: {expected_id}")
                    
            # Check prices
            for ritual in response:
                if ritual.get('id') == 'amarracao-forte' and ritual.get('preco') == 97.0:
                    print(f"   ✅ Amarração Forte price correct: R${ritual.get('preco')}")
                elif ritual.get('id') == 'volta-do-amor' and ritual.get('preco') == 127.0:
                    print(f"   ✅ Volta do Amor price correct: R${ritual.get('preco')}")
                elif ritual.get('id') == 'desamarre' and ritual.get('preco') == 87.0:
                    print(f"   ✅ Desamarre price correct: R${ritual.get('preco')}")
                elif ritual.get('id') == 'protecao-espiritual' and ritual.get('preco') == 67.0:
                    print(f"   ✅ Proteção Espiritual price correct: R${ritual.get('preco')}")
        
        return success, response

    def test_get_specific_ritual(self, ritual_id):
        """Test getting a specific ritual"""
        success, response = self.run_test(f"Get Ritual {ritual_id}", "GET", f"rituais/{ritual_id}", 200)
        
        if success and response:
            print(f"   Ritual Name: {response.get('nome')}")
            print(f"   Price: R${response.get('preco')}")
            print(f"   Description: {response.get('descricao', '')[:50]}...")
        
        return success, response

    def test_checkout_creation(self, ritual_id):
        """Test creating a checkout session"""
        checkout_data = {
            "ritual_id": ritual_id,
            "host_url": self.base_url
        }
        
        success, response = self.run_test("Create Checkout Session", "POST", "checkout", 200, checkout_data)
        
        if success and response:
            if 'session_id' in response:
                self.session_id = response['session_id']
                print(f"   Session ID: {self.session_id}")
            if 'url' in response:
                print(f"   Checkout URL: {response['url'][:50]}...")
        
        return success, response

    def test_checkout_status(self):
        """Test getting checkout status"""
        if not self.session_id:
            print("❌ No session ID available for status check")
            return False, {}
            
        return self.run_test("Get Checkout Status", "GET", f"checkout/status/{self.session_id}", 200)

    def test_create_client_without_payment(self):
        """Test creating client without valid payment (should fail)"""
        client_data = {
            "nome_completo": "Test User",
            "email": "test@example.com",
            "telefone": "(11) 99999-9999",
            "nome_pessoa_amada": "Test Love",
            "data_nascimento": "1990-01-01",
            "informacoes_adicionais": "Test info"
        }
        
        # This should fail because payment is not confirmed
        success, response = self.run_test("Create Client (No Payment)", "POST", "clientes", 400, 
                                        client_data, params={"session_id": "fake_session_id"})
        
        # For this test, failure is expected (400 status)
        if not success:
            print("   ✅ Correctly rejected client creation without valid payment")
            return True, response
        else:
            print("   ❌ Should have rejected client creation without valid payment")
            return False, response

    def test_admin_pedidos(self):
        """Test getting admin orders"""
        return self.run_test("Get Admin Orders", "GET", "admin/pedidos", 200)

    def test_invalid_ritual_id(self):
        """Test getting non-existent ritual"""
        success, response = self.run_test("Get Invalid Ritual", "GET", "rituais/invalid-id", 404)
        
        # For this test, failure is expected (404 status)
        if not success:
            print("   ✅ Correctly returned 404 for invalid ritual ID")
            return True, response
        else:
            print("   ❌ Should have returned 404 for invalid ritual ID")
            return False, response

def main():
    print("🚀 Starting Rituais API Testing...")
    print("=" * 60)
    
    tester = RitualsAPITester()
    
    # Test basic endpoints
    print("\n📋 BASIC API TESTS")
    print("-" * 30)
    tester.test_root_endpoint()
    
    # Test rituais endpoints
    print("\n🔮 RITUAIS ENDPOINTS")
    print("-" * 30)
    success, rituais = tester.test_get_rituais()
    
    if success and rituais:
        # Test specific rituais
        ritual_ids = ["amarracao-forte", "volta-do-amor", "desamarre", "protecao-espiritual"]
        for ritual_id in ritual_ids:
            tester.test_get_specific_ritual(ritual_id)
    
    # Test invalid ritual
    tester.test_invalid_ritual_id()
    
    # Test checkout functionality
    print("\n💳 CHECKOUT TESTS")
    print("-" * 30)
    tester.test_checkout_creation("amarracao-forte")
    tester.test_checkout_status()
    
    # Test client creation (should fail without payment)
    print("\n👤 CLIENT TESTS")
    print("-" * 30)
    tester.test_create_client_without_payment()
    
    # Test admin endpoints
    print("\n👨‍💼 ADMIN TESTS")
    print("-" * 30)
    tester.test_admin_pedidos()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())