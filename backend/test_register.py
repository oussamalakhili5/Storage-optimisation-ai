#!/usr/bin/env python3
"""
Script de test pour l'endpoint /api/register/

Commandes à exécuter:
1. Inscription valide:
   POST /api/register/
   {
     "username": "john_doe",
     "email": "john@example.com",
     "password": "SecurePass123"
   }

2. Email invalide:
   POST /api/register/
   {
     "username": "jane_doe",
     "email": "invalid-email",
     "password": "SecurePass123"
   }

3. Mot de passe trop court:
   POST /api/register/
   {
     "username": "bob_smith",
     "email": "bob@example.com",
     "password": "123"
   }

4. Champs manquants:
   POST /api/register/
   {
     "username": "alice"
   }
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    # Test 1: Inscription valide
    print("=" * 60)
    print("TEST 1: Inscription valide")
    print("=" * 60)
    
    payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/register/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 2: Email invalide
    print("\n" + "=" * 60)
    print("TEST 2: Email invalide")
    print("=" * 60)
    
    payload = {
        "username": "jane_doe",
        "email": "invalid-email",
        "password": "SecurePass123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/register/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 3: Mot de passe trop court
    print("\n" + "=" * 60)
    print("TEST 3: Mot de passe trop court")
    print("=" * 60)
    
    payload = {
        "username": "bob_smith",
        "email": "bob@example.com",
        "password": "123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/register/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 4: Champs manquants
    print("\n" + "=" * 60)
    print("TEST 4: Champs manquants")
    print("=" * 60)
    
    payload = {
        "username": "alice"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/register/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    test_register()
