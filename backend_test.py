import requests
import sys
import json
from datetime import datetime

class RitualsAPITester:
    def __init__(self, base_url="https://mystic-market.preview.emergentagent.com"):
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

    # ========== SCHEDULING SYSTEM TESTS ==========
    
    def test_get_admin_tipos_consulta(self):
        """Test getting all consultation types (admin)"""
        return self.run_test("Get Admin Tipos Consulta", "GET", "admin/tipos-consulta", 200, auth_required=True)
    
    def test_get_public_tipos_consulta(self):
        """Test getting active consultation types (public)"""
        return self.run_test("Get Public Tipos Consulta", "GET", "tipos-consulta", 200)
    
    def test_create_tipo_consulta(self):
        """Test creating a new consultation type"""
        tipo_data = {
            "nome": "Consulta de Teste",
            "descricao": "Consulta criada para teste automatizado",
            "preco": 150.0,
            "duracao_minutos": 90,
            "cor_tema": "#ff6b6b",
            "ativo": True,
            "ordem": 10
        }
        return self.run_test("Create Tipo Consulta", "POST", "admin/tipos-consulta", 200, tipo_data, auth_required=True)
    
    def test_update_tipo_consulta(self, tipo_id):
        """Test updating a consultation type"""
        update_data = {
            "preco": 175.0,
            "descricao": "Consulta atualizada via teste automatizado"
        }
        return self.run_test(f"Update Tipo Consulta {tipo_id}", "PUT", f"admin/tipos-consulta/{tipo_id}", 200, update_data, auth_required=True)
    
    def test_delete_tipo_consulta(self, tipo_id):
        """Test deleting a consultation type"""
        return self.run_test(f"Delete Tipo Consulta {tipo_id}", "DELETE", f"admin/tipos-consulta/{tipo_id}", 200, auth_required=True)
    
    def test_get_admin_horarios_disponiveis(self):
        """Test getting all available schedules (admin)"""
        return self.run_test("Get Admin Horarios Disponiveis", "GET", "admin/horarios-disponiveis", 200, auth_required=True)
    
    def test_create_horario_disponivel(self):
        """Test creating a new available schedule"""
        horario_data = {
            "dia_semana": 5,  # Saturday
            "hora_inicio": "10:00",
            "hora_fim": "16:00",
            "intervalo_minutos": 60,
            "ativo": True
        }
        return self.run_test("Create Horario Disponivel", "POST", "admin/horarios-disponiveis", 200, horario_data, auth_required=True)
    
    def test_update_horario_disponivel(self, horario_id):
        """Test updating an available schedule"""
        update_data = {
            "hora_fim": "17:00",
            "intervalo_minutos": 90
        }
        return self.run_test(f"Update Horario Disponivel {horario_id}", "PUT", f"admin/horarios-disponiveis/{horario_id}", 200, update_data, auth_required=True)
    
    def test_delete_horario_disponivel(self, horario_id):
        """Test deleting an available schedule"""
        return self.run_test(f"Delete Horario Disponivel {horario_id}", "DELETE", f"admin/horarios-disponiveis/{horario_id}", 200, auth_required=True)
    
    def test_get_horarios_disponiveis_data(self, data):
        """Test getting available times for a specific date"""
        return self.run_test(f"Get Horarios for {data}", "GET", f"horarios-disponiveis/{data}", 200)
    
    def test_create_agendamento_publico(self):
        """Test creating a public appointment"""
        from datetime import datetime, timedelta
        
        # Use a future date
        future_date = datetime.now() + timedelta(days=7)
        future_date_str = future_date.strftime("%Y-%m-%dT10:00:00")
        
        agendamento_data = {
            "consulta": {
                "tipo_consulta_id": "test_tipo_id",  # Will be replaced with actual ID
                "data_agendada": future_date_str,
                "observacoes": "Agendamento de teste automatizado"
            },
            "cliente": {
                "nome_completo": "Maria Silva Santos",
                "email": "maria.santos@email.com",
                "telefone": "(11) 98765-4321",
                "nome_pessoa_amada": "João Carlos",
                "data_nascimento": "1985-03-15",
                "informacoes_adicionais": "Cliente de teste para agendamento"
            }
        }
        return self.run_test("Create Agendamento Publico", "POST", "agendamento", 200, agendamento_data)
    
    def test_confirmar_consulta(self, session_id):
        """Test confirming a consultation after payment"""
        confirm_data = {
            "session_id": session_id
        }
        return self.run_test("Confirmar Consulta", "POST", "consultas/confirmar", 200, confirm_data)
    
    def test_update_consulta_status(self, consulta_id):
        """Test updating consultation status"""
        status_data = {
            "status": "confirmada",
            "link_reuniao": "https://meet.google.com/test-meeting"
        }
        return self.run_test(f"Update Consulta Status {consulta_id}", "PUT", f"admin/consultas/{consulta_id}/status", 200, status_data, auth_required=True)
    
    def test_get_agenda_dia(self, data):
        """Test getting day's agenda"""
        return self.run_test(f"Get Agenda {data}", "GET", f"admin/consultas/agenda/{data}", 200, auth_required=True)
    
    def test_scheduling_system_comprehensive(self):
        """Comprehensive test of the scheduling system"""
        print("\n📅 COMPREHENSIVE SCHEDULING SYSTEM TEST")
        print("-" * 50)
        
        # Test 1: Get admin consultation types (should have 3 defaults)
        print("\n   📋 Testing Admin Consultation Types:")
        success, tipos_admin = self.test_get_admin_tipos_consulta()
        
        if success and tipos_admin:
            print(f"   ✅ Found {len(tipos_admin)} consultation types")
            
            # Check for default types
            expected_types = [
                {"nome": "Tarot", "preco": 80.0},
                {"nome": "Mapa Astral", "preco": 120.0},
                {"nome": "Consulta Espiritual", "preco": 100.0}
            ]
            
            for expected in expected_types:
                found = any(t.get('nome') == expected['nome'] and t.get('preco') == expected['preco'] 
                          for t in tipos_admin)
                if found:
                    print(f"   ✅ Found default type: {expected['nome']} (R${expected['preco']})")
                else:
                    print(f"   ❌ Missing default type: {expected['nome']} (R${expected['preco']})")
        
        # Test 2: Get public consultation types
        print("\n   🌐 Testing Public Consultation Types:")
        success_public, tipos_public = self.test_get_public_tipos_consulta()
        
        if success_public and tipos_public:
            active_count = len([t for t in tipos_public if t.get('ativo', True)])
            print(f"   ✅ Found {active_count} active consultation types for public")
        
        # Test 3: Create new consultation type
        print("\n   ➕ Testing CRUD Operations for Consultation Types:")
        success_create, create_response = self.test_create_tipo_consulta()
        created_tipo_id = None
        
        if success_create and create_response:
            created_tipo_id = create_response.get('id')
            print(f"   ✅ Created consultation type with ID: {created_tipo_id}")
            
            # Test update
            if created_tipo_id:
                success_update, update_response = self.test_update_tipo_consulta(created_tipo_id)
                if success_update:
                    print(f"   ✅ Updated consultation type successfully")
        
        # Test 4: Get admin available schedules (should have Mon-Fri 9h-18h defaults)
        print("\n   ⏰ Testing Admin Available Schedules:")
        success_horarios, horarios_admin = self.test_get_admin_horarios_disponiveis()
        
        if success_horarios and horarios_admin:
            print(f"   ✅ Found {len(horarios_admin)} schedule configurations")
            
            # Check for weekday schedules (0-4 = Mon-Fri)
            weekdays_found = [h for h in horarios_admin if h.get('dia_semana') in [0, 1, 2, 3, 4]]
            if len(weekdays_found) >= 5:
                print(f"   ✅ Found weekday schedules (Mon-Fri)")
            else:
                print(f"   ⚠️  Expected 5 weekday schedules, found {len(weekdays_found)}")
            
            # Check for 9h-18h schedule
            business_hours = [h for h in horarios_admin 
                            if h.get('hora_inicio') == '09:00' and h.get('hora_fim') == '18:00']
            if business_hours:
                print(f"   ✅ Found business hours schedule (9h-18h)")
            else:
                print(f"   ⚠️  No 9h-18h schedule found")
        
        # Test 5: Create new schedule
        print("\n   ➕ Testing CRUD Operations for Schedules:")
        success_create_horario, create_horario_response = self.test_create_horario_disponivel()
        created_horario_id = None
        
        if success_create_horario and create_horario_response:
            created_horario_id = create_horario_response.get('id')
            print(f"   ✅ Created schedule with ID: {created_horario_id}")
            
            # Test update
            if created_horario_id:
                success_update_horario, update_horario_response = self.test_update_horario_disponivel(created_horario_id)
                if success_update_horario:
                    print(f"   ✅ Updated schedule successfully")
        
        # Test 6: Get available times for a specific date
        print("\n   📅 Testing Available Times for Specific Date:")
        from datetime import datetime, timedelta
        
        # Test with a future weekday
        future_date = datetime.now() + timedelta(days=7)
        while future_date.weekday() >= 5:  # Skip weekends
            future_date += timedelta(days=1)
        
        date_str = future_date.strftime("%Y-%m-%d")
        success_times, available_times = self.test_get_horarios_disponiveis_data(date_str)
        
        if success_times and available_times:
            print(f"   ✅ Found {len(available_times)} available time slots for {date_str}")
            if isinstance(available_times, list) and len(available_times) > 0:
                first_slot = available_times[0]
                print(f"      First slot: {first_slot}")
            elif isinstance(available_times, dict):
                print(f"      Response: {available_times}")
        elif success_times:
            print(f"   ✅ Available times endpoint responded successfully for {date_str}")
            print(f"      Response: {available_times}")
        
        # Test 7: Get day's agenda
        print("\n   📋 Testing Day's Agenda:")
        success_agenda, agenda_data = self.test_get_agenda_dia(date_str)
        
        if success_agenda:
            if isinstance(agenda_data, list):
                print(f"   ✅ Day's agenda retrieved: {len(agenda_data)} appointments")
            else:
                print(f"   ✅ Day's agenda retrieved (empty)")
        
        # Clean up created test data
        print("\n   🧹 Cleaning up test data:")
        if created_tipo_id:
            success_delete_tipo, _ = self.test_delete_tipo_consulta(created_tipo_id)
            if success_delete_tipo:
                print(f"   ✅ Deleted test consultation type")
        
        if created_horario_id:
            success_delete_horario, _ = self.test_delete_horario_disponivel(created_horario_id)
            if success_delete_horario:
                print(f"   ✅ Deleted test schedule")
        
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

    # ========== WHATSAPP BUSINESS API TESTS ==========
    
    def test_whatsapp_config_get(self):
        """Test getting WhatsApp configuration"""
        return self.run_test("Get WhatsApp Config", "GET", "admin/whatsapp/config", 200, auth_required=True)
    
    def test_whatsapp_config_post(self):
        """Test saving WhatsApp configuration"""
        config_data = {
            "api_url": "https://api.whatsapp.business/v1",
            "api_token": "test_whatsapp_token_12345",
            "ativo": True
        }
        
        return self.run_test("Save WhatsApp Config", "POST", "admin/whatsapp/config", 200, config_data, auth_required=True)
    
    def test_whatsapp_config_get_after_save(self):
        """Test getting WhatsApp configuration after saving"""
        success, response = self.run_test("Get WhatsApp Config (After Save)", "GET", "admin/whatsapp/config", 200, auth_required=True)
        
        if success and response:
            # Check if configuration was saved correctly
            if response.get('api_url') == 'https://api.whatsapp.business/v1':
                print("   ✅ API URL saved correctly")
            else:
                print(f"   ❌ API URL mismatch: expected 'https://api.whatsapp.business/v1', got '{response.get('api_url')}'")
            
            if response.get('api_token') == '***':
                print("   ✅ API Token properly masked in response")
            else:
                print(f"   ❌ API Token not masked: {response.get('api_token')}")
            
            if response.get('ativo') == True:
                print("   ✅ Active status saved correctly")
            else:
                print(f"   ❌ Active status incorrect: {response.get('ativo')}")
        
        return success, response
    
    def test_whatsapp_templates_get(self):
        """Test getting WhatsApp templates (should have 4 defaults)"""
        success, response = self.run_test("Get WhatsApp Templates", "GET", "admin/whatsapp/templates", 200, auth_required=True)
        
        if success and response:
            print(f"   Found {len(response)} WhatsApp templates")
            
            # Check for default templates
            expected_templates = [
                "confirmacao_ritual",
                "confirmacao_consulta", 
                "lembrete_consulta",
                "relatorio_diario"
            ]
            
            found_names = [t.get('nome') for t in response]
            
            for expected_name in expected_templates:
                if expected_name in found_names:
                    print(f"   ✅ Found default template: {expected_name}")
                else:
                    print(f"   ❌ Missing default template: {expected_name}")
            
            # Check template structure
            if response:
                template = response[0]
                required_keys = ['id', 'nome', 'template', 'ativo', 'created_at']
                if all(key in template for key in required_keys):
                    print(f"   ✅ Template structure is correct")
                else:
                    print(f"   ❌ Template structure incomplete")
                    
                # Check if templates contain variables
                template_content = template.get('template', '')
                if '{nome}' in template_content:
                    print(f"   ✅ Template contains variables (e.g., {{nome}})")
                else:
                    print(f"   ⚠️  Template may not contain expected variables")
        
        return success, response
    
    def test_whatsapp_templates_create(self):
        """Test creating a new WhatsApp template"""
        template_data = {
            "nome": "template_teste",
            "template": "🧪 Olá {nome}! Este é um template de teste criado automaticamente. Valor: {valor}",
            "ativo": True
        }
        
        return self.run_test("Create WhatsApp Template", "POST", "admin/whatsapp/templates", 200, template_data, auth_required=True)
    
    def test_whatsapp_templates_update(self, template_id):
        """Test updating a WhatsApp template"""
        update_data = {
            "template": "🧪 Olá {nome}! Template ATUALIZADO via teste automatizado. Valor: {valor} ✨",
            "ativo": True
        }
        
        return self.run_test(f"Update WhatsApp Template {template_id}", "PUT", f"admin/whatsapp/templates/{template_id}", 200, update_data, auth_required=True)
    
    def test_whatsapp_templates_delete(self, template_id):
        """Test deleting a WhatsApp template"""
        return self.run_test(f"Delete WhatsApp Template {template_id}", "DELETE", f"admin/whatsapp/templates/{template_id}", 200, auth_required=True)
    
    def test_whatsapp_send_test(self):
        """Test sending a test WhatsApp message"""
        test_data = {
            "phone_number": "+5511999887766",
            "message": "🧪 Esta é uma mensagem de teste do sistema WhatsApp Business API! Enviada automaticamente pelo teste."
        }
        
        # Use params for query parameters
        return self.run_test("Send Test WhatsApp Message", "POST", "admin/whatsapp/send-test", 200, 
                           params=test_data, auth_required=True)
    
    def test_whatsapp_messages_history(self):
        """Test getting WhatsApp messages history"""
        success, response = self.run_test("Get WhatsApp Messages History", "GET", "admin/whatsapp/messages", 200, auth_required=True)
        
        if success and response:
            print(f"   Found {len(response)} WhatsApp messages in history")
            
            if isinstance(response, list):
                print(f"   ✅ Messages history returns list format")
                
                if len(response) > 0:
                    message = response[0]
                    required_keys = ['id', 'to', 'message', 'status', 'created_at']
                    if all(key in message for key in required_keys):
                        print(f"   ✅ Message structure is correct")
                        print(f"      Status: {message.get('status')}")
                        print(f"      To: {message.get('to')}")
                        print(f"      Message preview: {message.get('message', '')[:50]}...")
                    else:
                        print(f"   ❌ Message structure incomplete")
                else:
                    print(f"   ℹ️  No messages in history (expected for new system)")
            else:
                print(f"   ❌ Messages history should return a list")
        
        return success, response
    
    def test_whatsapp_templates_invalid_operations(self):
        """Test invalid operations on WhatsApp templates"""
        # Test updating non-existent template
        update_data = {"template": "Test update"}
        success_update, _ = self.run_test("Update Invalid Template", "PUT", "admin/whatsapp/templates/invalid-id", 404, 
                                        update_data, auth_required=True)
        
        # Test deleting non-existent template  
        success_delete, _ = self.run_test("Delete Invalid Template", "DELETE", "admin/whatsapp/templates/invalid-id", 404, 
                                        auth_required=True)
        
        # Both should fail with 404
        if not success_update and not success_delete:
            print("   ✅ Correctly rejected operations on non-existent templates")
            return True
        else:
            print("   ❌ Should have rejected operations on non-existent templates")
            return False
    
    def test_whatsapp_unauthorized_access(self):
        """Test accessing WhatsApp endpoints without authentication"""
        # Temporarily remove auth token
        original_token = self.auth_token
        self.auth_token = None
        
        success, response = self.run_test("Unauthorized WhatsApp Access", "GET", "admin/whatsapp/config", 401, auth_required=False)
        
        # Restore auth token
        self.auth_token = original_token
        
        # For this test, failure is expected (401 status)
        if not success:
            print("   ✅ Correctly rejected unauthorized access to WhatsApp endpoints")
            return True, response
        else:
            print("   ❌ Should have rejected unauthorized access to WhatsApp endpoints")
            return False, response
    
    def test_whatsapp_system_comprehensive(self):
        """Comprehensive test of WhatsApp Business API system"""
        print("\n📱 COMPREHENSIVE WHATSAPP BUSINESS API TEST")
        print("-" * 50)
        
        # Test 1: Get initial config (should be empty initially)
        print("\n   ⚙️  Configuration Tests:")
        success_get_initial, initial_config = self.test_whatsapp_config_get()
        
        if success_get_initial:
            if initial_config is None:
                print("   ✅ Initial config is empty (as expected)")
            else:
                print(f"   ℹ️  Found existing config: {initial_config}")
        
        # Test 2: Save configuration
        success_save_config, save_response = self.test_whatsapp_config_post()
        
        if success_save_config and save_response:
            print("   ✅ WhatsApp configuration saved successfully")
            
            # Verify masked token
            if save_response.get('api_token') == '***':
                print("   ✅ API token properly masked in save response")
            else:
                print("   ❌ API token not masked in save response")
        
        # Test 3: Get config after saving
        success_get_after, config_after = self.test_whatsapp_config_get_after_save()
        
        # Test 4: Get templates (should have 4 defaults)
        print("\n   📝 Template Tests:")
        success_templates, templates_data = self.test_whatsapp_templates_get()
        
        if success_templates and templates_data:
            if len(templates_data) >= 4:
                print(f"   ✅ Found {len(templates_data)} templates (expected 4+ defaults)")
                
                # Verify default templates content
                for template in templates_data:
                    template_name = template.get('nome', '')
                    template_content = template.get('template', '')
                    
                    if template_name == 'confirmacao_ritual':
                        if '🙏' in template_content and '{nome}' in template_content and '{ritual}' in template_content:
                            print(f"   ✅ confirmacao_ritual template has correct structure")
                        else:
                            print(f"   ❌ confirmacao_ritual template structure incorrect")
                    
                    elif template_name == 'confirmacao_consulta':
                        if '📅' in template_content and '{nome}' in template_content and '{consulta}' in template_content:
                            print(f"   ✅ confirmacao_consulta template has correct structure")
                        else:
                            print(f"   ❌ confirmacao_consulta template structure incorrect")
                    
                    elif template_name == 'lembrete_consulta':
                        if '⏰' in template_content and '{nome}' in template_content and '{consulta}' in template_content:
                            print(f"   ✅ lembrete_consulta template has correct structure")
                        else:
                            print(f"   ❌ lembrete_consulta template structure incorrect")
                    
                    elif template_name == 'relatorio_diario':
                        if '📊' in template_content and '{data}' in template_content and '{faturamento}' in template_content:
                            print(f"   ✅ relatorio_diario template has correct structure")
                        else:
                            print(f"   ❌ relatorio_diario template structure incorrect")
            else:
                print(f"   ❌ Expected at least 4 default templates, found {len(templates_data)}")
        
        # Test 5: Create new template
        print("\n   ➕ Template CRUD Tests:")
        success_create, create_response = self.test_whatsapp_templates_create()
        created_template_id = None
        
        if success_create and create_response:
            created_template_id = create_response.get('id')
            print(f"   ✅ Created test template with ID: {created_template_id}")
            
            # Test update
            if created_template_id:
                success_update, update_response = self.test_whatsapp_templates_update(created_template_id)
                if success_update and update_response:
                    print(f"   ✅ Updated template successfully")
                    
                    # Verify update
                    updated_content = update_response.get('template', '')
                    if 'ATUALIZADO' in updated_content:
                        print(f"   ✅ Template content updated correctly")
                    else:
                        print(f"   ❌ Template content not updated")
        
        # Test 6: Send test message
        print("\n   📤 Message Sending Tests:")
        success_send, send_response = self.test_whatsapp_send_test()
        
        if success_send and send_response:
            print("   ✅ Test message sent successfully")
            
            if 'message' in send_response:
                print(f"      Response: {send_response['message']}")
        
        # Test 7: Get messages history
        print("\n   📋 Message History Tests:")
        success_history, history_data = self.test_whatsapp_messages_history()
        
        if success_history and history_data:
            if len(history_data) > 0:
                print(f"   ✅ Message history contains {len(history_data)} messages")
                
                # Check if our test message is there
                test_message_found = any('teste do sistema WhatsApp' in msg.get('message', '') 
                                       for msg in history_data)
                if test_message_found:
                    print(f"   ✅ Test message found in history")
                else:
                    print(f"   ⚠️  Test message not found in history (may be expected)")
            else:
                print(f"   ℹ️  No messages in history")
        
        # Test 8: Invalid operations
        print("\n   ❌ Error Handling Tests:")
        self.test_whatsapp_templates_invalid_operations()
        
        # Test 9: Unauthorized access
        print("\n   🔒 Security Tests:")
        self.test_whatsapp_unauthorized_access()
        
        # Clean up created test data
        print("\n   🧹 Cleaning up test data:")
        if created_template_id:
            success_delete, _ = self.test_whatsapp_templates_delete(created_template_id)
            if success_delete:
                print(f"   ✅ Deleted test template")
        
        return True

    # ========== CUPONS AND INDICACOES SYSTEM TESTS ==========
    
    def test_get_admin_cupons(self):
        """Test getting all coupons (admin)"""
        return self.run_test("Get Admin Cupons", "GET", "admin/cupons", 200, auth_required=True)
    
    def test_create_cupom(self):
        """Test creating a new coupon"""
        from datetime import datetime, timedelta
        
        # Create coupon valid for next 30 days
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        cupom_data = {
            "codigo": "PROMO20",
            "descricao": "Cupom de teste com 20% de desconto",
            "tipo": "percentual",
            "valor_desconto": 0,  # Not used for percentual type
            "percentual_desconto": 20.0,
            "valor_minimo": 50.0,
            "data_inicio": start_date.isoformat(),
            "data_fim": end_date.isoformat(),
            "uso_maximo": 100,
            "ativo": True
        }
        
        return self.run_test("Create Cupom PROMO20", "POST", "admin/cupons", 200, cupom_data, auth_required=True)
    
    def test_create_cupom_valor_fixo(self):
        """Test creating a fixed value coupon"""
        from datetime import datetime, timedelta
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=15)
        
        cupom_data = {
            "codigo": "DESCONTO50",
            "descricao": "Cupom de R$ 50 de desconto",
            "tipo": "valor_fixo",
            "valor_desconto": 50.0,
            "percentual_desconto": None,
            "valor_minimo": 100.0,
            "data_inicio": start_date.isoformat(),
            "data_fim": end_date.isoformat(),
            "uso_maximo": 50,
            "ativo": True
        }
        
        return self.run_test("Create Cupom DESCONTO50", "POST", "admin/cupons", 200, cupom_data, auth_required=True)
    
    def test_create_duplicate_cupom(self):
        """Test creating coupon with duplicate code (should fail)"""
        from datetime import datetime, timedelta
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        cupom_data = {
            "codigo": "PROMO20",  # Same code as previous test
            "descricao": "Cupom duplicado",
            "tipo": "percentual",
            "valor_desconto": 0,
            "percentual_desconto": 15.0,
            "valor_minimo": None,
            "data_inicio": start_date.isoformat(),
            "data_fim": end_date.isoformat(),
            "uso_maximo": None,
            "ativo": True
        }
        
        success, response = self.run_test("Create Duplicate Cupom", "POST", "admin/cupons", 400, cupom_data, auth_required=True)
        
        # For this test, failure is expected (400 status)
        if not success:
            print("   ✅ Correctly rejected duplicate coupon code")
            return True, response
        else:
            print("   ❌ Should have rejected duplicate coupon code")
            return False, response
    
    def test_validar_cupom_percentual(self):
        """Test validating percentage coupon (public endpoint)"""
        # Test with PROMO20 coupon (20% discount)
        params = {
            "codigo": "PROMO20",
            "valor_pedido": 100.0
        }
        
        success, response = self.run_test("Validate PROMO20 Coupon", "POST", "validar-cupom", 200, params=params)
        
        if success and response:
            # Verify discount calculation
            expected_discount = 100.0 * 0.20  # 20% of 100 = 20
            actual_discount = response.get('desconto', 0)
            
            if abs(actual_discount - expected_discount) < 0.01:  # Allow small floating point differences
                print(f"   ✅ Discount calculated correctly: R${actual_discount}")
            else:
                print(f"   ❌ Discount calculation error: expected R${expected_discount}, got R${actual_discount}")
            
            if response.get('valido') == True:
                print("   ✅ Coupon marked as valid")
            else:
                print("   ❌ Coupon should be valid")
            
            if response.get('tipo') == 'percentual':
                print("   ✅ Coupon type correct")
            else:
                print(f"   ❌ Coupon type incorrect: {response.get('tipo')}")
        
        return success, response
    
    def test_validar_cupom_valor_fixo(self):
        """Test validating fixed value coupon"""
        params = {
            "codigo": "DESCONTO50",
            "valor_pedido": 150.0
        }
        
        success, response = self.run_test("Validate DESCONTO50 Coupon", "POST", "validar-cupom", 200, params=params)
        
        if success and response:
            # Verify fixed discount
            expected_discount = 50.0
            actual_discount = response.get('desconto', 0)
            
            if actual_discount == expected_discount:
                print(f"   ✅ Fixed discount correct: R${actual_discount}")
            else:
                print(f"   ❌ Fixed discount error: expected R${expected_discount}, got R${actual_discount}")
        
        return success, response
    
    def test_validar_cupom_valor_minimo(self):
        """Test coupon validation with minimum value requirement"""
        # Test PROMO20 with value below minimum (should fail)
        params = {
            "codigo": "PROMO20",
            "valor_pedido": 30.0  # Below minimum of 50.0
        }
        
        success, response = self.run_test("Validate Coupon Below Minimum", "POST", "validar-cupom", 400, params=params)
        
        # For this test, failure is expected (400 status)
        if not success:
            print("   ✅ Correctly rejected coupon below minimum value")
            return True, response
        else:
            print("   ❌ Should have rejected coupon below minimum value")
            return False, response
    
    def test_validar_cupom_inexistente(self):
        """Test validating non-existent coupon"""
        params = {
            "codigo": "INEXISTENTE",
            "valor_pedido": 100.0
        }
        
        success, response = self.run_test("Validate Non-existent Coupon", "POST", "validar-cupom", 404, params=params)
        
        # For this test, failure is expected (404 status)
        if not success:
            print("   ✅ Correctly returned 404 for non-existent coupon")
            return True, response
        else:
            print("   ❌ Should have returned 404 for non-existent coupon")
            return False, response
    
    def test_create_indicacao_amigo(self):
        """Test creating friend referral (public endpoint)"""
        # First create a test client to use as referrer
        from datetime import datetime
        import uuid
        
        # Generate a test client ID
        test_cliente_id = str(uuid.uuid4())
        
        indicacao_data = {
            "nome_indicado": "Ana Maria Silva",
            "telefone_indicado": "+5511987654321"
        }
        
        params = {
            "cliente_id": test_cliente_id
        }
        
        success, response = self.run_test("Create Friend Referral", "POST", "indicacao-amigo", 200, 
                                        indicacao_data, params=params)
        
        if success and response:
            # Check if referral code was generated
            if 'codigo' in response:
                referral_code = response['codigo']
                print(f"   ✅ Referral code generated: {referral_code}")
                
                # Store for later use
                self.test_referral_code = referral_code
                
                if referral_code.startswith('IND'):
                    print("   ✅ Referral code has correct format (IND prefix)")
                else:
                    print(f"   ❌ Referral code format incorrect: {referral_code}")
            else:
                print("   ❌ No referral code in response")
            
            if 'message' in response:
                print(f"   ✅ Success message: {response['message']}")
        
        return success, response
    
    def test_get_admin_indicacoes(self):
        """Test getting all referrals (admin)"""
        success, response = self.run_test("Get Admin Indicacoes", "GET", "admin/indicacoes", 200, auth_required=True)
        
        if success and response:
            print(f"   Found {len(response)} referrals")
            
            if isinstance(response, list):
                print("   ✅ Referrals endpoint returns list format")
                
                if len(response) > 0:
                    referral = response[0]
                    required_keys = ['id', 'cliente_indicador_id', 'nome_indicado', 'telefone_indicado', 'codigo_indicacao', 'created_at']
                    
                    if all(key in referral for key in required_keys):
                        print("   ✅ Referral structure is correct")
                        print(f"      Code: {referral.get('codigo_indicacao')}")
                        print(f"      Referred: {referral.get('nome_indicado')}")
                        print(f"      Phone: {referral.get('telefone_indicado')}")
                        
                        # Check if our test referral is there
                        if hasattr(self, 'test_referral_code'):
                            test_found = any(r.get('codigo_indicacao') == self.test_referral_code for r in response)
                            if test_found:
                                print(f"   ✅ Test referral found in list")
                            else:
                                print(f"   ⚠️  Test referral not found in list")
                    else:
                        print("   ❌ Referral structure incomplete")
                        missing_keys = [key for key in required_keys if key not in referral]
                        print(f"      Missing keys: {missing_keys}")
                else:
                    print("   ℹ️  No referrals found")
            else:
                print("   ❌ Referrals endpoint should return a list")
        
        return success, response
    
    def test_update_cupom(self, cupom_id):
        """Test updating a coupon"""
        update_data = {
            "descricao": "Cupom PROMO20 atualizado via teste automatizado",
            "percentual_desconto": 25.0,  # Change from 20% to 25%
            "valor_minimo": 60.0  # Change minimum from 50 to 60
        }
        
        return self.run_test(f"Update Cupom {cupom_id}", "PUT", f"admin/cupons/{cupom_id}", 200, update_data, auth_required=True)
    
    def test_delete_cupom(self, cupom_id):
        """Test deleting a coupon"""
        return self.run_test(f"Delete Cupom {cupom_id}", "DELETE", f"admin/cupons/{cupom_id}", 200, auth_required=True)
    
    def test_cupons_indicacoes_comprehensive(self):
        """Comprehensive test of Cupons and Indicacoes system"""
        print("\n🎫 COMPREHENSIVE CUPONS AND INDICACOES TEST")
        print("-" * 50)
        
        # Test 1: Get initial cupons (should be empty initially)
        print("\n   🎫 Coupon System Tests:")
        success_get_initial, initial_cupons = self.test_get_admin_cupons()
        
        if success_get_initial:
            print(f"   ✅ Found {len(initial_cupons)} existing coupons")
        
        # Test 2: Create percentage coupon (PROMO20)
        print("\n   ➕ Creating Percentage Coupon:")
        success_create_promo, create_promo_response = self.test_create_cupom()
        created_promo_id = None
        
        if success_create_promo and create_promo_response:
            created_promo_id = create_promo_response.get('id')
            print(f"   ✅ Created PROMO20 coupon with ID: {created_promo_id}")
        
        # Test 3: Create fixed value coupon (DESCONTO50)
        print("\n   ➕ Creating Fixed Value Coupon:")
        success_create_fixed, create_fixed_response = self.test_create_cupom_valor_fixo()
        created_fixed_id = None
        
        if success_create_fixed and create_fixed_response:
            created_fixed_id = create_fixed_response.get('id')
            print(f"   ✅ Created DESCONTO50 coupon with ID: {created_fixed_id}")
        
        # Test 4: Try to create duplicate coupon (should fail)
        print("\n   ❌ Testing Duplicate Prevention:")
        self.test_create_duplicate_cupom()
        
        # Test 5: Validate percentage coupon
        print("\n   ✅ Testing Coupon Validation:")
        success_validate_promo, validate_promo_response = self.test_validar_cupom_percentual()
        
        # Test 6: Validate fixed value coupon
        success_validate_fixed, validate_fixed_response = self.test_validar_cupom_valor_fixo()
        
        # Test 7: Test minimum value validation
        print("\n   🚫 Testing Minimum Value Validation:")
        self.test_validar_cupom_valor_minimo()
        
        # Test 8: Test non-existent coupon
        print("\n   🚫 Testing Non-existent Coupon:")
        self.test_validar_cupom_inexistente()
        
        # Test 9: Update coupon
        if created_promo_id:
            print("\n   ✏️  Testing Coupon Update:")
            success_update, update_response = self.test_update_cupom(created_promo_id)
            if success_update:
                print("   ✅ Coupon updated successfully")
        
        # Test 10: Get updated cupons list
        print("\n   📋 Testing Updated Coupons List:")
        success_get_after, cupons_after = self.test_get_admin_cupons()
        
        if success_get_after and cupons_after:
            print(f"   ✅ Found {len(cupons_after)} coupons after creation")
            
            # Check if our test coupons are there
            promo_found = any(c.get('codigo') == 'PROMO20' for c in cupons_after)
            desconto_found = any(c.get('codigo') == 'DESCONTO50' for c in cupons_after)
            
            if promo_found:
                print("   ✅ PROMO20 coupon found in list")
            else:
                print("   ❌ PROMO20 coupon not found in list")
            
            if desconto_found:
                print("   ✅ DESCONTO50 coupon found in list")
            else:
                print("   ❌ DESCONTO50 coupon not found in list")
        
        # Test 11: Friend Referral System
        print("\n   👥 Friend Referral System Tests:")
        success_create_referral, referral_response = self.test_create_indicacao_amigo()
        
        if success_create_referral and referral_response:
            print("   ✅ Friend referral created successfully")
        
        # Test 12: Get referrals list
        print("\n   📋 Testing Referrals List:")
        success_get_referrals, referrals_data = self.test_get_admin_indicacoes()
        
        # Clean up created test data
        print("\n   🧹 Cleaning up test data:")
        if created_promo_id:
            success_delete_promo, _ = self.test_delete_cupom(created_promo_id)
            if success_delete_promo:
                print("   ✅ Deleted PROMO20 test coupon")
        
        if created_fixed_id:
            success_delete_fixed, _ = self.test_delete_cupom(created_fixed_id)
            if success_delete_fixed:
                print("   ✅ Deleted DESCONTO50 test coupon")
        
        # Summary
        print("\n   📊 Test Summary:")
        total_tests = 12
        passed_tests = 0
        
        if success_get_initial: passed_tests += 1
        if success_create_promo: passed_tests += 1
        if success_create_fixed: passed_tests += 1
        if success_validate_promo: passed_tests += 1
        if success_validate_fixed: passed_tests += 1
        if success_get_after: passed_tests += 1
        if success_create_referral: passed_tests += 1
        if success_get_referrals: passed_tests += 1
        
        print(f"   Passed: {passed_tests}/{total_tests} tests")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return True

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
    
    # Test Scheduling System
    print("\n📅 SCHEDULING SYSTEM TESTS")
    print("-" * 30)
    tester.test_scheduling_system_comprehensive()
    
    # Test WhatsApp Business API
    print("\n📱 WHATSAPP BUSINESS API TESTS")
    print("-" * 40)
    tester.test_whatsapp_system_comprehensive()
    
    # Test Cupons and Indicacoes System
    print("\n🎫 CUPONS AND INDICACOES SYSTEM TESTS")
    print("-" * 40)
    tester.test_cupons_indicacoes_comprehensive()
    
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