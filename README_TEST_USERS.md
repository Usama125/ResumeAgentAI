# Test User Seeder - Usage Guide

## Overview
This script creates realistic test users for your ResumeAgentAI platform with Indian/Pakistani names and professional data. All users are marked as test users and won't appear in the admin panel.

## Features
✅ **Realistic Names**: Indian/Pakistani names (Muslim, Hindi, English)  
✅ **Professional Photos**: High-quality profile pictures from Unsplash  
✅ **Complete Profiles**: Full experience, skills, projects, education data  
✅ **Database + Algolia**: Automatically syncs to both systems  
✅ **Admin Filtering**: Test users are hidden from admin panel  
✅ **Progress Tracking**: Real-time progress updates  
✅ **Error Handling**: Comprehensive error reporting  

## Usage

### Prerequisites
Make sure you're in the backend directory and have the virtual environment activated:
```bash
cd backend
source venv/bin/activate
```

### Basic Usage
```bash
# Create 20 test users
python create_test_users.py 20

# Create 50 test users
python create_test_users.py 50

# Dry run to see sample data (no actual creation)
python create_test_users.py 10 --dry-run
```

### Examples
```bash
# Create 20 users for initial testing
python create_test_users.py 20

# Create 100 users for a full platform demo
python create_test_users.py 100

# Test what would be created (dry run)
python create_test_users.py 5 --dry-run
```

## What Gets Created

### User Data
- **Names**: Realistic Indian/Pakistani names (60% Indian, 40% Pakistani)
- **Emails**: Gmail addresses (not example.com)
- **Usernames**: No "test" indicators
- **Photos**: Professional Unsplash images
- **Locations**: Real Indian/Pakistani cities
- **Professions**: 40+ realistic tech roles
- **Companies**: Top tech companies (Google, Microsoft, etc.)
- **Skills**: Profession-specific skills with experience levels
- **Experience**: 2-4 realistic job experiences
- **Projects**: 2-4 detailed projects with GitHub links
- **Education**: Real universities with degrees
- **Profile Score**: 70-80 (good quality profiles)

### Technical Details
- **Database**: MongoDB with complete user documents
- **Algolia**: Full-text search index sync
- **Test Flag**: `is_test_user: true` (hidden from admin)
- **Onboarding**: Marked as completed
- **Passwords**: All set to "TestUser123!"

## Sample Output
```
🚀 Starting creation of 20 test users...
📅 Started at: 2025-10-26 06:36:00

📝 Creating user 1/20...
  ✅ User created: Shahid Sheikh (shahidsheikh7219@gmail.com)
  📊 Profile score: 94
  🏢 Company: Cloudflare
  🔄 Syncing to Algolia...
  ✅ Synced to Algolia successfully
  📈 Progress: 5% (1/20)
--------------------------------------------------

📝 Creating user 2/20...
  ✅ User created: Fatima Khan (fatimakhan5731@gmail.com)
  📊 Profile score: 78
  🏢 Company: IBM
  🔄 Syncing to Algolia...
  ✅ Synced to Algolia successfully
  📈 Progress: 10% (2/20)
--------------------------------------------------

...

============================================================
📊 FINAL SUMMARY
============================================================
✅ Users created in database: 20
✅ Users synced to Algolia: 20
❌ Errors encountered: 0
📅 Completed at: 2025-10-26 06:36:45

🎉 Test user creation completed!
💡 Note: These users are marked as test users and won't appear in admin panel
```

## Important Notes

1. **Admin Panel**: Test users are automatically filtered out from admin views
2. **Search Results**: Test users appear in public search results (as intended)
3. **Database**: All users are stored with `is_test_user: true` flag
4. **Algolia**: Full sync ensures search functionality works perfectly
5. **Realistic Data**: No "test" indicators in usernames or data
6. **Professional Quality**: Good profile scores (70-80) for realistic feel

## Troubleshooting

### Common Issues
- **Module not found**: Make sure virtual environment is activated
- **Database connection**: Check MongoDB URL in environment variables
- **Algolia sync fails**: Verify Algolia credentials in environment

### Environment Variables
Make sure these are set in your `.env` file:
```
MONGODB_URL=your_mongodb_connection_string
DATABASE_NAME=ai_resume_builder
ALGOLIA_APP_ID=your_algolia_app_id
ALGOLIA_API_KEY=your_algolia_api_key
```

## Quick Start for Launch
```bash
# Create 50 users for a good platform feel
python create_test_users.py 50

# Verify in your app that users appear in search
# Check admin panel - test users should be hidden
```

This will give your platform a professional, populated feel without cluttering your admin panel with test data!
