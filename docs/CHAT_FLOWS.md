# Noor AI — Chat Flow Documentation

## Supported Conversation Flows

This document describes all conversational flows the Noor AI bot supports
across WhatsApp and Telegram.

---

## 1. Merchant Onboarding (Self-Registration)

When a new phone number messages the bot for the first time:

```
User: مرحبا
Bot:  أهلا وسهلا بنور! 🌟
      أنا مساعدك الذكي للبزنس.
      شو اسمك الكريم؟

User: أحمد
Bot:  تمام! شو اسم المحل أو البزنس تبعك؟

User: مطعم الشام
Bot:  حلو! شو نوع البزنس؟
      1. مطعم 🍽️
      2. محل 🏪
      3. خدمات 🔧
      4. غير ذلك

User: 1
Bot:  وين موقعك؟ (مثلاً: دمشق، حلب، حمص...)

User: دمشق
Bot:  تمام يا أحمد! تم تسجيل مطعم الشام بنجاح ✅

      هلق بقدر ساعدك بـ:
      • إدارة الطلبيات
      • متابعة الزبائن
      • إدارة المخزون

      ابعتلي 'مساعدة' إذا بدك تعرف أكتر!
```

---

## 2. New Order Flow

### Customer initiates an order:

```
Customer: بدي اطلب شاورما
Bot:      أهلاً! شو بدك تطلب من القائمة؟
          
          📋 القائمة:
          *ساندويشات*
            ✅ شاورما دجاج — 25,000 ل.س
            ✅ فلافل — 15,000 ل.س
          *مشروبات*
            ✅ عصير برتقال — 5,000 ل.س

Customer: شاورما 2 وعصير
Bot:      🛒 طلبيتك:
            شاورما دجاج × 2 = 50,000 ل.س
            عصير برتقال × 1 = 5,000 ل.س
          
          💰 المجموع: 55,000 ل.س
          
          بدك تأكد الطلبية؟

Customer: اي تمام
Bot:      تم تأكيد طلبيتك! ✅
          المجموع: 55,000 ل.س
          رح نبعتلك تحديث لما تصير جاهزة. شكراً! 🙏
```

### Merchant receives notification:
```
Bot → Merchant:
          🔔 طلبية جديدة #42
          الزبون: محمد
          الطلب: شاورما دجاج ×2, عصير برتقال ×1
          المجموع: 55,000 ل.س
          
          ابعت 'تأكيد 42' للموافقة
```

---

## 3. Order Tracking

```
Customer: وين طلبيتي
Bot:      طلبية #42: طلبيتك قيد التحضير
          رح نبعتلك تحديث لما تصير جاهزة!

--- Later ---

Bot:      🎉 طلبيتك #42 جاهزة! تفضل استلمها.
```

---

## 4. Order Cancellation

```
Customer: بدي الغي الطلب
Bot:      تم طلب إلغاء الطلبية. رح نتواصل معك للتأكيد.
```

---

## 5. Inventory Check (Merchant)

```
Merchant: كم باقي بالمخزون
Bot:      تنبيه! المنتجات التالية قربت تخلص:
          - عصير برتقال: باقي 3 حبة
          - كبة: باقي 2 حبة

--- Or if stock is OK ---

Bot:      المخزون تمام! كل المنتجات متوفرة بكميات كافية.
```

---

## 6. Inventory Report (Merchant)

```
Merchant: تقرير المخزون
Bot:      تقرير المخزون:
          - إجمالي المنتجات: 12
          - متوفر: 10
          - غير متوفر: 2
```

---

## 7. Daily Report (Auto-sent)

Sent automatically at end of day to active merchants:

```
Bot:      📊 تقرير اليوم:
          • الطلبيات: 15
          • الإيرادات: 450,000 ل.س
          • الأكثر طلباً: شاورما دجاج
          
          ابعت 'تقرير' للتفاصيل
```

---

## 8. Low Stock Alert (Auto-sent)

Sent automatically when stock is low:

```
Bot:      ⚠️ تنبيه مخزون منخفض:
            • عصير برتقال: 2 باقي
            • كبة: 1 باقي
          
          حدّث المخزون بإرسال 'تحديث مخزون'
```

---

## 9. Payment Flow

```
Bot:      💰 المجموع: 55,000 ل.س
          اختر طريقة الدفع:
          1. سيرياتيل كاش
          2. MTN كاش
          3. كاش عند الاستلام

Customer: 1
Bot:      تم إرسال طلب دفع إلى رقم سيرياتيل كاش الخاص بك.
          الرجاء تأكيد الدفع من تطبيق سيرياتيل كاش.

--- After payment confirmed ---

Bot:      ✅ تم استلام الدفعة بنجاح!
          طلبيتك #42 قيد التحضير.
```

---

## 10. Help / Greeting

```
Customer: مساعدة
Bot:      أهلا! أنا نور، مساعدك الذكي. بقدر ساعدك بـ:
          
          📦 طلبيات — ابعت "بدي اطلب"
          📋 القائمة — ابعت "القائمة"
          🔍 تتبع — ابعت "وين طلبيتي"
          ❌ إلغاء — ابعت "بدي الغي"
          📊 تقرير — ابعت "تقرير" (للتجار)
```

---

## Intent Keywords (Syrian Arabic)

| Intent | Keywords |
|--------|----------|
| New Order | بدي اطلب، بدي طلب، اطلب، طلبية جديدة، بدي اشتري |
| Check Order | وين طلبيتي، شو صار بالطلب، وصلت، جاهز، تتبع |
| Cancel Order | الغي، بدي الغي، ما بدي، كنسل |
| View Menu | شو عندكم، القائمة، المنيو، الأصناف، وريني |
| Help | مساعدة، كيف، شلون، شو بتقدرو |
| Greeting | مرحبا، هلا، أهلا، السلام عليكم، صباح الخير |
| Inventory | كم باقي، المخزون، الكمية، متوفر |
| Payment | دفع، بدي ادفع، كاش، سيرياتيل كاش، تحويل |
| Report | تقرير، احصائيات، مبيعات، كم بعنا |

---

## Supported Languages

| Language | Code | Status |
|----------|------|--------|
| Syrian Arabic | ar-SY | Full support |
| Modern Standard Arabic | ar | Partial support |
| English | en | Basic support |

The bot auto-detects the language from the message and responds accordingly.
When in doubt, it defaults to Syrian Arabic dialect.
