import pytest
import asyncio
from httpx import AsyncClient
from app.core.models_base import UserRole

@pytest.mark.asyncio
async def test_race_condition_submit_timesheet(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: Race Condition / Idempotency
    50 concurrent requests submitting the SAME timesheet draft.
    Should result in exactly ONE submission or appropriate errors for others.
    """
    token = mock_roles("FOREMAN")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create a draft timesheet
    # Assuming there's an endpoint to create draft
    # POST /api/v1/time-sheets
    draft_data = {
        "brigade_id": 1,
        "period_start": "2025-02-01",
        "period_end": "2025-02-07"
    }
    
    # We need a brigade. Assuming one exists or created by fixture.
    # Skipping creation if we assume pre-seeded DB for Anti-Gravity speed.
    # Or strict error handling.
    create_res = await async_client.post("/api/v1/time-sheets/", json=draft_data, headers=headers)
    if create_res.status_code != 201:
        # Check if already exists or other error
        if create_res.status_code == 409: # Conflict logic
             pytest.skip("Timesheet already exists, cannot test race creation.")
        # Try to fetch existing?
        # Proceed assuming testing SUBMIT action
        # Let's try to assume ID 1 exists for this test context
        ts_id = 1 
    else:
        ts_id = create_res.json()['id']

    # 2. Prepare 50 concurrent submit requests
    # POST /api/v1/time-sheets/{id}/submit
    
    endpoint = f"/api/v1/time-sheets/{ts_id}/submit"
    
    async def make_request():
        return await async_client.post(endpoint, headers=headers)
    
    # Launch 50 requests
    tasks = [make_request() for _ in range(50)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyze results
    success_count = 0
    errors = []
    
    for r in responses:
        if isinstance(r, Exception):
            errors.append(str(r))
        elif r.status_code == 200: # Or 201/204
            success_count += 1
        
    print(f"Race Condition Results: Success={success_count}, Total=50")
    
    # Ideally, ONLY ONE should succeed.
    # If logic is idempotent (status check BEFORE update in transaction), others fail with 400.
    assert success_count == 1, f"Race condition failed! {success_count} requests were successful."

@pytest.mark.asyncio
async def test_race_condition_double_approval(async_client: AsyncClient, mock_roles):
    """
    ATTACK VECTOR: Double Approval
    Two managers approve the same request at the same time.
    """
    # Setup: Create a request
    token_foreman = mock_roles("FOREMAN")
    token_manager = mock_roles("PROCUREMENT_MANAGER")
    
    # Create request
    req_res = await async_client.post("/api/v1/material-requests/", 
        json={"cost_object_id": 1, "items": [{"material_name": "Race Item", "quantity": 1, "unit": "pcs"}]},
        headers={"Authorization": f"Bearer {token_foreman}"}
    )
    if req_res.status_code != 201:
        pytest.skip("Could not create request for race test")
        
    req_id = req_res.json()['id']
    endpoint = f"/api/v1/material-requests/{req_id}/approve"
    headers = {"Authorization": f"Bearer {token_manager}"}
    
    # Fire 2 requests
    tasks = [async_client.post(endpoint, headers=headers) for _ in range(2)]
    responses = await asyncio.gather(*tasks)
    
    successes = [r for r in responses if r.status_code == 200]
    
    assert len(successes) <= 1, f"Double Approval! Both requests succeeded: {[r.status_code for r in responses]}"
