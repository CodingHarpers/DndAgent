import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000/api/play"

def run_test():
    print("1. Starting Session...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/start_session", 
            data=json.dumps({"player_name": "TestHero"}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST')
            
        with urllib.request.urlopen(req) as res:
            data = json.load(res)
            
        session_id = data.get("metadata", {}).get("session_id") or data.get("scene_id")
        print(f"Session ID: {session_id}")
        
        print("2. Sending Attack Command...")
        req_attack = urllib.request.Request(f"{BASE_URL}/step", 
            data=json.dumps({
                "session_id": session_id,
                "text": "I see a goblin and I attack instance goblin_1!"
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST')

        with urllib.request.urlopen(req_attack) as res_attack:
            attack_data = json.load(res_attack)
            
        print("Response received.")
        if "action_log" in attack_data and attack_data["action_log"]:
            log = attack_data["action_log"]
            print("\n[SUCCESS] Action Log Found:")
            print(json.dumps(log, indent=2))
        else:
            print("\n[FAILURE] No action_log in response.")
            print(json.dumps(attack_data, indent=2))

    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    run_test()
