# Order Workflow System - دليل نظام رحلة الطلبية

## Overview - نظرة عامة

The Order Workflow System manages the complete journey of orders from creation to delivery through multiple stages, ensuring proper approval and tracking at each step.

نظام رحلة الطلبية يدير الرحلة الكاملة للطلبات من الإنشاء إلى التوصيل من خلال مراحل متعددة، مما يضمن الموافقة المناسبة والتتبع في كل خطوة.

## Workflow Stages - مراحل الرحلة

### 1. Seller Submitted - تم إرسال الطلبية من البائع
- **Status**: `seller_submitted`
- **Description**: Order created by seller and submitted for approval
- **Action Required**: Call Center Manager approval
- **Next Stage**: Call Center Approved

### 2. Call Center Approved - تمت الموافقة من مركز الاتصال
- **Status**: `callcenter_approved`
- **Description**: Order reviewed and approved by call center
- **Action Required**: Stock Keeper verification and approval
- **Next Stage**: Stock Keeper Approved

### 3. Stock Keeper Approved - تمت الموافقة من أمين المخزن
- **Status**: `stockkeeper_approved`
- **Description**: Stock quantity verified and confirmed
- **Action Required**: Packaging Agent to start packaging
- **Next Stage**: Packaging In Progress

### 4. Packaging In Progress - التغليف قيد التنفيذ
- **Status**: `packaging_in_progress`
- **Description**: Order is being packaged
- **Action Required**: Packaging Agent to complete packaging
- **Next Stage**: Packaging Completed

### 5. Packaging Completed - تم التغليف
- **Status**: `packaging_completed`
- **Description**: Order packaging completed, ready for delivery
- **Action Required**: Delivery Agent to start delivery
- **Next Stage**: Delivery In Progress

### 6. Delivery In Progress - التوصيل قيد التنفيذ
- **Status**: `delivery_in_progress`
- **Description**: Order is being delivered
- **Action Required**: Delivery Agent to complete delivery
- **Next Stage**: Delivery Completed

### 7. Delivery Completed - تم التوصيل
- **Status**: `delivery_completed`
- **Description**: Order successfully delivered to customer
- **Action Required**: None - Order completed
- **Final Stage**: Complete

## User Roles and Permissions - الأدوار والصلاحيات

### Seller - البائع
- **Can**: Create orders, view own orders in workflow
- **Cannot**: Approve or change workflow status
- **Access**: Workflow dashboard (read-only)

### Call Center Manager - مدير مركز الاتصال
- **Can**: Approve orders from seller, assign agents
- **Access**: Workflow dashboard, order approval

### Stock Keeper - أمين المخزن
- **Can**: Verify stock, approve orders after call center
- **Access**: Workflow dashboard, stock verification

### Packaging Agent - وكيل التغليف
- **Can**: Start and complete packaging
- **Access**: Workflow dashboard, packaging management

### Delivery Agent - وكيل التوصيل
- **Can**: Start and complete delivery
- **Access**: Workflow dashboard, delivery management

## How to Use - كيفية الاستخدام

### For Sellers - للبائعين

1. **Create Order**: Create new order through the order creation form
2. **Submit**: Order automatically gets `seller_submitted` status
3. **Track**: Monitor order progress through workflow dashboard
4. **View**: See real-time updates on order status

### For Call Center Managers - لمديري مركز الاتصال

1. **Review**: Check orders with `seller_submitted` status
2. **Verify**: Review customer information and order details
3. **Approve**: Click "Approve Order" to move to next stage
4. **Assign**: Assign orders to call center agents if needed

### For Stock Keepers - لأمناء المخزن

1. **Check**: Review orders with `callcenter_approved` status
2. **Verify**: Confirm stock availability and quantities
3. **Approve**: Click "Confirm Stock & Approve" to proceed
4. **Update**: Update inventory if necessary

### For Packaging Agents - لوكيل التغليف

1. **Receive**: Get orders with `stockkeeper_approved` status
2. **Start**: Click "Start Packaging" to begin work
3. **Package**: Complete packaging process
4. **Complete**: Click "Complete Packaging" when done

### For Delivery Agents - لوكيل التوصيل

1. **Pickup**: Receive orders with `packaging_completed` status
2. **Start**: Click "Start Delivery" to begin delivery
3. **Deliver**: Complete delivery to customer
4. **Confirm**: Click "Complete Delivery" when delivered

## URLs and Navigation - الروابط والتنقل

### Main Workflow URLs
- **Workflow Dashboard**: `/orders/workflow/`
- **Order Detail**: `/orders/workflow/<order_id>/`
- **Order Approval**: `/orders/workflow/<order_id>/approve/`
- **Status Update**: `/orders/workflow/<order_id>/update-status/`
- **Statistics**: `/orders/workflow/statistics/`

### Navigation Flow
1. Access workflow dashboard
2. View pending orders for your role
3. Click on order to see details
4. Use approval buttons to advance workflow
5. Monitor progress through statistics

## Testing the System - اختبار النظام

### Create Test Data
```bash
python manage.py test_workflow --orders 10
```

This command will:
- Create test users for each role
- Create sample orders
- Move some orders through workflow stages
- Create workflow logs for testing

### Manual Testing Steps
1. **Create Order**: Use order creation form
2. **Login as Call Center**: Approve order
3. **Login as Stock Keeper**: Verify and approve
4. **Login as Packaging**: Start and complete packaging
5. **Login as Delivery**: Start and complete delivery
6. **Verify**: Check workflow logs and status updates

## Monitoring and Analytics - المراقبة والتحليلات

### Workflow Statistics
- **Total Orders**: Complete count of all orders
- **Stage Breakdown**: Orders in each workflow stage
- **Completion Rate**: Percentage of completed orders
- **Performance Metrics**: Efficiency and flow rate indicators

### Workflow Logs
- **Complete History**: All status changes with timestamps
- **User Tracking**: Who made each change
- **Notes**: Additional information about changes
- **Audit Trail**: Complete order journey documentation

## Troubleshooting - حل المشاكل

### Common Issues

#### Order Not Moving to Next Stage
- Check user permissions and role
- Verify current workflow status
- Ensure all required fields are filled
- Check for validation errors

#### Workflow Status Not Updating
- Refresh the page
- Check database for changes
- Verify workflow log creation
- Check user authentication

#### Permission Denied Errors
- Verify user role assignment
- Check role-based permissions
- Ensure user is logged in
- Contact administrator for role setup

### Debug Information
- Check Django admin for order status
- Review workflow logs in admin
- Verify user role assignments
- Check console for error messages

## Best Practices - أفضل الممارسات

### For Users
1. **Always verify** information before approving
2. **Add notes** when making status changes
3. **Check permissions** before attempting actions
4. **Use workflow dashboard** for real-time updates

### For Administrators
1. **Set up roles** properly for all users
2. **Monitor workflow** statistics regularly
3. **Review logs** for any issues
4. **Train users** on workflow procedures

### For Developers
1. **Maintain workflow** consistency
2. **Add proper** error handling
3. **Log all** workflow changes
4. **Test thoroughly** before deployment

## Support and Contact - الدعم والاتصال

For technical support or questions about the workflow system:
- **Email**: support@company.com
- **Documentation**: Check this README and system help
- **Admin**: Contact system administrator for role setup
- **Training**: Request workflow training sessions

---

**Note**: This workflow system is designed to ensure proper order processing and tracking. Always follow the established procedures and maintain accurate records of all actions taken.

**ملاحظة**: تم تصميم نظام الرحلة هذا لضمان معالجة وتتبع الطلبات بشكل صحيح. اتبع دائماً الإجراءات المحددة وحافظ على سجلات دقيقة لجميع الإجراءات المتخذة. 