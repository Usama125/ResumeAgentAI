#!/usr/bin/env python3
"""
Professional Test User Seeder for ResumeAgentAI
Creates realistic test users with Indian/Pakistani names and professional data
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from faker import Faker
from faker.providers import internet, person, company, lorem

# Import our services
from app.services.algolia_service import AlgoliaService
from app.models.user import UserInDB

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://Usama125:yabwj7sYtLD0FifC@cluster0.tfx2doy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_resume_builder")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Realistic Indian/Pakistani names
INDIAN_NAMES = {
    "muslim_male": [
        "Ahmed Khan", "Mohammed Ali", "Hassan Sheikh", "Usman Malik", "Omar Farooq",
        "Bilal Ahmed", "Tariq Hussain", "Nadeem Khan", "Rashid Ali", "Faisal Sheikh",
        "Imran Khan", "Sajid Ahmed", "Arif Hussain", "Khalid Malik", "Zubair Khan",
        "Naveed Ali", "Shahid Sheikh", "Rizwan Khan", "Asif Ahmed", "Javed Malik",
        "Waseem Khan", "Noman Ali", "Shoaib Sheikh", "Adnan Khan", "Farhan Ahmed",
        "Saad Malik", "Hamza Khan", "Yusuf Ali", "Ibrahim Sheikh", "Zain Khan",
        "Abdul Rahman", "Mohammad Hassan", "Ali Raza", "Hassan Ali", "Usman Khan",
        "Ahmad Sheikh", "Muhammad Ali", "Hassan Khan", "Usman Ali", "Omar Khan",
        "Bilal Khan", "Tariq Ali", "Nadeem Sheikh", "Rashid Khan", "Faisal Ali",
        "Imran Ali", "Sajid Khan", "Arif Ali", "Khalid Khan", "Zubair Ali",
        "Naveed Khan", "Shahid Ali", "Rizwan Ali", "Asif Khan", "Javed Ali",
        "Waseem Ali", "Noman Khan", "Shoaib Ali", "Adnan Ali", "Farhan Khan",
        "Saad Ali", "Hamza Ali", "Yusuf Khan", "Ibrahim Ali", "Zain Ali"
    ],
    "muslim_female": [
        "Fatima Khan", "Aisha Ahmed", "Zainab Sheikh", "Maryam Ali", "Khadija Malik",
        "Amina Khan", "Hafsa Ahmed", "Safiya Sheikh", "Ruqayya Ali", "Umm Kulthum",
        "Layla Khan", "Noor Ahmed", "Hiba Sheikh", "Dua Ali", "Mariam Khan",
        "Sumayya Ahmed", "Khadija Sheikh", "Asma Ali", "Umm Salama", "Zaynab Khan",
        "Rabia Ahmed", "Sakina Sheikh", "Nusayba Ali", "Umm Ayman", "Safiyya Khan",
        "Ramla Ahmed", "Umm Habiba", "Juwayriya Sheikh", "Maimuna Ali", "Zaynab Ahmed",
        "Fatima Ali", "Aisha Khan", "Zainab Ali", "Maryam Khan", "Khadija Ali",
        "Amina Ali", "Hafsa Khan", "Safiya Ali", "Ruqayya Khan", "Umm Kulthum Ali",
        "Layla Ali", "Noor Khan", "Hiba Ali", "Dua Khan", "Mariam Ali",
        "Sumayya Khan", "Khadija Ali", "Asma Khan", "Umm Salama Ali", "Zaynab Ali",
        "Rabia Khan", "Sakina Ali", "Nusayba Khan", "Umm Ayman Ali", "Safiyya Ali",
        "Ramla Khan", "Umm Habiba Ali", "Juwayriya Ali", "Maimuna Khan", "Zaynab Khan"
    ],
    "hindi_male": [
        "Rajesh Kumar", "Amit Sharma", "Vikram Singh", "Rahul Gupta", "Suresh Patel",
        "Manoj Kumar", "Deepak Sharma", "Anil Singh", "Pradeep Gupta", "Ravi Patel",
        "Sunil Kumar", "Naresh Sharma", "Vinod Singh", "Kumar Gupta", "Ashok Patel",
        "Ramesh Kumar", "Suresh Sharma", "Mukesh Singh", "Dinesh Gupta", "Harish Patel",
        "Naveen Kumar", "Rajesh Sharma", "Vijay Singh", "Sanjay Gupta", "Ajay Patel",
        "Rakesh Kumar", "Mahesh Sharma", "Jagdish Singh", "Krishna Gupta", "Gopal Patel",
        "Arun Kumar", "Suresh Kumar", "Vikram Kumar", "Rahul Kumar", "Amit Kumar",
        "Manoj Sharma", "Deepak Kumar", "Anil Kumar", "Pradeep Kumar", "Ravi Kumar",
        "Sunil Sharma", "Naresh Kumar", "Vinod Kumar", "Kumar Kumar", "Ashok Kumar",
        "Ramesh Sharma", "Suresh Kumar", "Mukesh Kumar", "Dinesh Kumar", "Harish Kumar",
        "Naveen Sharma", "Rajesh Kumar", "Vijay Kumar", "Sanjay Kumar", "Ajay Kumar",
        "Rakesh Sharma", "Mahesh Kumar", "Jagdish Kumar", "Krishna Kumar", "Gopal Kumar"
    ],
    "hindi_female": [
        "Priya Sharma", "Sunita Singh", "Kavita Gupta", "Meera Patel", "Anita Kumar",
        "Rekha Sharma", "Sushma Singh", "Geeta Gupta", "Lata Patel", "Rita Kumar",
        "Poonam Sharma", "Manju Singh", "Sarita Gupta", "Usha Patel", "Shanti Kumar",
        "Kamala Sharma", "Indira Singh", "Savitri Gupta", "Radha Patel", "Ganga Kumar",
        "Sita Sharma", "Parvati Singh", "Lakshmi Gupta", "Durga Patel", "Kali Kumar",
        "Saraswati Sharma", "Annapurna Singh", "Gayatri Gupta", "Surya Patel", "Chandra Kumar",
        "Priya Kumar", "Sunita Kumar", "Kavita Kumar", "Meera Kumar", "Anita Sharma",
        "Rekha Kumar", "Sushma Kumar", "Geeta Kumar", "Lata Kumar", "Rita Sharma",
        "Poonam Kumar", "Manju Kumar", "Sarita Kumar", "Usha Kumar", "Shanti Sharma",
        "Kamala Kumar", "Indira Kumar", "Savitri Kumar", "Radha Kumar", "Ganga Sharma",
        "Sita Kumar", "Parvati Kumar", "Lakshmi Kumar", "Durga Kumar", "Kali Sharma",
        "Saraswati Kumar", "Annapurna Kumar", "Gayatri Kumar", "Surya Kumar", "Chandra Sharma"
    ],
    "english_male": [
        "John Smith", "Michael Johnson", "David Williams", "Robert Brown", "James Jones",
        "William Garcia", "Richard Miller", "Charles Davis", "Joseph Rodriguez", "Thomas Martinez",
        "Christopher Anderson", "Daniel Taylor", "Paul Thomas", "Mark Jackson", "Donald White",
        "Steven Harris", "Andrew Martin", "Joshua Thompson", "Kenneth Garcia", "Kevin Martinez",
        "Brian Robinson", "George Clark", "Timothy Rodriguez", "Ronald Lewis", "Jason Lee",
        "Edward Walker", "Jeffrey Hall", "Ryan Allen", "Jacob Young", "Gary King"
    ],
    "english_female": [
        "Mary Johnson", "Patricia Williams", "Jennifer Brown", "Linda Jones", "Elizabeth Garcia",
        "Barbara Miller", "Susan Davis", "Jessica Rodriguez", "Sarah Martinez", "Karen Anderson",
        "Nancy Taylor", "Lisa Thomas", "Betty Jackson", "Helen White", "Sandra Harris",
        "Donna Martin", "Carol Thompson", "Ruth Garcia", "Sharon Martinez", "Michelle Robinson",
        "Laura Clark", "Sarah Rodriguez", "Kimberly Lewis", "Deborah Lee", "Dorothy Walker",
        "Lisa Hall", "Nancy Allen", "Karen Young", "Betty King", "Helen Wright"
    ],
    "european_male": [
        "Alexander Schmidt", "Johannes Mueller", "Pierre Dubois", "Marco Rossi", "Carlos Rodriguez",
        "Lars Andersen", "Stefan Kowalski", "Antonio Silva", "Nikolai Petrov", "Jan Novak",
        "Andreas Weber", "Giuseppe Bianchi", "Miguel Santos", "Erik Hansen", "Piotr Nowak",
        "François Martin", "Hans Mueller", "Luca Ferrari", "Jose Garcia", "Ole Johansen",
        "Thomas Mueller", "Paolo Romano", "Fernando Lopez", "Bjorn Larsson", "Krzysztof Kowalski",
        "Jean Dubois", "Wolfgang Schmidt", "Alessandro Conti", "Manuel Rodriguez", "Sven Eriksson",
        "Klaus Weber", "Roberto Bianchi", "Pedro Santos", "Magnus Nielsen", "Tomasz Kowalski",
        "Philippe Moreau", "Dieter Mueller", "Francesco Rossi", "Javier Martinez", "Henrik Andersen",
        "Grzegorz Nowak", "Alain Bernard", "Rainer Mueller", "Giovanni Ferrari", "Diego Sanchez",
        "Erik Johansson", "Marcin Kowalski", "Michel Dubois", "Helmut Schmidt", "Marco Bianchi"
    ],
    "european_female": [
        "Anna Schmidt", "Maria Mueller", "Sophie Dubois", "Giulia Rossi", "Carmen Rodriguez",
        "Ingrid Andersen", "Katarzyna Kowalski", "Ana Silva", "Elena Petrov", "Jana Novak",
        "Petra Weber", "Francesca Bianchi", "Isabel Santos", "Astrid Hansen", "Magdalena Nowak",
        "Claire Martin", "Gisela Mueller", "Valentina Ferrari", "Lucia Garcia", "Astrid Johansen",
        "Beate Mueller", "Chiara Romano", "Elena Lopez", "Birgitta Larsson", "Agnieszka Kowalski",
        "Marie Dubois", "Ursula Schmidt", "Sofia Conti", "Pilar Rodriguez", "Gunilla Eriksson",
        "Monika Weber", "Giulia Bianchi", "Teresa Santos", "Kirsten Nielsen", "Joanna Kowalski",
        "Nathalie Moreau", "Brigitte Mueller", "Caterina Rossi", "Dolores Martinez", "Karin Andersen",
        "Malgorzata Nowak", "Celine Bernard", "Renate Mueller", "Antonella Ferrari", "Concepcion Sanchez",
        "Eva Johansson", "Dorota Kowalski", "Isabelle Dubois", "Helga Schmidt", "Roberta Bianchi"
    ]
}

# Professional profile pictures (using better sources with more variety)
PROFESSIONAL_PHOTOS = {
    "male": [
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1595152772835-219674b2a8a6?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1507591064344-4c6ce005b128?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1595152772835-219674b2a8a6?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1507591064344-4c6ce005b128?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1595152772835-219674b2a8a6?w=400&h=400&fit=crop&crop=face",
        # Add more variety with different sources
        "https://randomuser.me/api/portraits/men/1.jpg",
        "https://randomuser.me/api/portraits/men/2.jpg",
        "https://randomuser.me/api/portraits/men/3.jpg",
        "https://randomuser.me/api/portraits/men/4.jpg",
        "https://randomuser.me/api/portraits/men/5.jpg",
        "https://randomuser.me/api/portraits/men/6.jpg",
        "https://randomuser.me/api/portraits/men/7.jpg",
        "https://randomuser.me/api/portraits/men/8.jpg",
        "https://randomuser.me/api/portraits/men/9.jpg",
        "https://randomuser.me/api/portraits/men/10.jpg",
        "https://randomuser.me/api/portraits/men/11.jpg",
        "https://randomuser.me/api/portraits/men/12.jpg",
        "https://randomuser.me/api/portraits/men/13.jpg",
        "https://randomuser.me/api/portraits/men/14.jpg",
        "https://randomuser.me/api/portraits/men/15.jpg",
        "https://randomuser.me/api/portraits/men/16.jpg",
        "https://randomuser.me/api/portraits/men/17.jpg",
        "https://randomuser.me/api/portraits/men/18.jpg",
        "https://randomuser.me/api/portraits/men/19.jpg",
        "https://randomuser.me/api/portraits/men/20.jpg"
    ],
    "female": [
        "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1506863530036-1efeddceb993?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1506863530036-1efeddceb993?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1489424731084-a5d8b219a5bb?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1506863530036-1efeddceb993?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop&crop=face",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&h=400&fit=crop&crop=face",
        # Add more variety with different sources
        "https://randomuser.me/api/portraits/women/1.jpg",
        "https://randomuser.me/api/portraits/women/2.jpg",
        "https://randomuser.me/api/portraits/women/3.jpg",
        "https://randomuser.me/api/portraits/women/4.jpg",
        "https://randomuser.me/api/portraits/women/5.jpg",
        "https://randomuser.me/api/portraits/women/6.jpg",
        "https://randomuser.me/api/portraits/women/7.jpg",
        "https://randomuser.me/api/portraits/women/8.jpg",
        "https://randomuser.me/api/portraits/women/9.jpg",
        "https://randomuser.me/api/portraits/women/10.jpg",
        "https://randomuser.me/api/portraits/women/11.jpg",
        "https://randomuser.me/api/portraits/women/12.jpg",
        "https://randomuser.me/api/portraits/women/13.jpg",
        "https://randomuser.me/api/portraits/women/14.jpg",
        "https://randomuser.me/api/portraits/women/15.jpg",
        "https://randomuser.me/api/portraits/women/16.jpg",
        "https://randomuser.me/api/portraits/women/17.jpg",
        "https://randomuser.me/api/portraits/women/18.jpg",
        "https://randomuser.me/api/portraits/women/19.jpg",
        "https://randomuser.me/api/portraits/women/20.jpg"
    ]
}

# Professional data
PROFESSIONS = [
    "Software Engineer", "Senior Software Engineer", "Full Stack Developer", "Frontend Developer", 
    "Backend Developer", "DevOps Engineer", "Data Scientist", "Machine Learning Engineer",
    "Product Manager", "Senior Product Manager", "UX Designer", "UI Designer", "UX/UI Designer",
    "Marketing Manager", "Digital Marketing Specialist", "Content Marketing Manager",
    "Sales Manager", "Business Development Manager", "Account Manager", "Customer Success Manager",
    "Business Analyst", "Senior Business Analyst", "Data Analyst", "Financial Analyst",
    "Project Manager", "Senior Project Manager", "Scrum Master", "Technical Lead",
    "Solutions Architect", "Cloud Architect", "System Administrator", "Database Administrator",
    "Quality Assurance Engineer", "Test Engineer", "Security Engineer", "Cybersecurity Specialist",
    "Mobile Developer", "iOS Developer", "Android Developer", "React Native Developer",
    "Python Developer", "Java Developer", "JavaScript Developer", "Node.js Developer",
    "AI/ML Engineer", "Computer Vision Engineer", "NLP Engineer", "Data Engineer"
]

COMPANIES = [
    "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Tesla", "Uber", "Airbnb", "Spotify",
    "Stripe", "Shopify", "Slack", "Zoom", "Dropbox", "Adobe", "Salesforce", "Oracle", "IBM", "Intel",
    "NVIDIA", "PayPal", "Twitter", "LinkedIn", "GitHub", "Atlassian", "MongoDB", "Redis", "Docker",
    "Kubernetes", "AWS", "Google Cloud", "Microsoft Azure", "IBM Cloud", "DigitalOcean", "Heroku",
    "Vercel", "Netlify", "Cloudflare", "Akamai", "Fastly", "Twilio", "SendGrid", "Mailchimp",
    "HubSpot", "Zendesk", "Intercom", "Freshworks", "Monday.com", "Asana", "Trello", "Notion"
]

INDIAN_CITIES = [
    "Mumbai, Maharashtra", "Delhi, Delhi", "Bangalore, Karnataka", "Hyderabad, Telangana",
    "Chennai, Tamil Nadu", "Kolkata, West Bengal", "Pune, Maharashtra", "Ahmedabad, Gujarat",
    "Jaipur, Rajasthan", "Surat, Gujarat", "Lucknow, Uttar Pradesh", "Kanpur, Uttar Pradesh",
    "Nagpur, Maharashtra", "Indore, Madhya Pradesh", "Thane, Maharashtra", "Bhopal, Madhya Pradesh",
    "Visakhapatnam, Andhra Pradesh", "Pimpri-Chinchwad, Maharashtra", "Patna, Bihar", "Vadodara, Gujarat",
    "Ghaziabad, Uttar Pradesh", "Ludhiana, Punjab", "Agra, Uttar Pradesh", "Nashik, Maharashtra",
    "Faridabad, Haryana", "Meerut, Uttar Pradesh", "Rajkot, Gujarat", "Kalyan-Dombivali, Maharashtra",
    "Vasai-Virar, Maharashtra", "Varanasi, Uttar Pradesh"
]

PAKISTANI_CITIES = [
    "Karachi, Sindh", "Lahore, Punjab", "Islamabad, Islamabad Capital Territory", "Rawalpindi, Punjab",
    "Faisalabad, Punjab", "Multan, Punjab", "Gujranwala, Punjab", "Peshawar, Khyber Pakhtunkhwa",
    "Quetta, Balochistan", "Sialkot, Punjab", "Sargodha, Punjab", "Bahawalpur, Punjab",
    "Sukkur, Sindh", "Jhang, Punjab", "Sheikhupura, Punjab", "Mardan, Khyber Pakhtunkhwa",
    "Gujrat, Punjab", "Kasur, Punjab", "Mingora, Khyber Pakhtunkhwa", "Nawabshah, Sindh",
    "Chiniot, Punjab", "Kotri, Sindh", "Khanpur, Punjab", "Hafizabad, Punjab",
    "Kohat, Khyber Pakhtunkhwa", "Jacobabad, Sindh", "Shikarpur, Sindh", "Muzaffargarh, Punjab",
    "Khanewal, Punjab", "Gojra, Punjab"
]

EUROPEAN_CITIES = [
    "London, UK", "Berlin, Germany", "Paris, France", "Madrid, Spain", "Rome, Italy",
    "Amsterdam, Netherlands", "Vienna, Austria", "Brussels, Belgium", "Copenhagen, Denmark",
    "Stockholm, Sweden", "Oslo, Norway", "Helsinki, Finland", "Zurich, Switzerland",
    "Prague, Czech Republic", "Warsaw, Poland", "Budapest, Hungary", "Lisbon, Portugal",
    "Dublin, Ireland", "Athens, Greece", "Bucharest, Romania", "Sofia, Bulgaria",
    "Zagreb, Croatia", "Ljubljana, Slovenia", "Bratislava, Slovakia", "Tallinn, Estonia",
    "Riga, Latvia", "Vilnius, Lithuania", "Luxembourg City, Luxembourg", "Valletta, Malta",
    "Nicosia, Cyprus", "Reykjavik, Iceland", "Monaco, Monaco", "San Marino, San Marino",
    "Vatican City, Vatican", "Andorra la Vella, Andorra", "Liechtenstein, Vaduz", "Moscow, Russia",
    "Kiev, Ukraine", "Minsk, Belarus", "Chisinau, Moldova", "Tirana, Albania",
    "Podgorica, Montenegro", "Sarajevo, Bosnia", "Skopje, North Macedonia", "Belgrade, Serbia"
]

UNIVERSITIES = [
    "Indian Institute of Technology (IIT)", "Indian Institute of Management (IIM)", "Delhi University",
    "Mumbai University", "Bangalore University", "Anna University", "Jadavpur University",
    "University of Delhi", "University of Mumbai", "University of Calcutta", "University of Madras",
    "Pune University", "Osmania University", "Andhra University", "Gujarat University",
    "Rajasthan University", "Punjab University", "Aligarh Muslim University", "Jamia Millia Islamia",
    "Banaras Hindu University", "University of Hyderabad", "Jawaharlal Nehru University",
    "Lahore University of Management Sciences", "University of Karachi", "Quaid-i-Azam University",
    "University of the Punjab", "Aga Khan University", "COMSATS University", "National University of Sciences and Technology",
    "University of Engineering and Technology", "Government College University", "Forman Christian College",
    "Institute of Business Administration", "Lahore School of Economics", "Beaconhouse National University"
]

SKILLS_BY_PROFESSION = {
    "Software Engineer": [
        {"name": "Python", "level": "Expert", "years": 5},
        {"name": "JavaScript", "level": "Advanced", "years": 4},
        {"name": "React", "level": "Advanced", "years": 3},
        {"name": "Node.js", "level": "Advanced", "years": 4},
        {"name": "MongoDB", "level": "Intermediate", "years": 2},
        {"name": "AWS", "level": "Intermediate", "years": 2}
    ],
    "Data Scientist": [
        {"name": "Python", "level": "Expert", "years": 6},
        {"name": "R", "level": "Advanced", "years": 4},
        {"name": "SQL", "level": "Expert", "years": 5},
        {"name": "Machine Learning", "level": "Expert", "years": 5},
        {"name": "TensorFlow", "level": "Advanced", "years": 3},
        {"name": "Pandas", "level": "Expert", "years": 4}
    ],
    "Product Manager": [
        {"name": "Product Strategy", "level": "Expert", "years": 6},
        {"name": "User Research", "level": "Advanced", "years": 4},
        {"name": "Agile/Scrum", "level": "Expert", "years": 5},
        {"name": "Data Analysis", "level": "Advanced", "years": 4},
        {"name": "Roadmapping", "level": "Expert", "years": 5},
        {"name": "Stakeholder Management", "level": "Expert", "years": 6}
    ],
    "UX Designer": [
        {"name": "Figma", "level": "Expert", "years": 4},
        {"name": "Sketch", "level": "Advanced", "years": 3},
        {"name": "Adobe Creative Suite", "level": "Expert", "years": 5},
        {"name": "User Research", "level": "Expert", "years": 4},
        {"name": "Prototyping", "level": "Expert", "years": 4},
        {"name": "Wireframing", "level": "Expert", "years": 4}
    ]
}

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def generate_realistic_username(name: str) -> str:
    """Generate a realistic username without 'test' indicators"""
    # Remove spaces and special characters, convert to lowercase
    base = name.lower().replace(" ", "").replace("'", "").replace("-", "").replace(".", "")
    
    # Add random numbers to make it unique
    suffix = random.randint(10, 9999)
    return f"{base}{suffix}"

def get_realistic_name_and_gender(used_names: set) -> tuple:
    """Get a realistic name and gender from Indian/Pakistani/European names, ensuring uniqueness"""
    max_attempts = 50  # Prevent infinite loops
    
    for _ in range(max_attempts):
        # 50% Asian names (Indian/Pakistani), 30% European names, 20% English names
        region_choice = random.random()
        
        if region_choice < 0.5:
            # Asian names (Indian/Pakistani) - 50%
            if random.random() < 0.6:  # 60% Indian names
                if random.random() < 0.4:  # 40% Muslim names
                    if random.random() < 0.5:
                        name = random.choice(INDIAN_NAMES["muslim_male"])
                        gender = "male"
                    else:
                        name = random.choice(INDIAN_NAMES["muslim_female"])
                        gender = "female"
                else:  # 60% Hindi names
                    if random.random() < 0.5:
                        name = random.choice(INDIAN_NAMES["hindi_male"])
                        gender = "male"
                    else:
                        name = random.choice(INDIAN_NAMES["hindi_female"])
                        gender = "female"
            else:  # 40% Pakistani names (mostly Muslim)
                if random.random() < 0.5:
                    name = random.choice(INDIAN_NAMES["muslim_male"])
                    gender = "male"
                else:
                    name = random.choice(INDIAN_NAMES["muslim_female"])
                    gender = "female"
        elif region_choice < 0.8:
            # European names - 30%
            if random.random() < 0.5:
                name = random.choice(INDIAN_NAMES["european_male"])
                gender = "male"
            else:
                name = random.choice(INDIAN_NAMES["european_female"])
                gender = "female"
        else:
            # English names - 20%
            if random.random() < 0.5:
                name = random.choice(INDIAN_NAMES["english_male"])
                gender = "male"
            else:
                name = random.choice(INDIAN_NAMES["english_female"])
                gender = "female"
        
        # Check if name is already used
        if name not in used_names:
            used_names.add(name)
            return name, gender
    
    # Fallback: if we can't find a unique name, add a random number
    fallback_name = f"{name} {random.randint(1, 999)}"
    used_names.add(fallback_name)
    return fallback_name, gender

def get_professional_photo(gender: str, used_photos: set) -> str:
    """Get a professional profile picture, ensuring uniqueness"""
    available_photos = [photo for photo in PROFESSIONAL_PHOTOS[gender] if photo not in used_photos]
    
    if available_photos:
        photo = random.choice(available_photos)
        used_photos.add(photo)
        return photo
    else:
        # If all photos are used, generate a unique one using multiple sources
        max_attempts = 100
        for attempt in range(max_attempts):
            # Try different photo sources
            if attempt < 50:
                # Use randomuser.me with different IDs
                photo_id = random.randint(1, 200)
                photo = f"https://randomuser.me/api/portraits/{gender}/{photo_id}.jpg"
            elif attempt < 75:
                # Use picsum.photos with different IDs
                photo_id = random.randint(1, 1000)
                photo = f"https://picsum.photos/400/400?random={photo_id}"
            else:
                # Use ui-avatars.com with random initials
                initials = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
                photo = f"https://ui-avatars.com/api/?name={initials}&size=400&background=random"
            
            if photo not in used_photos:
                used_photos.add(photo)
                return photo
        
        # Final fallback - generate a completely unique URL
        unique_id = random.randint(100000, 999999)
        photo = f"https://via.placeholder.com/400x400/4A90E2/FFFFFF?text=Profile+{unique_id}"
        used_photos.add(photo)
        return photo

def get_location() -> str:
    """Get a realistic location from India, Pakistan, or Europe"""
    location_choice = random.random()
    
    if location_choice < 0.4:  # 40% Indian cities
        return random.choice(INDIAN_CITIES)
    elif location_choice < 0.6:  # 20% Pakistani cities
        return random.choice(PAKISTANI_CITIES)
    else:  # 40% European cities
        return random.choice(EUROPEAN_CITIES)

def generate_realistic_profile(used_names: set, used_photos: set) -> Dict[str, Any]:
    """Generate a complete realistic profile"""
    fake = Faker()
    
    # Get realistic name and gender
    name, gender = get_realistic_name_and_gender(used_names)
    username = generate_realistic_username(name)
    email = f"{username}@gmail.com"  # Use gmail instead of example.com
    
    # Select profession and related data
    profession = random.choice(PROFESSIONS)
    years_exp = random.randint(2, 12)
    
    # Get profession-specific skills or generate generic ones
    if profession in SKILLS_BY_PROFESSION:
        skills = SKILLS_BY_PROFESSION[profession].copy()
        # Add some variation to years
        for skill in skills:
            skill["years"] = max(1, skill["years"] + random.randint(-1, 2))
    else:
        # Generate generic skills
        generic_skills = ["Python", "JavaScript", "SQL", "Git", "AWS", "Docker", "Agile", "Communication"]
        skills = []
        for skill_name in random.sample(generic_skills, k=random.randint(4, 6)):
            skills.append({
                "name": skill_name,
                "level": random.choice(["Beginner", "Intermediate", "Advanced", "Expert"]),
                "years": random.randint(1, years_exp)
            })
    
    # Generate experience details
    experience_details = []
    companies_used = random.sample(COMPANIES, k=random.randint(2, 4))
    
    for i, company in enumerate(companies_used):
        is_current = i == 0
        exp_years = random.randint(1, 4)
        
        experience_details.append({
            "company": company,
            "position": profession if i == 0 else f"Senior {profession}",
            "duration": f"{exp_years} years",
            "description": f"Led {random.choice(['cross-functional teams', 'product initiatives', 'development projects', 'design systems'])} to deliver high-impact solutions. Collaborated with stakeholders to drive business objectives and improve user experience.",
            "start_date": str(fake.date_between(start_date='-10y', end_date='-2y')),
            "end_date": None if is_current else str(fake.date_between(start_date='-2y', end_date='today')),
            "current": is_current,
            "technologies": [skill["name"] for skill in skills[:3]] if "Developer" in profession or "Engineer" in profession else []
        })
    
    # Generate projects
    projects = []
    for i in range(random.randint(2, 4)):
        project_types = ["Web Application", "Mobile App", "Data Pipeline", "API Development", "Machine Learning Model", "Dashboard", "E-commerce Platform"]
        project_name = f"{random.choice(project_types)} {i+1}"
        
        projects.append({
            "name": project_name,
            "description": f"Delivered a comprehensive {project_name.lower()} that improved user engagement by {random.randint(20, 60)}% and increased business metrics.",
            "technologies": [skill["name"] for skill in skills[:4]],
            "url": f"https://github.com/{username}/{project_name.lower().replace(' ', '-')}",
            "github_url": f"https://github.com/{username}/{project_name.lower().replace(' ', '-')}",
            "duration": f"{random.randint(3, 12)} months"
        })
    
    # Generate education
    education = [
        {
            "institution": random.choice(UNIVERSITIES),
            "degree": "Master of Science" if years_exp > 5 else "Bachelor of Science",
            "field_of_study": random.choice(["Computer Science", "Information Technology", "Business Administration", "Engineering", "Data Science"]),
            "start_date": str(fake.date_between(start_date='-15y', end_date='-10y')),
            "end_date": str(fake.date_between(start_date='-10y', end_date='-8y')),
            "grade": f"{random.uniform(3.2, 4.0):.2f}",
            "activities": random.choice(["Tech Club President", "Coding Society", "Student Council", "Debate Team"]),
            "description": "Focused on building strong technical and leadership foundations."
        }
    ]
    
    # Generate certifications
    certifications = [
        f"Certified {profession}",
        f"Advanced {random.choice(['Leadership', 'Technical Skills', 'Project Management', 'Data Analysis'])}"
    ]
    
    # Generate languages
    languages = [
        {"name": "English", "proficiency": "Fluent"},
        {"name": "Hindi", "proficiency": "Native"} if "hindi" in name.lower() else {"name": "Urdu", "proficiency": "Native"}
    ]
    
    # Generate interests
    interests = random.sample([
        "Photography", "Travel", "Reading", "Cooking", "Hiking", "Gaming", "Music", "Art", 
        "Sports", "Yoga", "Meditation", "Writing", "Blogging", "Volunteering", "Learning Languages", 
        "Technology", "Innovation", "Startups", "Entrepreneurship", "Fitness", "Running", "Cycling"
    ], k=random.randint(3, 6))
    
    # Generate contact info
    contact_info = {
        "email": email,
        "phone": fake.phone_number(),
        "linkedin": f"https://linkedin.com/in/{username}",
        "github": f"https://github.com/{username}",
        "portfolio": f"https://{username}.portfolio.com"
    }
    
    # Calculate profile score
    profile_score = random.randint(70, 80)  # Good quality profiles (70-80 range)
    
    # Generate work preferences
    work_preferences = {
        "current_employment_mode": ["full-time"],
        "preferred_work_mode": random.choice([["remote"], ["hybrid"], ["on-site"], ["remote", "hybrid"]]),
        "preferred_employment_type": ["full-time"],
        "preferred_location": get_location(),
        "notice_period": random.choice(["2 weeks", "1 month", "2 months"]),
        "availability": random.choice(["immediate", "2 weeks", "1 month"])
    }
    
    # Generate onboarding progress
    onboarding_progress = {
        "step_1_pdf_upload": "completed",
        "step_2_profile_info": "completed", 
        "step_3_work_preferences": "completed",
        "step_4_salary_availability": "completed",
        "current_step": 5,
        "completed": True
    }
    
    return {
        "name": name,
        "username": username,
        "email": email,
        "hashed_password": hash_password("TestUser123!"),
        "profession": profession,
        "designation": profession,
        "location": get_location(),
        "profile_picture": get_professional_photo(gender, used_photos),
        "is_looking_for_job": random.choice([True, False]),
        "expected_salary": f"₹{random.randint(8, 25)}L - ₹{random.randint(15, 40)}L" if random.random() < 0.7 else f"${random.randint(80, 200)}K - ${random.randint(150, 350)}K",
        "current_salary": f"₹{random.randint(6, 20)}L" if random.random() < 0.7 else f"${random.randint(60, 150)}K",
        "experience": f"{years_exp} years",
        "summary": f"Experienced {profession.lower()} with {years_exp} years of expertise in delivering high-quality solutions. Proven track record of leading successful projects and driving business growth through innovative approaches.",
        "skills": skills,
        "experience_details": experience_details,
        "projects": projects,
        "certifications": certifications,
        "contact_info": contact_info,
        "education": education,
        "languages": languages,
        "awards": [
            {
                "title": f"{random.choice(['Best', 'Top', 'Outstanding'])} {random.choice(['Developer', 'Engineer', 'Professional'])}",
                "issuer": random.choice(COMPANIES),
                "date": str(fake.date_between(start_date='-3y', end_date='today')),
                "description": "Awarded for exceptional performance and contribution."
            }
        ],
        "publications": [
            {
                "title": f"Research on {random.choice(['AI', 'Web Technologies', 'Data Science', 'User Experience'])}",
                "publisher": random.choice(UNIVERSITIES),
                "date": str(fake.date_between(start_date='-3y', end_date='today')),
                "url": f"https://research.com/{username}/publication",
                "description": "Published research in a reputed journal."
            }
        ],
        "volunteer_experience": [
            {
                "organization": random.choice(["Red Cross", "UNICEF", "WWF", "Local NGO"]),
                "role": random.choice(["Volunteer", "Coordinator", "Team Lead"]),
                "start_date": str(fake.date_between(start_date='-3y', end_date='-1y')),
                "end_date": str(fake.date_between(start_date='-1y', end_date='today')),
                "description": "Contributed to community service and social causes."
            }
        ],
        "interests": interests,
        "work_preferences": work_preferences,
        "onboarding_progress": onboarding_progress,
        "rating": round(random.uniform(4.2, 5.0), 1),
        "onboarding_completed": True,
        "onboarding_skipped": False,
        "daily_requests": 0,
        "last_request_reset": datetime.utcnow(),
        "job_matching_request_timestamps": [],
        "chat_request_timestamps": [],
        "refresh_token_jti": None,
        "refresh_token_expires_at": None,
        "password_reset_token": None,
        "password_reset_expires_at": None,
        "google_id": None,
        "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 365)),
        "updated_at": datetime.utcnow(),
        "section_order": ["about", "experience", "skills", "projects", "education", "contact", "languages", "awards", "publications", "volunteer", "interests", "preferences"],
        "profile_score": profile_score,
        "profile_variant": "default",
        "is_test_user": True  # Mark as test user
    }

async def create_test_users(count: int) -> Dict[str, Any]:
    """Create test users in database and sync to Algolia"""
    print(f"🚀 Starting creation of {count} test users...")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to database
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    users_collection = db.users
    
    # Initialize Algolia service
    algolia_service = AlgoliaService()
    
    created_users = []
    synced_to_algolia = 0
    errors = []
    used_names = set()
    used_photos = set()
    
    try:
        for i in range(count):
            try:
                print(f"📝 Creating user {i+1}/{count}...")
                
                # Generate profile
                profile = generate_realistic_profile(used_names, used_photos)
                
                # Insert into database
                result = await users_collection.insert_one(profile)
                user_id = str(result.inserted_id)
                profile["_id"] = user_id
                
                print(f"  ✅ User created: {profile['name']} ({profile['email']})")
                print(f"  📊 Profile score: {profile['profile_score']}")
                print(f"  🏢 Company: {profile['experience_details'][0]['company'] if profile['experience_details'] else 'N/A'}")
                
                # Sync to Algolia
                print(f"  🔄 Syncing to Algolia...")
                try:
                    user_obj = UserInDB(**profile)
                    success = await algolia_service.sync_user_to_algolia(user_obj)
                    if success:
                        synced_to_algolia += 1
                        print(f"  ✅ Synced to Algolia successfully")
                    else:
                        print(f"  ❌ Failed to sync to Algolia")
                        errors.append(f"User {profile['name']}: Algolia sync failed")
                except Exception as e:
                    print(f"  ❌ Algolia sync error: {str(e)}")
                    errors.append(f"User {profile['name']}: Algolia sync error - {str(e)}")
                
                created_users.append({
                    "id": user_id,
                    "name": profile["name"],
                    "email": profile["email"],
                    "profession": profile["profession"],
                    "profile_score": profile["profile_score"]
                })
                
                # Progress update
                progress = int(((i + 1) / count) * 100)
                print(f"  📈 Progress: {progress}% ({i+1}/{count})")
                print("-" * 50)
                
            except Exception as e:
                error_msg = f"Error creating user {i+1}: {str(e)}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)
                continue
        
        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)
        print(f"✅ Users created in database: {len(created_users)}")
        print(f"✅ Users synced to Algolia: {synced_to_algolia}")
        print(f"❌ Errors encountered: {len(errors)}")
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if errors:
            print("\n❌ ERRORS:")
            for error in errors:
                print(f"  - {error}")
        
        print("\n🎉 Test user creation completed!")
        print("💡 Note: These users are marked as test users and won't appear in admin panel")
        
        return {
            "success": True,
            "created_count": len(created_users),
            "algolia_synced": synced_to_algolia,
            "errors": errors,
            "users": created_users
        }
        
    finally:
        await client.close()

async def main():
    """Main function to handle command line arguments and create users"""
    parser = argparse.ArgumentParser(description="Create realistic test users for ResumeAgentAI")
    parser.add_argument("count", type=int, help="Number of users to create (1-100)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without actually creating users")
    
    args = parser.parse_args()
    
    if args.count < 1 or args.count > 100:
        print("❌ Error: Count must be between 1 and 100")
        sys.exit(1)
    
    if args.dry_run:
        print(f"🔍 DRY RUN: Would create {args.count} test users")
        print("Sample user data:")
        sample_profile = generate_realistic_profile(set(), set())
        print(json.dumps({
            "name": sample_profile["name"],
            "email": sample_profile["email"],
            "profession": sample_profile["profession"],
            "location": sample_profile["location"],
            "profile_score": sample_profile["profile_score"],
            "is_test_user": sample_profile["is_test_user"]
        }, indent=2))
        return
    
    try:
        result = await create_test_users(args.count)
        
        if result["success"]:
            print(f"\n✅ Successfully created {result['created_count']} test users!")
            if result["algolia_synced"] < result["created_count"]:
                print(f"⚠️  Note: Only {result['algolia_synced']} users were synced to Algolia")
        else:
            print("❌ Failed to create test users")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
