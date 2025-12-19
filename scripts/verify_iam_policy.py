#!/usr/bin/env python3
"""Verify IAM policy structure is correct"""

import json
import re
import sys

def extract_policy_from_markdown(file_path):
    """Extract JSON policy from markdown file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find JSON block
    match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if not match:
        print("❌ Could not find JSON block in markdown")
        return None
    
    json_str = match.group(1).strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return None

def verify_policy(policy):
    """Verify IAM policy structure"""
    print("🔍 Verifying IAM Policy Structure...\n")
    
    # Check basic structure
    if "Version" not in policy:
        print("❌ Missing 'Version' field")
        return False
    
    if "Statement" not in policy:
        print("❌ Missing 'Statement' field")
        return False
    
    statements = policy["Statement"]
    print(f"✅ Found {len(statements)} statements")
    
    # Find IAM-related statements
    iam_statements = []
    for stmt in statements:
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        
        if any("iam:" in str(action) for action in actions):
            iam_statements.append(stmt)
    
    print(f"✅ Found {len(iam_statements)} IAM-related statements\n")
    
    # Check for CreateRole statement
    create_role_stmt = None
    pass_role_stmt = None
    
    for stmt in iam_statements:
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        
        if "iam:CreateRole" in str(actions):
            create_role_stmt = stmt
        if "iam:PassRole" in str(actions):
            pass_role_stmt = stmt
    
    # Verify CreateRole statement
    if not create_role_stmt:
        print("❌ CRITICAL: No statement found with 'iam:CreateRole'")
        return False
    
    print("✅ Found CreateRole statement:")
    print(f"   Sid: {create_role_stmt.get('Sid', 'N/A')}")
    print(f"   Has Condition: {bool(create_role_stmt.get('Condition'))}")
    
    if create_role_stmt.get("Condition"):
        print("   ⚠️  WARNING: CreateRole statement has a Condition!")
        print("   ⚠️  This will block role creation!")
        return False
    else:
        print("   ✅ No condition (correct)")
    
    # Verify PassRole statement
    if not pass_role_stmt:
        print("❌ CRITICAL: No statement found with 'iam:PassRole'")
        return False
    
    print("\n✅ Found PassRole statement:")
    print(f"   Sid: {pass_role_stmt.get('Sid', 'N/A')}")
    print(f"   Has Condition: {bool(pass_role_stmt.get('Condition'))}")
    
    if not pass_role_stmt.get("Condition"):
        print("   ⚠️  WARNING: PassRole statement has NO Condition!")
        print("   ⚠️  This is a security risk - should restrict to Lambda")
        return False
    else:
        condition = pass_role_stmt.get("Condition", {})
        if "StringEquals" in condition:
            passed_to = condition["StringEquals"].get("iam:PassedToService")
            if passed_to == "lambda.amazonaws.com":
                print("   ✅ Condition restricts to Lambda (correct)")
            else:
                print(f"   ⚠️  Condition restricts to: {passed_to}")
        else:
            print("   ⚠️  Condition format unexpected")
    
    # Verify they are separate statements
    if create_role_stmt == pass_role_stmt:
        print("\n❌ CRITICAL: CreateRole and PassRole are in the SAME statement!")
        print("❌ They must be in separate statements!")
        return False
    else:
        print("\n✅ CreateRole and PassRole are in separate statements (correct)")
    
    print("\n" + "="*60)
    print("✅ POLICY STRUCTURE IS CORRECT!")
    print("="*60)
    return True

if __name__ == "__main__":
    policy_file = "docs/AWS_IAM_PERMISSIONS.md"
    
    if len(sys.argv) > 1:
        policy_file = sys.argv[1]
    
    policy = extract_policy_from_markdown(policy_file)
    if not policy:
        sys.exit(1)
    
    if verify_policy(policy):
        sys.exit(0)
    else:
        sys.exit(1)





