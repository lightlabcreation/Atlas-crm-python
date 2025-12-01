from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Product
from sellers.models import Product as SellerProduct

@login_required
def product_list(request):
    """List all products."""
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

@login_required
def product_detail(request, product_id):
    """Show product details."""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_detail.html', {'product': product})

@login_required
def product_create(request):
    """Create a new product."""
    return render(request, 'products/product_create.html')

@login_required
def product_edit(request, product_id):
    """Edit a product."""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_edit.html', {'product': product})

@login_required
def product_delete(request, product_id):
    """Delete a product."""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/product_delete.html', {'product': product})

@login_required
def product_detail_api(request, product_id):
    """Get product details as JSON for modal display."""
    print(f"DEBUG: product_detail_api called with product_id: {product_id}")
    try:
        # Try to get from sellers.Product first (the main product model)
        try:
            print(f"DEBUG: Trying to get SellerProduct with id: {product_id}")
            product = get_object_or_404(SellerProduct, id=product_id)
            print(f"DEBUG: Found SellerProduct: {product.name_en}")
            
            product_data = {
                'id': product.id,
                'name_en': product.name_en,
                'name_ar': product.name_ar,
                'code': product.code,
                'sku': product.code,  # Use code as SKU since there's no separate SKU field
            'description': product.description,
            'product_variant': product.product_variant if hasattr(product, 'product_variant') else None,
            'price': float(product.selling_price) if product.selling_price else 0,
            'selling_price': float(product.selling_price) if product.selling_price else 0,
            'purchase_price': float(product.purchase_price) if product.purchase_price else 0,
                'image': product.image.url if product.image else None,
                'image_url': product.image.url if product.image else None,
                'category': product.category if product.category else None,
                'brand': None,  # No brand field in sellers.Product
                'weight': None,  # No weight field in sellers.Product
                'dimensions': None,  # No dimensions field in sellers.Product
                'stock_quantity': product.stock_quantity if hasattr(product, 'stock_quantity') else None,
                'is_active': product.is_approved if hasattr(product, 'is_approved') else True,
                'created_at': product.created_at.isoformat() if hasattr(product, 'created_at') and product.created_at else None,
                'updated_at': product.updated_at.isoformat() if hasattr(product, 'updated_at') and product.updated_at else None,
            }
            
            return JsonResponse({
                'success': True,
                'product': product_data
            })
            
        except Exception as e:
            print(f"DEBUG: SellerProduct not found, trying Product: {str(e)}")
            # Fallback to products.Product if sellers.Product fails
            product = get_object_or_404(Product, id=product_id)
            print(f"DEBUG: Found Product: {product.name}")
            
            product_data = {
                'id': product.id,
                'name_en': product.name,
                'name_ar': product.name,
                'code': product.sku,
                'sku': product.sku,
                'description': product.description,
                'product_variant': product.product_variant if hasattr(product, 'product_variant') else None,
                'price': float(product.price) if product.price else 0,
                'selling_price': float(product.price) if product.price else 0,
                'purchase_price': 0,
                'image': None,
                'image_url': None,
                'category': None,
                'brand': None,
                'weight': None,
                'dimensions': None,
                'stock_quantity': product.stock if hasattr(product, 'stock') else None,
                'is_active': True,
                'created_at': product.created_at.isoformat() if hasattr(product, 'created_at') and product.created_at else None,
                'updated_at': product.updated_at.isoformat() if hasattr(product, 'updated_at') and product.updated_at else None,
            }
            
            return JsonResponse({
                'success': True,
                'product': product_data
            })
            
    except Exception as e:
        print(f"DEBUG: Final error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Product not found: {str(e)}'
        }, status=404)
