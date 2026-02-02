import pytest
from httpx import AsyncClient
from app.core.models_base import UserRole

@pytest.mark.asyncio
async def test_self_approval(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: Self-Approval
    User with both requester and approver roles tries to approve their own request.
    """
    # 1. Create a user (conceptually) with multiple roles.
    # We mock the token to have both roles.
    # Ideally, we should create a real user in DB, but checking token logic is a good first step.
    
    # User is FOREMAN (can create) and PROCUREMENT_MANAGER (can approve)
    # We assume the ID is the same (e.g. 1)
    
    # Simulate: Create a Material Request
    # Note: Using mock_roles helper which creates token with ONE role. 
    # We need to manually create a token with multiple roles.
    
    from app.auth.security import create_access_token
    user_id = 999
    token = create_access_token({
        "sub": str(user_id), 
        "roles": [UserRole.FOREMAN.value, UserRole.PROCUREMENT_MANAGER.value], 
        "type": "access"
    })
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create request
    req_data = {
        "cost_object_id": 1, # ID that exists or mocked
        "items": [{"material_name": "Self-Approve Item", "quantity": 10, "unit": "pcs"}]
    }
    # We might need a valid cost_object_id. 
    # In integration tests, we rely on conftest to setup DB.
    # Assuming ID 1 exists (created in fixture or pre-existing).
    
    # POST /api/v1/material-requests/
    res_create = await async_client.post("/api/v1/material-requests/", json=req_data, headers=headers)
    if res_create.status_code != 201:
        pytest.skip(f"Could not create request: {res_create.status_code}")
        
    req_id = res_create.json()['id']
    
    # Try to APPROVE it with SAME token
    res_approve = await async_client.post(f"/api/v1/material-requests/{req_id}/approve", headers=headers)
    
    # EXPECTATION: Should be Forbidden (403) or at least Logic Error. 
    # A user should not approve their own request even if they have the role.
    print(f"Self-Approval Status: {res_approve.status_code}")
    
    assert res_approve.status_code == 403 or res_approve.status_code == 400, \
        "CRITICAL: User successfully approved their own request!"

@pytest.mark.asyncio
async def test_privilege_escalation(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: Privilege Escalation
    HR_MANAGER tries to access Admin settings.
    """
    token = mock_roles("HR_MANAGER")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access a known admin endpoint (from spec)
    # GET /api/v1/users/ (List users might be admin/manager only)
    # DELETE /api/v1/users/{id}
    
    res = await async_client.delete("/api/v1/users/2", headers=headers)
    
    assert res.status_code == 403, "Privilege Escalation! HR Manager deleted a user."
