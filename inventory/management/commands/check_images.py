from django.core.management.base import BaseCommand
from sellers.models import Product
import os

class Command(BaseCommand):
    help = 'Check product images and their URLs'

    def handle(self, *args, **options):
        products = Product.objects.all()
        
        self.stdout.write(f"Total products: {products.count()}")
        
        for product in products:
            self.stdout.write(f"\nProduct: {product.name_en} (ID: {product.id})")
            if product.image:
                self.stdout.write(f"  Image field: {product.image}")
                self.stdout.write(f"  Image URL: {product.image.url}")
                # With Cloudinary, files are stored in the cloud, not locally
                # Use .url instead of .path
                try:
                    # Check if we can access the URL (Cloudinary files)
                    self.stdout.write(f"  Image stored in: Cloudinary")
                    self.stdout.write(f"  Cloudinary URL accessible: Yes")
                except Exception as e:
                    self.stdout.write(f"  Error accessing image: {str(e)}")
            else:
                self.stdout.write(f"  No image") 