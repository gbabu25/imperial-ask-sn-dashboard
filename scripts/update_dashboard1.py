import requests
import json
import sys
import time

# Configuration
BASE_URL = "https://servi........"
INPUT_FILE = "data/chat_interactions_20260113_processed"
headers = {
    'Content-Type': 'application/json',
    'Authorization': ' ',
    'Cookie': ''

def load_processed_data(file_path):
    """Load and parse the processed JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('result', [])
    except FileNotFoundError:
        print(f"✗ ERROR: File not found - {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ ERROR: Invalid JSON format - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ ERROR: Failed to read file - {str(e)}")
        sys.exit(1)

def update_record(sys_id, u_label):
    """Update a single record in ServiceNow."""
    url = f"{BASE_URL}/{sys_id}"
    payload = {
        "u_label": u_label
    }
    
    try:
        # Use json parameter instead of data to ensure proper JSON encoding
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        return response
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.RequestException as e:
        return None
    except Exception as e:
        return None

def main():
    # Load processed data
    print(f"Loading data from {INPUT_FILE}...")
    records = load_processed_data(INPUT_FILE)
    print(f"Found {len(records)} records to process\n")
    
    # Debug: Show first few records to verify data structure
    print("DEBUG: First 3 records sample:")
    for i, record in enumerate(records[:3], 1):
        print(f"  Record {i}: sys_id={record.get('sys_id')}, u_label={repr(record.get('u_label'))}, number={record.get('number')}")
    print()
    
    # Statistics
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    # Process each record
    for idx, record in enumerate(records, 1):
        sys_id = record.get('sys_id')
        u_label = record.get('u_label')
        number = record.get('number', 'N/A')
        
        # Skip if sys_id is missing
        if not sys_id:
            print(f"[{idx}/{len(records)}] SKIPPED - Missing sys_id, number: {number}")
            skipped_count += 1
            continue
        
        # Check if u_label is missing or empty
        if u_label is None or u_label == "":
            print(f"[{idx}/{len(records)}] SKIPPED - Empty u_label, sys_id: {sys_id}, number: {number}")
            skipped_count += 1
            continue
        
        # Strip whitespace from u_label
        u_label = u_label.strip()
        if not u_label:
            print(f"[{idx}/{len(records)}] SKIPPED - Empty u_label after strip, sys_id: {sys_id}, number: {number}")
            skipped_count += 1
            continue
        
        print(f"[{idx}/{len(records)}] Processing - sys_id: {sys_id}, u_label: '{u_label}', number: {number}")
        
        # Debug: Show payload being sent (only for first record)
        if idx == 1:
            payload_debug = {"u_label": u_label}
            print(f"  DEBUG: Payload being sent: {json.dumps(payload_debug)}")
        
        # Update record
        response = update_record(sys_id, u_label)
        
        if response is None:
            print(f"  ✗ ERROR: Failed to update record (connection/timeout error)")
            error_count += 1
            continue
        
        # Check response status
        if response.status_code == 200:
            # Verify the response to see what was actually updated
            try:
                response_data = response.json()
                updated_label = response_data.get('result', {}).get('u_label', '')
                if updated_label == u_label:
                    print(f"  ✓ SUCCESS: Update completed - u_label set to '{updated_label}'")
                else:
                    print(f"  ⚠ WARNING: Update returned status 200 but u_label mismatch!")
                    print(f"    Expected: '{u_label}', Got: '{updated_label}'")
            except:
                print(f"  ✓ SUCCESS: Update completed (status 200, but couldn't parse response)")
            success_count += 1
        elif response.status_code == 204:
            print(f"  ✓ SUCCESS: Update completed (No Content)")
            success_count += 1
        elif response.status_code == 401:
            print(f"  ✗ ERROR: Authentication failed")
            error_count += 1
        elif response.status_code == 403:
            print(f"  ✗ ERROR: Forbidden - Insufficient permissions")
            error_count += 1
        elif response.status_code == 404:
            print(f"  ✗ ERROR: Not Found - Record may not exist")
            error_count += 1
        else:
            print(f"  ⚠ WARNING: Unexpected status code: {response.status_code}")
            try:
                error_msg = response.json()
                print(f"    Response: {json.dumps(error_msg, indent=2)}")
            except:
                print(f"    Response: {response.text}")
            error_count += 1
        
        # Add a small delay to avoid overwhelming the API
        if idx < len(records):
            time.sleep(0.1)
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total records: {len(records)}")
    print(f"Successful updates: {success_count}")
    print(f"Failed updates: {error_count}")
    print(f"Skipped records: {skipped_count}")
    print("=" * 50)

if __name__ == "__main__":
    main()
