#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta
import uuid

class CuponsIndicacoesTester:
    def __init__(self, base_url="https://mystic-services-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.auth_token = None

    def authenticate_admin(self):
        """Authenticate as admin user"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        url = f"{self.api_url}/auth/login"
        response = requests.post(url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data['access_token']
            print(f"✅ Admin authenticated successfully")
            return True
        else:
            print(f"❌ Failed to authenticate admin: {response.status_code}")
            return False

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authorization header if required
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

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

def main():
    print("🎫 FOCUSED CUPONS AND INDICACOES TESTING")
    print("=" * 50)
    
    tester = CuponsIndicacoesTester()
    
    # Authenticate
    if not tester.authenticate_admin():
        return 1
    
    # Test 1: Create PROMO20 coupon
    print("\n📝 CREATING PROMO20 COUPON")
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    cupom_data = {
        "codigo": "PROMO20",
        "descricao": "Cupom de teste com 20% de desconto",
        "tipo": "percentual",
        "valor_desconto": 0,
        "percentual_desconto": 20.0,
        "valor_minimo": 50.0,
        "data_inicio": start_date.isoformat(),
        "data_fim": end_date.isoformat(),
        "uso_maximo": 100,
        "ativo": True
    }
    
    success, response = tester.run_test("Create PROMO20 Coupon", "POST", "admin/cupons", 200, cupom_data, auth_required=True)
    
    if not success:
        print("❌ Failed to create coupon, stopping tests")
        return 1
    
    cupom_id = response.get('id')
    print(f"✅ Created coupon with ID: {cupom_id}")
    
    # Test 2: Validate PROMO20 coupon
    print("\n✅ VALIDATING PROMO20 COUPON")
    params = {
        "codigo": "PROMO20",
        "valor_pedido": 100.0
    }
    
    success, response = tester.run_test("Validate PROMO20", "POST", "validar-cupom", 200, params=params)
    
    if success:
        discount = response.get('desconto', 0)
        expected_discount = 100.0 * 0.20  # 20% of 100 = 20
        
        if abs(discount - expected_discount) < 0.01:
            print(f"✅ Discount calculated correctly: R${discount}")
        else:
            print(f"❌ Discount calculation error: expected R${expected_discount}, got R${discount}")
        
        if response.get('valido') == True:
            print("✅ Coupon marked as valid")
        else:
            print("❌ Coupon should be valid")
    
    # Test 3: Test minimum value validation
    print("\n🚫 TESTING MINIMUM VALUE VALIDATION")
    params = {
        "codigo": "PROMO20",
        "valor_pedido": 30.0  # Below minimum of 50.0
    }
    
    success, response = tester.run_test("Validate Below Minimum", "POST", "validar-cupom", 400, params=params)
    
    if not success:
        print("✅ Correctly rejected coupon below minimum value")
    else:
        print("❌ Should have rejected coupon below minimum value")
    
    # Test 4: Create friend referral
    print("\n👥 CREATING FRIEND REFERRAL")
    test_cliente_id = str(uuid.uuid4())
    
    indicacao_data = {
        "nome_indicado": "Ana Maria Silva",
        "telefone_indicado": "+5511987654321"
    }
    
    params = {
        "cliente_id": test_cliente_id
    }
    
    success, response = tester.run_test("Create Friend Referral", "POST", "indicacao-amigo", 200, 
                                      indicacao_data, params=params)
    
    if success:
        referral_code = response.get('codigo')
        print(f"✅ Referral code generated: {referral_code}")
        
        if referral_code and referral_code.startswith('IND'):
            print("✅ Referral code has correct format")
        else:
            print(f"❌ Referral code format incorrect: {referral_code}")
    
    # Test 5: Get referrals list
    print("\n📋 GETTING REFERRALS LIST")
    success, response = tester.run_test("Get Referrals", "GET", "admin/indicacoes", 200, auth_required=True)
    
    if success:
        print(f"✅ Found {len(response)} referrals")
        if len(response) > 0:
            referral = response[0]
            print(f"   Latest referral: {referral.get('nome_indicado')} - {referral.get('codigo_indicacao')}")
    
    # Test 6: Get coupons list
    print("\n📋 GETTING COUPONS LIST")
    success, response = tester.run_test("Get Coupons", "GET", "admin/cupons", 200, auth_required=True)
    
    if success:
        print(f"✅ Found {len(response)} coupons")
        promo_found = any(c.get('codigo') == 'PROMO20' for c in response)
        if promo_found:
            print("✅ PROMO20 coupon found in list")
        else:
            print("❌ PROMO20 coupon not found in list")
    
    # Cleanup: Delete test coupon
    print("\n🧹 CLEANUP")
    if cupom_id:
        success, response = tester.run_test("Delete Test Coupon", "DELETE", f"admin/cupons/{cupom_id}", 200, auth_required=True)
        if success:
            print("✅ Test coupon deleted successfully")
    
    print("\n🎉 FOCUSED TESTING COMPLETED!")
    return 0

if __name__ == "__main__":
    exit(main())