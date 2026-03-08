from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from models.customer import CustomerCreate, CustomerUpdate, CustomerResponse, Customer
from database import customers_collection
from utils.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/customers", tags=["CRM"])

@router.post("/", response_model=CustomerResponse)
async def create_customer(customer_data: CustomerCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="User must be associated with a company")
    
    # Override company_id with current user's company
    customer_data.company_id = company_id
    
    customer = Customer(**customer_data.model_dump())
    customer_dict = customer.model_dump()
    customer_dict['created_at'] = customer_dict['created_at'].isoformat()
    customer_dict['updated_at'] = customer_dict['updated_at'].isoformat()
    
    if customer_dict.get('last_interaction'):
        customer_dict['last_interaction'] = customer_dict['last_interaction'].isoformat()
    
    await customers_collection.insert_one(customer_dict)
    
    return CustomerResponse(**customer.model_dump())

@router.get("/", response_model=List[CustomerResponse])
async def get_customers(
    segment: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    
    if segment:
        query["segment"] = segment
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    customers = await customers_collection.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for customer in customers:
        if isinstance(customer.get('created_at'), str):
            customer['created_at'] = datetime.fromisoformat(customer['created_at'])
        if isinstance(customer.get('updated_at'), str):
            customer['updated_at'] = datetime.fromisoformat(customer['updated_at'])
        if customer.get('last_interaction') and isinstance(customer['last_interaction'], str):
            customer['last_interaction'] = datetime.fromisoformat(customer['last_interaction'])
    
    return customers

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    customer = await customers_collection.find_one(
        {"id": customer_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if isinstance(customer.get('created_at'), str):
        customer['created_at'] = datetime.fromisoformat(customer['created_at'])
    if isinstance(customer.get('updated_at'), str):
        customer['updated_at'] = datetime.fromisoformat(customer['updated_at'])
    if customer.get('last_interaction') and isinstance(customer['last_interaction'], str):
        customer['last_interaction'] = datetime.fromisoformat(customer['last_interaction'])
    
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    update_data: CustomerUpdate,
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user.get("company_id")
    
    customer = await customers_collection.find_one(
        {"id": customer_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_dict = {k: v for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await customers_collection.update_one(
        {"id": customer_id},
        {"$set": update_dict}
    )
    
    updated_customer = await customers_collection.find_one(
        {"id": customer_id},
        {"_id": 0}
    )
    
    if isinstance(updated_customer.get('created_at'), str):
        updated_customer['created_at'] = datetime.fromisoformat(updated_customer['created_at'])
    if isinstance(updated_customer.get('updated_at'), str):
        updated_customer['updated_at'] = datetime.fromisoformat(updated_customer['updated_at'])
    if updated_customer.get('last_interaction') and isinstance(updated_customer['last_interaction'], str):
        updated_customer['last_interaction'] = datetime.fromisoformat(updated_customer['last_interaction'])
    
    return updated_customer

@router.delete("/{customer_id}")
async def delete_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    result = await customers_collection.delete_one({"id": customer_id, "company_id": company_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {"message": "Customer deleted successfully"}