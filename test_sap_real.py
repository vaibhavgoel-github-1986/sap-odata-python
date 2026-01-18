#!/usr/bin/env python3
"""
Test script for real SAP OData services on D2A-120.
This script tests V4 (zsd_get_subs_v2) and V2 (ZS4_CCW_SEND_SUBSCR_SNAPSHOT_SRV_01).
"""

from sap_odata import ODataClient
import json

# SAP D2A-120 connection details (you need to fill these)
SAP_HOST = "https://vhcysd2acs.us4.hec.cisco.com:44300"
SAP_USER = ""  # Fill in
SAP_PASS = ""  # Fill in  
SAP_CLIENT = "120"

SUBS_REF = "INTSRQ2A01226"


def test_v4_get_subs():
    """Test V4 OData - zsd_get_subs_v2 with complex $expand."""
    print("\n" + "="*60)
    print("TEST: V4 OData - zsd_get_subs_v2")
    print("="*60)
    
    client = ODataClient(SAP_HOST, SAP_USER, SAP_PASS, client=SAP_CLIENT, verify_ssl=False)
    
    # Complex expand like the MCP tool does
    expand = "partyAccounts($expand=contacts),majorLines($expand=smartAccounts,partyAccounts($expand=contacts)),minorLines($expand=discountAttributes,partyAccounts($expand=contacts))"
    
    result = client.get(
        service="zsd_get_subs_v2",
        entity="Header",
        version="v4",
        namespace="zsb_get_subs_v2",
        filter=f"subscriptionRefId eq '{SUBS_REF}'",
        expand=expand
    )
    
    print(f"\nStatus: {'SUCCESS' if result.get('value') else 'NO DATA'}")
    print(f"Records found: {len(result.get('value', []))}")
    
    if result.get("value"):
        header = result["value"][0]
        print(f"\nHeader Details:")
        print(f"  - subscriptionId: {header.get('subscriptionId')}")
        print(f"  - subscriptionRefId: {header.get('subscriptionRefId')}")
        print(f"  - statusDesc: {header.get('statusDesc')}")
        print(f"  - majorLines count: {len(header.get('majorLines', []))}")
        print(f"  - minorLines count: {len(header.get('minorLines', []))}")
        print(f"  - partyAccounts count: {len(header.get('partyAccounts', []))}")
    
    client.close()
    return result


def test_v2_snapshot():
    """Test V2 OData - ZS4_CCW_SEND_SUBSCR_SNAPSHOT_SRV_01 with complex $expand."""
    print("\n" + "="*60)
    print("TEST: V2 OData - ZS4_CCW_SEND_SUBSCR_SNAPSHOT_SRV_01")
    print("="*60)
    
    client = ODataClient(SAP_HOST, SAP_USER, SAP_PASS, client=SAP_CLIENT, verify_ssl=False)
    
    # Entity with keys in path
    entity = f"HeaderSet(SubscriptionRefId='{SUBS_REF}',WebOrderId='',SubscriptionId='')"
    
    # Complex nested expand
    expand = "HeaderToPrtyAccts/PrtyAcctsToContacts,HeaderToMjrLine/MjrLineToSmartAcct,HeaderToMjrLine/MjrLineToPrtyAccts2/PrtyAccts2ToContacts,HeaderToMjrLine/MjrLineToDscntAttr,HeaderToMnrLines/MnrLinesToDscntAttr,HeaderToMnrLines/MnrLinesToCommitmentSchedules,HeaderToMnrLines/MnrLinesToPrtyAccts2/PrtyAccts2ToContacts"
    
    result = client.get(
        service="ZS4_CCW_SEND_SUBSCR_SNAPSHOT_SRV_01",
        entity=entity,
        version="v2",
        expand=expand
    )
    
    print(f"\nStatus: {'SUCCESS' if result.get('value') else 'NO DATA'}")
    print(f"Records found: {len(result.get('value', []))}")
    
    if result.get("value"):
        header = result["value"][0]
        print(f"\nHeader Details:")
        print(f"  - SubscriptionId: {header.get('SubscriptionId')}")
        print(f"  - SubscriptionRefId: {header.get('SubscriptionRefId')}")
        print(f"  - StatusDesc: {header.get('StatusDesc')}")
        
        mjr_lines = header.get("HeaderToMjrLine", {}).get("results", [])
        print(f"  - HeaderToMjrLine count: {len(mjr_lines)}")
        
        mnr_lines = header.get("HeaderToMnrLines", {}).get("results", [])
        print(f"  - HeaderToMnrLines count: {len(mnr_lines)}")
    
    client.close()
    return result


if __name__ == "__main__":
    print("SAP OData Python Library - Real SAP Test")
    print("="*60)
    print(f"Host: {SAP_HOST}")
    print(f"Client: {SAP_CLIENT}")
    print(f"Subscription Ref: {SUBS_REF}")
    
    if not SAP_USER or not SAP_PASS:
        print("\n⚠️  Please fill in SAP_USER and SAP_PASS to run tests")
    else:
        try:
            test_v4_get_subs()
        except Exception as e:
            print(f"V4 Test FAILED: {e}")
        
        try:
            test_v2_snapshot()
        except Exception as e:
            print(f"V2 Test FAILED: {e}")
