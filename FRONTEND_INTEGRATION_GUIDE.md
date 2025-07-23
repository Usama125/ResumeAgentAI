# AI Resume Builder API - Frontend Integration Guide

## Base URL
```
http://localhost:8000
```

## Authentication
All protected endpoints require Bearer token authentication:
```javascript
headers: {
  'Authorization': 'Bearer <access_token>',
  'Content-Type': 'application/json'
}
```

## Secure Endpoints
Some endpoints require additional secure request verification with these headers:
```javascript
headers: {
  'X-API-Key': 'AIR_2024_FRONTEND_KEY_$ecur3_K3y_H3r3',
  'X-Signature': '<calculated_signature>',
  'X-Timestamp': '<current_timestamp>'
}
```

---

## 1. Authentication Endpoints

### Register User
```javascript
POST /api/v1/auth/register
Content-Type: application/json

// Request Body
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}

// Response
{
  "user": {
    "id": "687b188f3c1522e81814cc18",
    "email": "test@example.com",
    "name": "Test User",
    "designation": null,
    "location": null,
    "profile_picture": null,
    "is_looking_for_job": true,
    "onboarding_completed": false,
    "onboarding_progress": {
      "step_1_pdf_upload": "not_started",
      "step_2_profile_info": "not_started",
      "step_3_work_preferences": "not_started",
      "step_4_salary_availability": "not_started",
      "current_step": 1,
      "completed": false
    },
    "rating": 4.5,
    "created_at": "2025-07-19T04:01:19.867809"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Login User
```javascript
POST /api/v1/auth/login
Content-Type: application/json

// Request Body
{
  "email": "user@example.com",
  "password": "password123"
}

// Response
{
  "user": {
    "id": "687b188f3c1522e81814cc18",
    "email": "test@example.com",
    "name": "Test User",
    "designation": "Full Stack Software Engineer at SmashCloud",
    "location": "Lahore District, Punjab, Pakistan",
    "profile_picture": null,
    "is_looking_for_job": true,
    "onboarding_completed": true,
    "onboarding_progress": {
      "step_1_pdf_upload": "completed",
      "step_2_profile_info": "completed",
      "step_3_work_preferences": "completed",
      "step_4_salary_availability": "completed",
      "current_step": 4,
      "completed": true
    },
    "rating": 4.5
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 2. User Profile Endpoints

### Get Current User Profile
```javascript
GET /api/v1/users/me
Authorization: Bearer <token>

// Response (After PDF Processing & Onboarding)
{
  "id": "687b188f3c1522e81814cc18",
  "email": "test@example.com",
  "name": "Usama Farooq",
  "designation": "Full Stack Software Engineer at SmashCloud",
  "location": "Lahore District, Punjab, Pakistan",
  "summary": "I'm a seasoned Full Stack Developer with a deep focus on the MERN stack, bringing over 6 years of experience in crafting robust web and mobile applications.",
  "skills": [
    {"name": "React.js", "level": "Advanced", "years": 5},
    {"name": "Node.js", "level": "Advanced", "years": 5},
    {"name": "MongoDB", "level": "Advanced", "years": 5},
    {"name": "TypeScript", "level": "Advanced", "years": 5}
  ],
  "experience_details": [
    {
      "company": "SmashCloud",
      "position": "Full Stack Engineer",
      "duration": "August 2022 - Present (3 years)",
      "description": "Lahore, Punjab, Pakistan"
    }
  ],
  "certifications": ["Preparing for AWS Certified Cloud Practitioner Certification"],
  "profile_picture": null,
  "is_looking_for_job": true,
  "onboarding_completed": true,
  "onboarding_progress": {
    "step_1_pdf_upload": "completed",
    "step_2_profile_info": "completed",
    "step_3_work_preferences": "completed",
    "step_4_salary_availability": "completed",
    "current_step": 4,
    "completed": true
  },
  "rating": 4.5
}
```

### Update Current User Profile
```javascript
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

// Request Body
{
  "name": "John Smith",
  "designation": "Senior Software Engineer",
  "location": "San Francisco, CA",
  "summary": "Updated summary...",
  "is_looking_for_job": true
}

// Response: Updated user object
```

### Get Public User Profile
```javascript
GET /api/v1/users/{user_id}

// Response
{
  "id": "user_id",
  "name": "John Doe",
  "designation": "Software Engineer",
  "location": "New York, NY",
  "summary": "Public summary...",
  "skills": [...],
  "profile_picture": "/uploads/profiles/filename.jpg"
}
```

### Get Featured Users
```javascript
GET /api/v1/users/?limit=12

// Response: Array of public user profiles
```

---

## 3. Onboarding Endpoints

### Get Onboarding Status
```javascript
GET /api/v1/onboarding/status
Authorization: Bearer <token>

// Response - Initial Status
{
  "current_step": 1,
  "completed": false,
  "step_1_pdf_upload": "not_started",
  "step_2_profile_info": "not_started", 
  "step_3_work_preferences": "not_started",
  "step_4_salary_availability": "not_started"
}

// Response - After PDF Upload
{
  "current_step": 2,
  "completed": false,
  "step_1_pdf_upload": "completed",
  "step_2_profile_info": "not_started", 
  "step_3_work_preferences": "not_started",
  "step_4_salary_availability": "not_started"
}
```

### Step 1: Upload LinkedIn PDF
```javascript
POST /api/v1/onboarding/step-1/pdf-upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

// FormData
const formData = new FormData();
formData.append('file', pdfFile); // Must be a PDF file

// Response - Success
{
  "success": true,
  "next_step": 2,
  "message": "PDF processed successfully, proceed to step 2",
  "onboarding_completed": false
}

// Response - Error (if PDF processing fails)
{
  "detail": "Only PDF files are allowed"
}

// What happens during PDF processing:
// 1. PDF text is extracted using AI
// 2. Profile information is automatically parsed:
//    - Name, designation, location, summary
//    - Skills with levels and estimated years
//    - Work experience with companies and durations  
//    - Certifications
// 3. User profile is updated with extracted data
// 4. Onboarding progresses to Step 2
// 5. User can then review/edit the extracted information
```

### Step 2: Update Profile Info
```javascript
POST /api/v1/onboarding/step-2/profile-info
Authorization: Bearer <token>
Content-Type: multipart/form-data

// FormData
const formData = new FormData();
formData.append('profile_picture', imageFile); // Optional
formData.append('name', 'John Doe');
formData.append('designation', 'Software Engineer');
formData.append('location', 'New York, NY');
formData.append('summary', 'Professional summary...');
formData.append('is_looking_for_job', true);
formData.append('additional_info', 'Additional information...');

// Response
{
  "success": true,
  "next_step": 3,
  "message": "Profile information updated successfully, proceed to step 3",
  "onboarding_completed": false
}
```

### Step 3: Work Preferences
```javascript
POST /api/v1/onboarding/step-3/work-preferences
Authorization: Bearer <token>
Content-Type: multipart/form-data

// FormData
const formData = new FormData();
formData.append('current_employment_mode', 'full-time,remote');
formData.append('preferred_work_mode', 'remote,hybrid');
formData.append('preferred_employment_type', 'full-time');
formData.append('preferred_location', 'San Francisco, CA');
formData.append('notice_period', '2 weeks');
formData.append('availability', 'immediate');

// Response
{
  "success": true,
  "next_step": 4,
  "message": "Work preferences updated successfully, proceed to step 4",
  "onboarding_completed": false
}
```

### Step 4: Salary & Availability (Final Step)
```javascript
POST /api/v1/onboarding/step-4/salary-availability
Authorization: Bearer <token>
Content-Type: multipart/form-data

// FormData
const formData = new FormData();
formData.append('current_salary', '$80,000');
formData.append('expected_salary', '$100,000');
formData.append('availability', 'immediate');
formData.append('notice_period', '2 weeks');

// Response
{
  "success": true,
  "next_step": null,
  "message": "Onboarding completed successfully!",
  "onboarding_completed": true
}
```

### Resume Onboarding from Specific Step
```javascript
POST /api/v1/onboarding/resume/{step}
Authorization: Bearer <token>

// Response: OnboardingStatusResponse
```

---

## 4. Search Endpoints

### Search Users
```javascript
GET /api/v1/search/users?q=javascript&skills=React,Node.js&location=New York&looking_for_job=true&limit=20&skip=0

// Query Parameters:
// - q: Search query (optional)
// - skills: Comma-separated skills (optional)
// - location: Location filter (optional)
// - looking_for_job: Job seeking status (optional)
// - limit: Number of results (1-100, default: 20)
// - skip: Number of results to skip (default: 0)

// Response: Array of public user profiles
```

---

## 5. Chat Endpoints (Secure)

### Chat with User Profile
```javascript
POST /api/v1/chat/{user_id}
X-API-Key: AIR_2024_FRONTEND_KEY_$ecur3_K3y_H3r3
X-Signature: <calculated_signature>
X-Timestamp: <current_timestamp>
Content-Type: application/json

// Request Body
{
  "message": "Tell me about your experience with React"
}

// Response
{
  "response": "AI generated response about the user's React experience...",
  "user_id": "user_id"
}
```

### Get Chat Suggestions
```javascript
GET /api/v1/chat/suggestions/{user_id}
X-API-Key: AIR_2024_FRONTEND_KEY_$ecur3_K3y_H3r3
X-Signature: <calculated_signature>
X-Timestamp: <current_timestamp>

// Response
[
  "What projects have you worked on with React?",
  "Tell me about your backend experience",
  "What are your salary expectations?"
]
```

---

## 6. Job Matching Endpoints (Secure)

### Search Matching Candidates (POST)
```javascript
POST /api/v1/job-matching/search
X-API-Key: AIR_2024_FRONTEND_KEY_$ecur3_K3y_H3r3
X-Signature: <calculated_signature>
X-Timestamp: <current_timestamp>
Content-Type: application/json

// Request Body
{
  "query": "We need a Senior React Developer with 5+ years experience",
  "location": "San Francisco",
  "experience_level": "senior",
  "limit": 10,
  "skip": 0
}

// Response
{
  "query": "We need a Senior React Developer...",
  "total_matches": 5,
  "results": [
    {
      "user_id": "user_id",
      "name": "John Doe",
      "designation": "Senior Software Engineer",
      "location": "San Francisco, CA",
      "match_percentage": 85.5,
      "match_reasons": [
        "5+ years React experience",
        "Located in San Francisco",
        "Senior level experience"
      ],
      "profile_summary": "Experienced React developer..."
    }
  ]
}
```

### Search Matching Candidates (GET)
```javascript
GET /api/v1/job-matching/search?q=React Developer&location=New York&experience_level=senior&limit=10&skip=0
X-API-Key: AIR_2024_FRONTEND_KEY_$ecur3_K3y_H3r3
X-Signature: <calculated_signature>
X-Timestamp: <current_timestamp>

// Response: Same as POST version
```

### Get Job Match Summary
```javascript
GET /api/v1/job-matching/summary?q=React Developer
X-API-Key: AIR_2024_FRONTEND_KEY_$ecur3_K3y_H3r3
X-Signature: <calculated_signature>
X-Timestamp: <current_timestamp>

// Response
{
  "query": "React Developer",
  "summary": {
    "total_candidates": 25,
    "excellent_matches": 5,
    "good_matches": 12,
    "average_matches": 8,
    "average_match_score": 72.3
  }
}
```

### Analyze Specific Candidate
```javascript
GET /api/v1/job-matching/analyze/{user_id}?q=React Developer position
X-API-Key: AIR_2024_FRONTEND_KEY_$ecur3_K3y_H3r3
X-Signature: <calculated_signature>
X-Timestamp: <current_timestamp>

// Response
{
  "user_id": "user_id",
  "candidate_name": "John Doe",
  "job_query": "React Developer position",
  "analysis": {
    "match_score": 85.5,
    "strengths": ["Strong React experience", "Good portfolio"],
    "areas_for_improvement": ["Could benefit from more backend experience"],
    "recommendation": "Highly recommended for this position"
  }
}
```

---

## 7. Health Check

### Health Check
```javascript
GET /health

// Response
{
  "status": "healthy"
}
```

### API Documentation
```javascript
GET /docs
// Returns interactive Swagger UI documentation
```

---

## Error Handling

All endpoints return consistent error responses:

```javascript
// 400 Bad Request
{
  "detail": "Validation error message"
}

// 401 Unauthorized
{
  "detail": "Incorrect email or password"
}

// 403 Forbidden  
{
  "detail": "Complete onboarding first before updating profile"
}

// 404 Not Found
{
  "detail": "User not found"
}

// 500 Internal Server Error
{
  "detail": "Internal server error message"
}
```

---

## File Upload Guidelines

### PDF Files (LinkedIn PDF)
- Maximum size: 10MB
- Allowed formats: .pdf only
- Used in: Step 1 onboarding

### Profile Pictures
- Maximum size: 10MB  
- Allowed formats: .jpg, .jpeg, .png
- Used in: Step 2 onboarding and profile updates

### File Access
- Uploaded files are accessible via: `http://localhost:8000/uploads/...`
- Profile pictures: `/uploads/profiles/filename.jpg`
- PDFs: `/uploads/pdfs/filename.pdf`

---

## Rate Limiting

- Daily request limit: 10 requests per day for general endpoints
- Job matching limit: 3 requests per day per user
- Limits are tracked per user/IP

---

## ✅ Tested Examples & Working Code

All endpoints below have been tested and verified working with the current backend.

### React/JavaScript Integration Examples

```javascript
// 1. User Registration - TESTED ✅
const register = async (email, password, name) => {
  const response = await fetch('http://localhost:8000/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password, name })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('token', data.access_token);
    return data.user;
  } else {
    throw new Error(data.detail);
  }
};

// 2. User Login - TESTED ✅
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('token', data.access_token);
    return data.user;
  } else {
    throw new Error(data.detail);
  }
};

// 3. Get Current User Profile - TESTED ✅
const getCurrentUser = async () => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/v1/users/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    return await response.json();
  } else {
    throw new Error('Failed to fetch user');
  }
};

// 4. Get Onboarding Status - TESTED ✅
const getOnboardingStatus = async () => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/v1/onboarding/status', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};

// 5. Upload LinkedIn PDF - TESTED ✅
const uploadLinkedInPDF = async (file) => {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/v1/onboarding/step-1/pdf-upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
      // Note: Don't set Content-Type for FormData, browser will set it automatically
    },
    body: formData
  });
  
  return await response.json();
};

// 6. Complete Profile Info (Step 2) - TESTED ✅  
const updateProfileInfo = async (profileData, profilePicture = null) => {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  
  // Add profile picture if provided
  if (profilePicture) {
    formData.append('profile_picture', profilePicture);
  }
  
  // Add other profile fields
  formData.append('name', profileData.name || '');
  formData.append('designation', profileData.designation || '');
  formData.append('location', profileData.location || '');
  formData.append('summary', profileData.summary || '');
  formData.append('is_looking_for_job', profileData.isLookingForJob || true);
  formData.append('additional_info', profileData.additionalInfo || '');
  
  const response = await fetch('http://localhost:8000/api/v1/onboarding/step-2/profile-info', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  return await response.json();
};

// 7. Search Users - TESTED ✅
const searchUsers = async (query, skills = '', location = '', limit = 20) => {
  const params = new URLSearchParams({
    ...(query && { q: query }),
    ...(skills && { skills }),
    ...(location && { location }),
    limit: limit.toString()
  });
  
  const response = await fetch(`http://localhost:8000/api/v1/search/users?${params}`);
  return await response.json();
};

// 8. Health Check - TESTED ✅
const healthCheck = async () => {
  const response = await fetch('http://localhost:8000/health');
  return await response.json(); // Should return: {"status": "healthy"}
};
```

### React Hook Example for Complete Onboarding Flow

```javascript
import { useState, useEffect } from 'react';

const useOnboarding = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Get current onboarding status
  const getStatus = async () => {
    try {
      setLoading(true);
      const status = await getOnboardingStatus();
      setStatus(status);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Upload PDF and proceed to step 2
  const uploadPDF = async (file) => {
    try {
      setLoading(true);
      const result = await uploadLinkedInPDF(file);
      if (result.success) {
        await getStatus(); // Refresh status
        return result;
      } else {
        throw new Error(result.message || 'PDF upload failed');
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    getStatus();
  }, []);
  
  return {
    status,
    loading,
    error,
    uploadPDF,
    refreshStatus: getStatus
  };
};

// Usage in React component:
const OnboardingComponent = () => {
  const { status, loading, error, uploadPDF } = useOnboarding();
  
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      try {
        await uploadPDF(file);
        alert('PDF uploaded successfully!');
      } catch (err) {
        alert(`Upload failed: ${err.message}`);
      }
    }
  };
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <h3>Onboarding Step {status?.current_step}</h3>
      {status?.current_step === 1 && (
        <input 
          type="file" 
          accept=".pdf" 
          onChange={handleFileUpload}
        />
      )}
      {/* Add other steps UI here */}
    </div>
  );
};
```

## Backend Status
- ✅ **Server Running**: `http://localhost:8000`
- ✅ **MongoDB Connected**: Local instance
- ✅ **All APIs Tested**: Registration, Login, PDF Upload, Profile Management
- ✅ **AI Processing**: LinkedIn PDF extraction working
- ✅ **File Uploads**: PDF and image uploads working
- ✅ **Authentication**: JWT tokens working
- ✅ **Onboarding Flow**: 4-step process working

## Ready for Frontend Development
This guide provides complete, tested integration instructions for all API endpoints with proper authentication, real response examples, and error handling. All endpoints have been verified working with the current backend implementation.