"""
Barcode generation utility for sourcing requests and products.
"""
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from datetime import datetime


class BarcodeGenerator:
    """Generate barcodes for products and sourcing requests."""

    @staticmethod
    def generate_sourcing_barcode(sourcing_request):
        """
        Generate a unique barcode for a sourcing request.
        Format: SRC-{id}-{timestamp}
        """
        code = f"SRC{sourcing_request.id:06d}{int(datetime.now().timestamp())}"
        return BarcodeGenerator._generate_code128(code)

    @staticmethod
    def generate_product_barcode(product):
        """
        Generate a unique barcode for a product.
        Format: PRD-{id}-{timestamp}
        """
        code = f"PRD{product.id:06d}{int(datetime.now().timestamp())}"
        return BarcodeGenerator._generate_code128(code)

    @staticmethod
    def _generate_code128(code_text):
        """
        Generate Code128 barcode and return as base64 image.
        """
        # Generate barcode
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(code_text, writer=ImageWriter())

        # Save to BytesIO
        buffer = BytesIO()
        barcode_instance.write(buffer)

        # Convert to base64
        buffer.seek(0)
        barcode_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        return {
            'code': code_text,
            'image_base64': barcode_base64,
            'image_data_url': f'data:image/png;base64,{barcode_base64}'
        }

    @staticmethod
    def generate_qr_code(data):
        """Generate QR code for warehouse locations or quick access."""
        import qrcode
        from qrcode.image.pil import PilImage

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        return {
            'data': data,
            'image_base64': qr_base64,
            'image_data_url': f'data:image/png;base64,{qr_base64}'
        }
