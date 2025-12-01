#!/usr/bin/env python
"""
Test file for custom template filters
"""
from templatetags.order_filters import div, mul, get_item

def test_filters():
    """Test the custom template filters"""
    print("Testing custom template filters...")
    
    # Test div filter
    print(f"div(10, 2) = {div(10, 2)}")  # Should be 5.0
    print(f"div(15, 3) = {div(15, 3)}")  # Should be 5.0
    print(f"div(0, 5) = {div(0, 5)}")    # Should be 0.0
    print(f"div(5, 0) = {div(5, 0)}")    # Should be 0 (division by zero)
    
    # Test mul filter
    print(f"mul(5, 3) = {mul(5, 3)}")    # Should be 15.0
    print(f"mul(2.5, 4) = {mul(2.5, 4)}") # Should be 10.0
    print(f"mul(0, 10) = {mul(0, 10)}")   # Should be 0.0
    
    # Test get_item filter
    test_dict = {'a': 1, 'b': 2, 'c': 3}
    print(f"get_item(test_dict, 'a') = {get_item(test_dict, 'a')}")  # Should be 1
    print(f"get_item(test_dict, 'd') = {get_item(test_dict, 'd')}")  # Should be 0 (default)
    
    print("All tests completed!")

if __name__ == "__main__":
    test_filters() 