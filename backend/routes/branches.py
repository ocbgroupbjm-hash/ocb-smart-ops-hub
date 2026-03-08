from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models.branch import BranchCreate, BranchUpdate, BranchResponse, Branch
from database import branches_collection, sales_orders_collection
from utils.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/branches", tags=["Branches"])

@router.post("/", response_model=BranchResponse)
async def create_branch(branch_data: BranchCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    # Override company_id
    branch_data.company_id = company_id
    
    branch = Branch(**branch_data.model_dump())
    branch_dict = branch.model_dump()
    branch_dict['created_at'] = branch_dict['created_at'].isoformat()
    branch_dict['updated_at'] = branch_dict['updated_at'].isoformat()
    
    await branches_collection.insert_one(branch_dict)
    
    return BranchResponse(**branch.model_dump())

@router.get("/", response_model=List[BranchResponse])
async def get_branches(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    branches = await branches_collection.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for branch in branches:
        if isinstance(branch.get('created_at'), str):
            branch['created_at'] = datetime.fromisoformat(branch['created_at'])
        if isinstance(branch.get('updated_at'), str):
            branch['updated_at'] = datetime.fromisoformat(branch['updated_at'])
    
    return branches

@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(branch_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    branch = await branches_collection.find_one(
        {"id": branch_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    if isinstance(branch.get('created_at'), str):
        branch['created_at'] = datetime.fromisoformat(branch['created_at'])
    if isinstance(branch.get('updated_at'), str):
        branch['updated_at'] = datetime.fromisoformat(branch['updated_at'])
    
    return branch

@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    update_data: BranchUpdate,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    
    branch = await branches_collection.find_one(
        {"id": branch_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await branches_collection.update_one(
        {"id": branch_id},
        {"$set": update_dict}
    )
    
    updated_branch = await branches_collection.find_one(
        {"id": branch_id},
        {"_id": 0}
    )
    
    if isinstance(updated_branch.get('created_at'), str):
        updated_branch['created_at'] = datetime.fromisoformat(updated_branch['created_at'])
    if isinstance(updated_branch.get('updated_at'), str):
        updated_branch['updated_at'] = datetime.fromisoformat(updated_branch['updated_at'])
    
    return updated_branch

@router.delete("/{branch_id}")
async def delete_branch(branch_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    result = await branches_collection.delete_one({"id": branch_id, "company_id": company_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    return {"message": "Branch deleted successfully"}