from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import traceback

from utils.telegram_auth import get_miniapp_user
from db.controller.listingController import get_listings, get_listing_details

router = APIRouter(tags=["Mini App"])


@router.get("/me")
def get_me(_auth=Depends(get_miniapp_user)):
    try:
        user_id, user = _auth
        data = vars(user)
        data["id"] = str(data["id"])
        return {"status": "ok", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"MINIAPP GET ME ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/listings")
def list_listings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    product_name: Optional[str] = Query(None),
    town: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    max_price: Optional[int] = Query(None),
    _auth=Depends(get_miniapp_user),
):
    try:
        result = get_listings(
            page=page,
            limit=limit,
            product_name=product_name,
            town=town,
            region=region,
            max_price=max_price,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        print(f"MINIAPP LIST LISTINGS ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/listings/mine")
def list_my_listings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    _auth=Depends(get_miniapp_user),
):
    try:
        user_id, _ = _auth
        result = get_listings(
            page=page,
            limit=limit,
            user_id=user_id,
            include_unverified=True,
        )
        return {"status": "ok", "data": result}
    except Exception as e:
        print(f"MINIAPP LIST MY LISTINGS ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/listings/{listing_id}")
def listing_detail(listing_id: int, _auth=Depends(get_miniapp_user)):
    try:
        user_id, _ = _auth
        result = get_listing_details(listing_id, user_id=user_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        return {"status": "ok", "data": result["listing"]}
    except HTTPException:
        raise
    except Exception as e:
        print(f"MINIAPP LISTING DETAIL ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
