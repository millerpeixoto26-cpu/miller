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
        self.auth_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authorization header if required
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)

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

    def authenticate_admin(self):
        """Authenticate as admin user"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, login_data)
        
        if success and response and 'access_token' in response:
            self.auth_token = response['access_token']
            print(f"   ✅ Admin authenticated successfully")
            print(f"   User: {response.get('user', {}).get('username', 'Unknown')}")
            return True
        else:
            print(f"   ❌ Failed to authenticate admin")
            return False

    def test_instagram_api_config_get(self):
        """Test getting Instagram API configuration"""
        return self.run_test("Get Instagram API Config", "GET", "admin/instagram/api/config", 200, auth_required=True)

    def test_instagram_api_config_post(self):
        """Test saving Instagram API configuration"""
        config_data = {
            "app_id": "test_app_id_12345",
            "app_secret": "test_app_secret_67890",
            "redirect_uri": f"{self.base_url}/admin/instagram/callback",
            "is_active": True
        }
        
        return self.run_test("Save Instagram API Config", "POST", "admin/instagram/api/config", 200, config_data, auth_required=True)

    def test_instagram_api_status(self):
        """Test Instagram API connection status"""
        return self.run_test("Get Instagram API Status", "GET", "admin/instagram/api/status", 200, auth_required=True)

    def test_instagram_api_connect(self):
        """Test Instagram API connect (should generate OAuth URL)"""
        return self.run_test("Instagram API Connect", "GET", "admin/instagram/api/connect", 200, auth_required=True)

    def test_instagram_api_sync_without_connection(self):
        """Test Instagram API sync without connection (should fail)"""
        sync_data = {"sync_type": "both"}
        success, response = self.run_test("Instagram API Sync (No Connection)", "POST", "admin/instagram/api/sync", 400, sync_data, auth_required=True)
        
        # For this test, failure is expected (400 status)
        if not success:
            print("   ✅ Correctly rejected sync without connection")
            return True, response
        else:
            print("   ❌ Should have rejected sync without connection")
            return False, response

    def test_instagram_api_disconnect(self):
        """Test Instagram API disconnect"""
        return self.run_test("Instagram API Disconnect", "DELETE", "admin/instagram/api/disconnect", 200, auth_required=True)

    def test_instagram_api_sync_history(self):
        """Test getting Instagram API sync history"""
        return self.run_test("Get Instagram API Sync History", "GET", "admin/instagram/api/sync/history", 200, auth_required=True)

    def test_instagram_api_config_get_after_save(self):
        """Test getting Instagram API configuration after saving"""
        success, response = self.run_test("Get Instagram API Config (After Save)", "GET", "admin/instagram/api/config", 200, auth_required=True)
        
        if success and response:
            # Check if configuration was saved correctly
            if response.get('app_id') == 'test_app_id_12345':
                print("   ✅ App ID saved correctly")
            else:
                print(f"   ❌ App ID mismatch: expected 'test_app_id_12345', got '{response.get('app_id')}'")
            
            if response.get('app_secret') == '***':
                print("   ✅ App Secret properly masked in response")
            else:
                print(f"   ❌ App Secret not masked: {response.get('app_secret')}")
            
            if self.base_url in response.get('redirect_uri', ''):
                print("   ✅ Redirect URI saved correctly")
            else:
                print(f"   ❌ Redirect URI incorrect: {response.get('redirect_uri')}")
        
        return success, response

    def test_unauthorized_access(self):
        """Test accessing Instagram API endpoints without authentication"""
        # Temporarily remove auth token
        original_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test("Unauthorized Access Test", "GET", "admin/instagram/api/config", 401, auth_required=False)
        
        # Restore auth token
        self.auth_token = original_token
        
        # For this test, failure is expected (401 status)
        if not success:
            print("   ✅ Correctly rejected unauthorized access")
            return True, response
        else:
            print("   ❌ Should have rejected unauthorized access")
            return False, response

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

    def test_sales_dashboard_main(self):
        """Test main sales dashboard endpoint"""
        return self.run_test("Sales Dashboard Main", "GET", "admin/dashboard/vendas", 200, auth_required=True)

    def test_sales_dashboard_consultas(self):
        """Test sales dashboard consultas endpoint"""
        return self.run_test("Sales Dashboard Consultas", "GET", "admin/dashboard/vendas/consultas", 200, auth_required=True)

    def test_get_monthly_goal(self):
        """Test getting monthly goal for current month"""
        from datetime import date
        hoje = date.today()
        return self.run_test(f"Get Monthly Goal {hoje.month}/{hoje.year}", "GET", f"admin/metas/{hoje.month}/{hoje.year}", 200, auth_required=True)

    def test_create_monthly_goal(self):
        """Test creating/updating monthly goal"""
        from datetime import date
        hoje = date.today()
        
        goal_data = {
            "mes": hoje.month,
            "ano": hoje.year,
            "valor_meta": 8000.0
        }
        
        return self.run_test("Create/Update Monthly Goal", "POST", "admin/metas", 200, goal_data, auth_required=True)

    def test_sales_dashboard_comprehensive(self):
        """Comprehensive test of sales dashboard functionality"""
        print("\n🎯 COMPREHENSIVE SALES DASHBOARD TEST")
        print("-" * 50)
        
        # Test main dashboard
        success, dashboard_data = self.test_sales_dashboard_main()
        
        if success and dashboard_data:
            # Validate dashboard structure
            required_keys = ['dia', 'mes', 'meta', 'periodo']
            for key in required_keys:
                if key in dashboard_data:
                    print(f"   ✅ Dashboard has '{key}' section")
                else:
                    print(f"   ❌ Dashboard missing '{key}' section")
            
            # Check day statistics
            if 'dia' in dashboard_data:
                dia_data = dashboard_data['dia']
                if 'rituais' in dia_data and 'consultas' in dia_data and 'total' in dia_data:
                    print(f"   ✅ Day statistics complete")
                    print(f"      Rituais hoje: {dia_data['rituais']['quantidade']} (R${dia_data['rituais']['faturamento']})")
                    print(f"      Consultas hoje: {dia_data['consultas']['quantidade']} (R${dia_data['consultas']['faturamento']})")
                    print(f"      Total hoje: {dia_data['total']['quantidade']} (R${dia_data['total']['faturamento']})")
                else:
                    print(f"   ❌ Day statistics incomplete")
            
            # Check month statistics
            if 'mes' in dashboard_data:
                mes_data = dashboard_data['mes']
                if 'rituais' in mes_data and 'consultas' in mes_data and 'total' in mes_data:
                    print(f"   ✅ Month statistics complete")
                    print(f"      Rituais mês: {mes_data['rituais']['quantidade']} (R${mes_data['rituais']['faturamento']})")
                    print(f"      Consultas mês: {mes_data['consultas']['quantidade']} (R${mes_data['consultas']['faturamento']})")
                    print(f"      Total mês: {mes_data['total']['quantidade']} (R${mes_data['total']['faturamento']})")
                else:
                    print(f"   ❌ Month statistics incomplete")
            
            # Check goal information
            if 'meta' in dashboard_data:
                meta_data = dashboard_data['meta']
                required_meta_keys = ['valor_meta', 'faturamento_atual', 'percentual_atingido', 'falta_para_meta']
                meta_complete = all(key in meta_data for key in required_meta_keys)
                
                if meta_complete:
                    print(f"   ✅ Goal information complete")
                    print(f"      Meta: R${meta_data['valor_meta']}")
                    print(f"      Faturamento atual: R${meta_data['faturamento_atual']}")
                    print(f"      Percentual atingido: {meta_data['percentual_atingido']}%")
                    print(f"      Falta para meta: R${meta_data['falta_para_meta']}")
                    
                    # Validate default goal of R$ 5,000
                    if meta_data['valor_meta'] == 5000.0:
                        print(f"   ✅ Default goal of R$ 5,000 correctly set")
                    else:
                        print(f"   ⚠️  Goal is R${meta_data['valor_meta']}, expected R$ 5,000 default")
                else:
                    print(f"   ❌ Goal information incomplete")
            
            # Check period information
            if 'periodo' in dashboard_data:
                periodo_data = dashboard_data['periodo']
                if 'mes_nome' in periodo_data and 'ano' in periodo_data and 'dia_atual' in periodo_data:
                    print(f"   ✅ Period information complete")
                    print(f"      Período: {periodo_data['mes_nome']} {periodo_data['ano']}, dia {periodo_data['dia_atual']}")
                else:
                    print(f"   ❌ Period information incomplete")
        
        # Test consultas endpoint
        print(f"\n   📋 Testing Consultas List:")
        success_consultas, consultas_data = self.test_sales_dashboard_consultas()
        
        if success_consultas:
            if isinstance(consultas_data, list):
                print(f"   ✅ Consultas endpoint returns list with {len(consultas_data)} items")
                if len(consultas_data) == 0:
                    print(f"   ℹ️  No consultas found (expected for new system)")
                else:
                    # Check structure of first consulta if exists
                    consulta = consultas_data[0]
                    required_consulta_keys = ['id', 'tipo_consulta', 'titulo', 'preco', 'status_pagamento']
                    if all(key in consulta for key in required_consulta_keys):
                        print(f"   ✅ Consulta structure is correct")
                    else:
                        print(f"   ❌ Consulta structure incomplete")
            else:
                print(f"   ❌ Consultas endpoint should return a list")
        
        # Test monthly goal endpoints
        print(f"\n   🎯 Testing Monthly Goals:")
        success_get_goal, goal_data = self.test_get_monthly_goal()
        
        if success_get_goal and goal_data:
            if 'valor_meta' in goal_data:
                print(f"   ✅ Monthly goal retrieved: R${goal_data['valor_meta']}")
            else:
                print(f"   ❌ Monthly goal data incomplete")
        
        # Test creating/updating goal
        success_create_goal, create_response = self.test_create_monthly_goal()
        
        if success_create_goal and create_response:
            if 'message' in create_response and 'valor_meta' in create_response:
                print(f"   ✅ Goal creation/update successful: {create_response['message']}")
                print(f"      New goal value: R${create_response['valor_meta']}")
            else:
                print(f"   ❌ Goal creation response incomplete")
        
        return True

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
    
    # Test authentication
    print("\n🔐 AUTHENTICATION TESTS")
    print("-" * 30)
    auth_success = tester.authenticate_admin()
    
    if not auth_success:
        print("❌ Authentication failed - skipping admin tests")
        return 1
    
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
    
    # Test Sales Dashboard
    print("\n💰 SALES DASHBOARD TESTS")
    print("-" * 30)
    tester.test_sales_dashboard_comprehensive()
    
    # Test Instagram API Integration
    print("\n📸 INSTAGRAM API INTEGRATION TESTS")
    print("-" * 40)
    
    # Test unauthorized access first
    tester.test_unauthorized_access()
    
    # Test getting initial config (should be empty)
    print("\n   📋 Configuration Tests:")
    tester.test_instagram_api_config_get()
    
    # Test saving configuration
    tester.test_instagram_api_config_post()
    
    # Test getting config after saving
    tester.test_instagram_api_config_get_after_save()
    
    # Test connection status (should be not connected initially)
    print("\n   🔗 Connection Tests:")
    tester.test_instagram_api_status()
    
    # Test connect endpoint (should generate OAuth URL after config)
    tester.test_instagram_api_connect()
    
    # Test sync without connection (should fail)
    print("\n   🔄 Sync Tests:")
    tester.test_instagram_api_sync_without_connection()
    
    # Test sync history
    tester.test_instagram_api_sync_history()
    
    # Test disconnect
    print("\n   ❌ Disconnect Tests:")
    tester.test_instagram_api_disconnect()
    
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