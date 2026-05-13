import asyncio
from app.database import AsyncSessionLocal
from app.models import Session, ChartOfAccount

DEFAULT_CHART = [
    ('1000', 'Cash', 'Asset'),
    ('1100', 'Accounts Receivable', 'Asset'),
    ('2000', 'Accounts Payable', 'Liability'),
    ('3000', "Owner's Equity", 'Equity'),
    ('4000', 'Sales Revenue', 'Revenue'),
    ('5000', 'Cost of Goods Sold', 'Expense'),
    ('6000', 'Rent Expense', 'Expense'),
    ('6100', 'Software Expense', 'Expense'),
    ('6200', 'Office Supplies', 'Expense'),
    ('6300', 'Travel Expense', 'Expense')
]

async def seed_demo_data():
    async with AsyncSessionLocal() as db:
        s1 = Session(name='Demo Company US', base_currency='USD')
        s2 = Session(name='Demo Company EU', base_currency='EUR')
        db.add_all([s1, s2])
        await db.flush()

        # Add chart of accounts to each session
        for session in [s1, s2]:
            for code, name, atype in DEFAULT_CHART:
                db.add(ChartOfAccount(session_id=session.id, code=code, name=name, type=atype))
        
        await db.commit()
        print(f'Seeded sessions {s1.id} and {s2.id} with chart of accounts.')

if __name__ == '__main__':
    asyncio.run(seed_demo_data())