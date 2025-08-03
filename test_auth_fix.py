#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.routers.users import router

def test_download_endpoint():
    """Test that the download endpoint is properly configured"""
    print("🧪 Testing Download Endpoint Configuration...")
    
    # Check if the endpoint exists
    routes = [route for route in router.routes if hasattr(route, 'path')]
    download_route = None
    
    for route in routes:
        if hasattr(route, 'path') and '/download-profile' in route.path:
            download_route = route
            break
    
    if download_route:
        print(f"✅ Download endpoint found: {download_route.path}")
        print(f"✅ Method: {download_route.methods}")
        print(f"✅ Endpoint name: {download_route.name}")
    else:
        print("❌ Download endpoint not found")
        return False
    
    return True

if __name__ == "__main__":
    success = test_download_endpoint()
    if success:
        print("\n🎉 Download endpoint test passed!")
    else:
        print("\n❌ Download endpoint test failed!")
        sys.exit(1) 