from fastapi import FastAPI, HTTPException
import httpx
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json
from dotenv import load_dotenv
from models import Employee, EmailRequest, OrganizationData, Company  # Import the dataclass models

# Load environment variables from .env file
load_dotenv()

async def generate_phishing_email(scope: str, employee: Employee, company_name: str) -> dict:
    """Generate phishing email content using Claude API"""
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    prompt = f"""Generate an email from security department with the following context:
    Company: {company_name}
    Target Employee: {employee.first_name} {employee.last_name}
    Role: {employee.role}
    
    The email should be an urgent request to change their password due to a security vulnerability.
    Include a sense of urgency and importance.
    The email should be professional and tailored to the employee's role.
    
    Return the response in the following JSON format:
    {{
        "subject": "Email subject line",
        "body": "Email body content in HTML format"
    }}
    
    Make sure the body is properly formatted HTML with appropriate paragraphs and styling."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-3-opus-20240229",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
        )
        
        if response.status_code != 200:
            print(f"Status code: {response.status_code}")
            print(f"Response body: {response.text}")
            raise HTTPException(status_code=500, detail=f"Failed to generate email content: {response.text}")
        
        # Parse the response content
        response_data = response.json()
        content = response_data["content"][0]["text"]
        
        # Ensure the response is valid JSON
        print(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse response as JSON")
    
app = FastAPI()

@app.post("/send-email")
async def send_email(request: EmailRequest):
    results = []
    
    for employee in request.data.employees:
        try:
            # Generate phishing email content
            email_content = await generate_phishing_email(
                request.scope,
                employee,
                request.data.company.name
            )
            
            results.append({
                "employee": {
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "email": employee.email
                },
                "status": "success",
                "email_content": email_content
            })
            
        except Exception as e:
            results.append({
                "employee": {
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "email": employee.email
                },
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "message": f"Generated content for {len(request.data.employees)} employees",
        "results": results
    }

@app.get("/test")
async def test_send_email():
    # Create sample test data
    test_data = EmailRequest(
        scope="test phishing simulation",
        data=OrganizationData(
            company=Company(
                name="Test Company",
                domain="testcompany.com"
            ),
            employees=[
                Employee(
                    first_name="Test",
                    last_name="User",
                    role="Software Engineer",
                    reports_to="Test Manager",
                    start_date="2024-01-01",
                    email="test.user@testcompany.com",
                    phone="123-456-7890",
                    linkedin_profile_url="https://linkedin.com/in/testuser"
                )
            ]
        )
    )
    
    # Call the send_email endpoint with test data
    return await send_email(test_data)


