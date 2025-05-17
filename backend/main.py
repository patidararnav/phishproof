from fastapi import FastAPI, HTTPException
import httpx
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json
from models import Employee, EmailRequest, OrganizationData  # Import the dataclass models

async def generate_phishing_email(scope: str, employee: Employee, company_name: str) -> dict:
    """Generate phishing email content using Claude API"""
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    prompt = f"""Generate a convincing phishing email with the following context:
    Company: {company_name}
    Target Employee: {employee.name.first_name} {employee.name.last_name}
    Role: {employee.role}
    Attack Scope: {scope}
    
    The email should be professional, convincing, and tailored to the employee's role.
    
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
                "max_tokens": 1000,
                "response_format": {"type": "json_object"}
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to generate email content")
        
        return response.json()["content"][0]["text"]

app = FastAPI()

@app.get("/")
async def root():
    

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
            
            # Parse the JSON response
            email_data = json.loads(email_content)
            
            # Send the email
            await send_email_via_smtp(
                employee,
                email_data["subject"],
                email_data["body"],
                request.data.company.name,
                request.data.company.manager
            )
            
            results.append({
                "employee": employee.name,
                "status": "success",
                "email": employee.email
            })
            
        except Exception as e:
            results.append({
                "employee": employee.name,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "message": f"Processed {len(request.data.employees)} employees",
        "results": results
    }


