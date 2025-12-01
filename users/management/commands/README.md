# أوامر إدارة المستخدمين (User Management Commands)

## نظرة عامة
مجموعة شاملة من أوامر Django لإدارة المستخدمين في نظام إدارة علاقات العملاء (CRM).

## الأوامر المتاحة

### 1. إنشاء مدير عام محسن (Enhanced Super Admin Creation)

#### `create_superuser_enhanced`
نسخة محسنة من أمر إنشاء المدير مع واجهة مستخدم أفضل.

**الاستخدام:**
```bash
python manage.py create_superuser_enhanced
```

**الميزات:**
- ✅ واجهة مستخدم مع رموز تعبيرية
- ✅ رسائل خطأ واضحة
- ✅ التحقق من صحة البيانات
- ✅ تأكيد كلمة المرور
- ✅ تعيين دور Super Admin تلقائياً
- ✅ واجهة سهلة الاستخدام

#### `create_superuser_advanced`
نسخة متقدمة مع ألوان وفحص قوة كلمة المرور وتصميم جميل.

**الاستخدام:**
```bash
python manage.py create_superuser_advanced
```

**الميزات:**
- 🎨 دعم الألوان (عند دعم الطرفية لها)
- 🔒 مؤشر قوة كلمة المرور
- 📊 حدود ASCII جميلة
- ✅ تحقق محسن من البيانات
- 🚀 واجهة احترافية
- 🛡️ تعيين دور Super Admin مع جميع الصلاحيات

### 2. إدارة المستخدمين العادية (Regular User Management)

#### `activate_user` - تفعيل المستخدمين
```bash
# تفعيل مستخدم واحد
python manage.py activate_user --email user@example.com
python manage.py activate_user --user-id 123

# تفعيل جميع المستخدمين غير المفعلين
python manage.py activate_user --all

# عرض المستخدمين غير المفعلين
python manage.py activate_user --list-inactive
```

#### `deactivate_user` - إلغاء تفعيل المستخدمين
```bash
# إلغاء تفعيل مستخدم واحد
python manage.py deactivate_user --email user@example.com
python manage.py deactivate_user --user-id 123

# إلغاء تفعيل جميع المستخدمين (عدا المديرين)
python manage.py deactivate_user --all --confirm

# عرض المستخدمين المفعلين
python manage.py deactivate_user --list-active
```

#### `manage_users` - إدارة شاملة للمستخدمين
```bash
# عرض قائمة المستخدمين
python manage.py manage_users list
python manage.py manage_users list --status active
python manage.py manage_users list --status inactive

# تفعيل/إلغاء تفعيل
python manage.py manage_users activate --email user@example.com
python manage.py manage_users deactivate --email user@example.com

# إدارة الأدوار
python manage.py manage_users assign-role --email user@example.com --role "Seller"
python manage.py manage_users assign-role --email user@example.com --role "Admin" --primary
python manage.py manage_users remove-role --email user@example.com --role "Seller"

# عرض معلومات المستخدم
python manage.py manage_users info --email user@example.com
```

## خيارات سطر الأوامر (Command Line Options)

Both commands support the following options:

```bash
python manage.py create_superuser_enhanced [options]
python manage.py create_superuser_advanced [options]

Options:
  --username USERNAME     Username for the superuser
  --email EMAIL          Email for the superuser
  --first-name NAME      First name for the superuser
  --last-name NAME       Last name for the superuser
  --phone PHONE          Phone number for the superuser
  --database DATABASE    Database to use (default: default)
  --help                 Show help message
```

## Examples

### Basic Usage
```bash
python manage.py create_superuser_enhanced
```

### With Pre-filled Values
```bash
python manage.py create_superuser_advanced --username admin --email admin@example.com
```

### Full Example
```bash
python manage.py create_superuser_advanced \
    --username admin \
    --email admin@example.com \
    --first-name John \
    --last-name Doe \
    --phone +971501234567
```

## Features Comparison

| Feature | Django Default | Enhanced | Advanced |
|---------|----------------|----------|----------|
| Basic UI | ✅ | ✅ | ✅ |
| Emojis | ❌ | ✅ | ✅ |
| Colors | ❌ | ❌ | ✅ |
| Password Strength | ❌ | ❌ | ✅ |
| ASCII Art | ❌ | ❌ | ✅ |
| Input Validation | Basic | Enhanced | Enhanced |
| Error Messages | Basic | Better | Best |
| User Experience | Basic | Good | Excellent |

## Why Use These Commands?

1. **Better User Experience**: Clear prompts and helpful error messages
2. **Enhanced Security**: Password strength checking and validation
3. **Professional Look**: Beautiful formatting and colors
4. **Accessibility**: Clear visual indicators and emojis
5. **Validation**: Comprehensive input validation and error handling

## Requirements

- Django 3.0+
- Python 3.6+
- Terminal that supports Unicode (for emojis)
- Terminal that supports colors (for advanced version)

## Notes

- The `--noinput` flag is not supported as these commands are designed for interactive use
- Colors are automatically detected and disabled if the terminal doesn't support them
- All commands maintain backward compatibility with Django's standard superuser creation
- The commands automatically handle database transactions and error handling

## Customization

You can easily customize these commands by:
- Modifying the validation rules
- Adding new fields
- Changing the color schemes
- Adding more password strength criteria
- Customizing the ASCII art borders

## Troubleshooting

### Colors Not Working
- Ensure your terminal supports colors
- Check if `NO_COLOR` environment variable is set
- Verify `TERM` environment variable is not set to 'dumb'

### Emojis Not Displaying
- Ensure your terminal supports Unicode
- Check your system's font support
- Verify your terminal encoding is set to UTF-8

### Command Not Found
- Ensure the commands are in the correct directory
- Check that Django can find the management commands
- Verify the file permissions are correct
