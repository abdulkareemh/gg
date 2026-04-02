"""Seed the database with demo data for testing and demos.

Usage:
    python -m scripts.seed_data
"""

import asyncio
from datetime import datetime, timedelta
import random

from src.models.database import async_session, init_db
from src.services.merchant_service import MerchantService
from src.services.customer_service import CustomerService
from src.services.product_service import ProductService
from src.services.order_service import OrderService


# Demo merchants
MERCHANTS = [
    {
        "phone": "+963944100001",
        "name": "أحمد الشامي",
        "business_name": "مطعم الشام الأصيل",
        "business_type": "restaurant",
        "city": "دمشق",
    },
    {
        "phone": "+963944100002",
        "name": "سارة حلبية",
        "business_name": "بوتيك سارة",
        "business_type": "shop",
        "city": "حلب",
    },
    {
        "phone": "+963944100003",
        "name": "خالد عبد الرحمن",
        "business_name": "إلكترونيات خالد",
        "business_type": "shop",
        "city": "حمص",
    },
]

# Demo products for restaurant
RESTAURANT_PRODUCTS = [
    {"name": "Chicken Shawarma", "name_ar": "شاورما دجاج", "price": 25000, "category": "ساندويشات", "stock": 50},
    {"name": "Meat Shawarma", "name_ar": "شاورما لحمة", "price": 35000, "category": "ساندويشات", "stock": 40},
    {"name": "Falafel Sandwich", "name_ar": "فلافل ساندويش", "price": 15000, "category": "ساندويشات", "stock": 60},
    {"name": "Hummus", "name_ar": "حمص", "price": 12000, "category": "مقبلات", "stock": 30},
    {"name": "Fattoush", "name_ar": "فتوش", "price": 12000, "category": "سلطات", "stock": 25},
    {"name": "Tabbouleh", "name_ar": "تبولة", "price": 10000, "category": "سلطات", "stock": 25},
    {"name": "Kibbeh", "name_ar": "كبة مقلية", "price": 20000, "category": "أطباق رئيسية", "stock": 20},
    {"name": "Grilled Chicken", "name_ar": "دجاج مشوي", "price": 45000, "category": "أطباق رئيسية", "stock": 15},
    {"name": "Mixed Grill", "name_ar": "مشاوي مشكلة", "price": 65000, "category": "أطباق رئيسية", "stock": 10},
    {"name": "Orange Juice", "name_ar": "عصير برتقال", "price": 5000, "category": "مشروبات", "stock": 100},
    {"name": "Lemonade", "name_ar": "ليموناضة", "price": 5000, "category": "مشروبات", "stock": 80},
    {"name": "Arabic Coffee", "name_ar": "قهوة عربية", "price": 3000, "category": "مشروبات", "stock": 200},
    {"name": "Tea", "name_ar": "شاي", "price": 2000, "category": "مشروبات", "stock": 200},
    {"name": "Kunafa", "name_ar": "كنافة", "price": 15000, "category": "حلويات", "stock": 20},
    {"name": "Baklava", "name_ar": "بقلاوة", "price": 18000, "category": "حلويات", "stock": 15},
]

# Demo customers
CUSTOMER_NAMES = [
    "محمد", "فاطمة", "علي", "زينب", "حسين",
    "ريم", "عمر", "نور", "ياسر", "هدى",
    "كريم", "لينا", "سامر", "دانا", "رامي",
]


async def seed():
    """Populate the database with demo data."""
    await init_db()

    async with async_session() as db:
        m_svc = MerchantService(db)
        c_svc = CustomerService(db)
        p_svc = ProductService(db)
        o_svc = OrderService(db)

        print("Seeding merchants...")
        merchants = []
        for m_data in MERCHANTS:
            merchant = await m_svc.create(**m_data)
            merchants.append(merchant)
            print(f"  Created: {merchant.business_name} ({merchant.city})")

        # Add products to restaurant
        restaurant = merchants[0]
        print(f"\nSeeding products for {restaurant.business_name}...")
        products = await p_svc.bulk_create_from_list(restaurant.id, RESTAURANT_PRODUCTS)
        print(f"  Created {len(products)} products")

        # Create customers and orders
        print(f"\nSeeding customers and orders...")
        for i, name in enumerate(CUSTOMER_NAMES):
            phone = f"+96395500{i:04d}"
            customer, _ = await c_svc.get_or_create(restaurant.id, phone)
            await c_svc.update_name(customer.id, name)

            # Create 1-5 random orders per customer
            num_orders = random.randint(1, 5)
            for _ in range(num_orders):
                # Pick 1-3 random products
                order_products = random.sample(products, min(random.randint(1, 3), len(products)))
                items = [
                    {"product_id": p.id, "quantity": random.randint(1, 3)}
                    for p in order_products
                ]

                order = await o_svc.create_order(
                    merchant_id=restaurant.id,
                    customer_id=customer.id,
                    items=items,
                )

                # Randomly advance some orders through statuses
                statuses = ["confirmed", "preparing", "ready", "delivered", "completed"]
                advance_to = random.randint(0, len(statuses) - 1)
                for status in statuses[:advance_to + 1]:
                    await o_svc.update_status(order.id, status)

                await c_svc.increment_orders(customer.id)

            print(f"  {name}: {num_orders} orders")

        # Mark some customers as diaspora
        diaspora_customers = random.sample(CUSTOMER_NAMES, 3)
        print(f"\nMarking diaspora customers: {', '.join(diaspora_customers)}")

        print("\nSeed complete!")
        print(f"  Merchants: {len(merchants)}")
        print(f"  Products: {len(products)}")
        print(f"  Customers: {len(CUSTOMER_NAMES)}")


if __name__ == "__main__":
    asyncio.run(seed())
