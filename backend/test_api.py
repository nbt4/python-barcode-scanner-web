import requests
import json
from datetime import datetime, timedelta

BASE_URL = 'http://localhost:5000'

def test_health():
    """Test health check endpoint"""
    print("\nTesting Backend API Endpoints")
    print("=" * 40)
    
    response = requests.get(f'{BASE_URL}/health')
    print(f"Health check: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")
    return response.status_code == 200

def test_auth():
    """Test authentication endpoints"""
    print("\nTesting login with correct credentials:")
    response = requests.post(f'{BASE_URL}/api/v1/auth/login', json={
        'username': 'test',
        'password': 'test'
    })
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code != 200:
        print("❌ Login failed")
        return None
    
    token = response.json().get('token')
    
    print("\nTesting token verification:")
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/api/v1/auth/verify', headers=headers)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Authentication working")
    else:
        print("❌ Authentication failed")
        return None
    
    return token

def test_jobs(token):
    """Test jobs endpoints"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test GET all jobs
    print("\nTesting GET all jobs:")
    response = requests.get(f'{BASE_URL}/api/v1/jobs/', headers=headers)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        jobs = response.json()
        print(f"Found {len(jobs)} jobs")
    
    # Test POST new job
    print("\nTesting POST new job:")
    new_job = {
        'customerID': 1,  # Using first customer
        'statusID': 1,    # Using first status
        'description': 'Test job',
        'startDate': datetime.now().strftime('%Y-%m-%d'),
        'endDate': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    }
    
    response = requests.post(f'{BASE_URL}/api/v1/jobs/', 
                           headers=headers,
                           json=new_job)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ Jobs endpoints working")
    else:
        print("❌ Jobs endpoints failed")

def main():
    """Main test function"""
    if not test_health():
        return
    
    token = test_auth()
    if not token:
        return
    
    test_jobs(token)
    print("\nAPI testing completed!")

if __name__ == '__main__':
    main()
