# Atlas CRM - Complete Project Documentation

## Project Overview (Project Ka Overview)

**Atlas CRM** ek comprehensive **Fulfillment Management System** hai jo UAE-based e-commerce businesses ke liye banaya gaya hai. Ye system sellers ko unke orders manage karne, inventory track karne, aur delivery process ko handle karne mein help karta hai.

<!-- **Live URL:** https://atlas.kiaantechnology.com -->
**Live URL:** https://web-production-5ba14555.up.railway.app
---

## System Architecture (System Ki Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                        ATLAS CRM SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  SELLER  │───>│CALL CENTER│───>│ PACKAGING│───>│ DELIVERY │  │
│  │  MODULE  │    │  MODULE   │    │  MODULE  │    │  MODULE  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │              │               │               │          │
│       v              v               v               v          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ORDERS DATABASE                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│       │              │               │               │          │
│       v              v               v               v          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │INVENTORY │    │ FINANCE  │    │ ANALYTICS│    │  ADMIN   │  │
│  │  MODULE  │    │  MODULE  │    │  MODULE  │    │ DASHBOARD│  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Roles (User Ke Roles)

| Role | Description | Access |
|------|-------------|--------|
| **Super Admin** | Full system access | Sab kuch manage kar sakta hai |
| **Admin** | Administrative access | Users, roles, settings manage karta hai |
| **Seller** | Product sellers | Products add karta hai, orders create karta hai |
| **Call Center Manager** | Call center head | Agents manage karta hai, orders assign karta hai |
| **Call Center Agent** | Phone operators | Customers ko call karke orders confirm karta hai |
| **Stock Keeper** | Inventory manager | Stock check karta hai, inventory manage karta hai |
| **Packaging Agent** | Packaging staff | Orders pack karta hai |
| **Delivery Agent** | Delivery boys | Orders deliver karta hai |
| **Delivery Manager** | Delivery head | Delivery agents manage karta hai |
| **Accountant/Finance** | Finance team | Payments, invoices manage karta hai |

---

## Complete Order Flow (Order Ka Poora Flow)

### Step 1: Seller Order Creation
```
SELLER DASHBOARD (/sellers/)
    │
    ├── Product Add karta hai
    │   └── /sellers/products/create/
    │
    └── Order Create karta hai
        └── /sellers/orders/create/
            │
            ├── Customer Name
            ├── Phone Number
            ├── Address (City, Area, Street)
            ├── Product Select
            ├── Quantity
            └── Price
```

### Step 2: Call Center Review
```
ORDER STATUS: seller_submitted → callcenter_review
    │
    ├── Call Center Manager (/callcenter/manager/)
    │   └── Orders ko agents ko assign karta hai
    │
    └── Call Center Agent (/callcenter/agent/)
        │
        ├── Customer ko call karta hai
        ├── Order confirm karta hai
        ├── Address verify karta hai
        │
        └── Status Options:
            ├── confirmed → Order confirmed
            ├── no_answer_1st → First attempt, no answer
            ├── no_answer_2nd → Second attempt
            ├── no_answer_final → Final attempt
            ├── postponed → Customer ne baad mein bulaya
            ├── cancelled → Customer ne cancel kiya
            └── escalate_manager → Manager ko escalate
```

### Step 3: Packaging Process
```
ORDER STATUS: callcenter_approved → packaging_in_progress
    │
    └── Packaging Agent (/packaging/)
        │
        ├── Order items collect karta hai
        ├── Package pack karta hai
        ├── Label print karta hai
        │
        └── STATUS: packaging_completed
```

### Step 4: Delivery Process
```
ORDER STATUS: packaging_completed → ready_for_delivery
    │
    ├── Delivery Manager (/delivery/manager/)
    │   └── Orders ko delivery agents ko assign karta hai
    │
    └── Delivery Agent (/delivery/)
        │
        ├── Order pickup karta hai
        ├── Customer ko deliver karta hai
        │
        └── STATUS: delivery_completed
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ORDER LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  SELLER                CALL CENTER              WAREHOUSE    DELIVERY   │
│    │                       │                       │            │       │
│    │ Create Order          │                       │            │       │
│    │─────────────────────>│                       │            │       │
│    │                       │ Assign to Agent       │            │       │
│    │                       │──────────────────────>│            │       │
│    │                       │                       │            │       │
│    │                       │ Call Customer         │            │       │
│    │                       │<──────────────────────│            │       │
│    │                       │                       │            │       │
│    │                       │ Confirm Order         │            │       │
│    │                       │──────────────────────>│            │       │
│    │                       │                       │            │       │
│    │                       │                       │ Pack Order │       │
│    │                       │                       │──────────>│        │
│    │                       │                       │            │       │
│    │                       │                       │            │Deliver│
│    │                       │                       │            │──────>│
│    │                       │                       │            │       │
│    │<──────────────────────────────────────────────────────────────────│
│    │                    Order Completed                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Database Models (Database Ke Models)

### 1. Users Module (`/users/`)
```
User Model:
├── email (Primary Login)
├── full_name
├── phone_number
├── company_name
├── store_name
├── store_link
├── approval_status (pending/approved/rejected)
├── email_verified
└── password_change_required
```

### 2. Products Module (`/products/`, `/sellers/products/`)
```
Product Model:
├── name_en (English Name)
├── name_ar (Arabic Name)
├── code (Auto-generated SKU)
├── category
├── selling_price
├── purchase_price
├── stock_quantity
├── image (Cloudinary)
├── seller (FK → User)
├── is_approved
└── warehouse (FK → Warehouse)
```

### 3. Orders Module (`/orders/`)
```
Order Model:
├── order_code (#YYMMDD001)
├── customer (Name)
├── customer_phone
├── seller (FK → User)
├── status (pending/confirmed/packaged/shipped/delivered/cancelled)
├── workflow_status (seller_submitted → delivery_completed)
├── shipping_address
├── city, emirate, region
├── agent (Call Center Agent)
├── tracking_number
└── total_price
```

### 4. Inventory Module (`/inventory/`)
```
InventoryRecord Model:
├── product (FK → Product)
├── warehouse (FK → Warehouse)
├── quantity
├── transaction_type (in/out/adjustment)
└── notes
```

### 5. Returns Module (`/orders/returns/`)
```
Return Model:
├── return_code (RET250114001)
├── order (FK → Order)
├── return_reason
├── return_status
├── refund_amount
├── refund_status
└── inspection_notes
```

---

## URL Structure (URL Ka Structure)

### Main URLs
| URL | Module | Description |
|-----|--------|-------------|
| `/` | Landing | Homepage |
| `/users/login/` | Users | Login page |
| `/users/register/` | Users | Registration |
| `/dashboard/` | Dashboard | Main dashboard |
| `/sellers/` | Sellers | Seller module |
| `/products/` | Products | Products list |
| `/orders/` | Orders | Orders list |
| `/inventory/` | Inventory | Inventory management |
| `/sourcing/` | Sourcing | Sourcing module |
| `/callcenter/` | Call Center | Call center dashboard |
| `/callcenter/manager/` | Call Center | Manager dashboard |
| `/callcenter/agent/` | Call Center | Agent dashboard |
| `/packaging/` | Packaging | Packaging dashboard |
| `/delivery/` | Delivery | Delivery dashboard |
| `/finance/` | Finance | Finance module |
| `/stock-keeper/` | Stock Keeper | Stock keeper dashboard |
| `/settings/` | Settings | System settings |
| `/analytics/` | Analytics | Analytics & KPIs |
| `/notifications/` | Notifications | User notifications |
| `/roles/` | Roles | Role management |

### API Endpoints
| API URL | Purpose |
|---------|---------|
| `/api/users/login/` | User login API |
| `/api/users/profile/` | User profile API |
| `/api/callcenter/` | Call center APIs |
| `/analytics/api/orders/` | Order analytics |
| `/analytics/api/sales/` | Sales analytics |
| `/analytics/api/inventory/` | Inventory analytics |

---

## Workflow Status Progression

```
seller_submitted
       ↓
callcenter_review
       ↓
callcenter_approved
       ↓
packaging_in_progress
       ↓
packaging_completed
       ↓
ready_for_delivery
       ↓
delivery_in_progress
       ↓
delivery_completed
```

---

## Security Features

1. **Authentication**
   - Email-based login
   - Password hashing (Argon2)
   - Session management
   - 2FA support (optional)

2. **Authorization**
   - Role-based access control (RBAC)
   - Permission-based access
   - Protected routes

3. **Security Headers**
   - CSRF protection
   - XSS protection
   - Content-Type validation

4. **Audit Logging**
   - All actions logged
   - User activity tracking
   - Login attempt tracking

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.2 (Python) |
| Database | SQLite / PostgreSQL |
| Frontend | HTML, TailwindCSS, JavaScript |
| File Storage | Cloudinary |
| Deployment | Docker |
| Web Server | Gunicorn |
| Reverse Proxy | Traefik |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `docker-compose.yml` | Docker configuration |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Docker build instructions |
| `crm_fulfillment/settings.py` | Django settings |

---

## Common Operations

### Login Credentials
- **Super Admin:** Contact system administrator
- **Default Seller Role:** New registrations get Seller role

### Creating a New Order (Seller)
1. Login → `/users/login/`
2. Go to Sellers Dashboard → `/sellers/`
3. Add Product (if needed) → `/sellers/products/create/`
4. Create Order → `/sellers/orders/create/`

### Processing an Order (Call Center)
1. Login as Call Center Agent
2. Go to `/callcenter/agent/`
3. View assigned orders
4. Call customer
5. Update status (confirmed/cancelled/postponed)

### Packaging an Order
1. Login as Packaging Agent
2. Go to `/packaging/`
3. View confirmed orders
4. Pack order
5. Mark as packaged

### Delivering an Order
1. Login as Delivery Agent
2. Go to `/delivery/`
3. View assigned orders
4. Pick up order
5. Deliver to customer
6. Mark as delivered

---

## Troubleshooting

### Common Issues

1. **Login not working**
   - Check CSRF_TRUSTED_ORIGINS in settings.py
   - Restart Docker container

2. **500 Error**
   - Check Docker logs: `docker logs atlas-crm-web`
   - Check database migrations

3. **Static files not loading**
   - Run: `python manage.py collectstatic`
   - Restart container

4. **Images not uploading**
   - Check Cloudinary configuration
   - Verify CLOUDINARY_STORAGE settings

---

## Contact & Support

For technical support or questions about this system, please contact the development team.

**Project Location:** `/home/maani/atlas-crm`
<!-- **Live URL:** https://atlas.kiaantechnology.com -->
**Live URL:** https://web-production-5ba14555.up.railway.app



---

*Last Updated: January 14, 2026*
