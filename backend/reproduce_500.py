
import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.models import MaterialCost
from app.upd.schemas import UPDDetailResponse

# Force using the real DB, not test logic
DATABASE_URL = settings.database_url

async def reproduce():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Querying UPD #107...")
        query = (
            select(MaterialCost)
            .options(selectinload(MaterialCost.items))
            .where(MaterialCost.id == 107)
        )
        result = await session.execute(query)
        upd = result.scalar_one_or_none()
        
        if not upd:
            print("UPD #107 not found!")
            return
            
        print(f"Found UPD: {upd.document_number}")
        print(f"Items count: {len(upd.items)}")
        
        for item in upd.items:
            print(f"Item {item.id}: {item.product_name}")
            print(f"  Price: {item.price}, Amount: {item.amount}, VAT: {item.vat_amount}")
            try:
                print(f"  Total with VAT (property): {item.total_with_vat}")
            except Exception as e:
                print(f"  ERROR accessing property: {e}")
        
        print("Attempting Pydantic serialization...")
        try:
            # We explicitly specificy items to match what router does if needed
            # But UPDDetailResponse config validation will run on fields
            # We manualy construct dict first? No, router passes object.
            # But Pydantic generic model validation from attributes:
            
            # Note: UPDDetailResponse expects 'items' field to be list of objects.
            # We need to construct the list explicitly as done in router:
            from app.upd.schemas import UPDItemResponse, ParsingIssueResponse
            import json
            
            items_list = [
                UPDItemResponse(
                    id=item.id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    price=item.price,
                    amount=item.amount,
                    vat_rate=item.vat_rate,
                    vat_amount=item.vat_amount,
                    total_with_vat=item.total_with_vat
                )
                for item in upd.items
            ]
            
            # Issues
            issues = []
            if upd.parsing_issues:
                 issues = json.loads(upd.parsing_issues)
                 
            response = UPDDetailResponse(
                id=upd.id,
                document_number=upd.document_number,
                document_date=upd.document_date,
                supplier_name=upd.supplier_name,
                supplier_inn=upd.supplier_inn,
                buyer_name=None,
                buyer_inn=None,
                total_amount=upd.total_amount,
                total_vat=upd.total_vat,
                total_with_vat=upd.total_with_vat,
                status=upd.status,
                xml_file_path=upd.xml_file_path,
                generator=upd.generator,
                format_version=None,
                items=items_list,
                parsing_issues=[ParsingIssueResponse(**i) for i in issues],
                created_at=upd.created_at,
                updated_at=upd.updated_at
            )
            print("Serialization SUCCESS!")
        except Exception as e:
            print(f"Serialization FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Ensure backend in path
    import os
    sys.path.append(os.getcwd())
    asyncio.run(reproduce())
