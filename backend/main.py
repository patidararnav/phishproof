from fastapi import FastAPI, HTTPException
import httpx
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json
from dotenv import load_dotenv
from models import Employee, EmailRequest, OrganizationData, Company  # Import the dataclass models
import mailslurp_client
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

async def generate_phishing_email(scope: str, employee: Employee, company_name: str) -> str:
    """Generate phishing email content using Claude API"""
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")

    prompt = f"""Generate a phishing email from security department with the following context:
    Company: {company_name}
    Target Employee: {employee.first_name} {employee.last_name}
    Role: {employee.role}
    
    The email should be an urgent request to change their password due to a security vulnerability.
    Include a sense of urgency and importance.
    The email should be professional and tailored to the employee's role.
    
    Provide the email body in HTML format with appropriate paragraphs and styling. Do not pretext it with anything
    """

    try:
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
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_msg = f"API Error (Status {response.status_code}): {response.text}"
                print(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
            response_data = response.json()
            
            if "content" not in response_data or not response_data["content"]:
                raise HTTPException(status_code=500, detail="No content in API response")
                
            return response_data["content"][0]["text"].strip()

    except httpx.RequestError as e:
        error_msg = f"Request failed: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    
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
    logger.info("Starting test email generation and sending process")
    
    # Create sample test data with all required fields
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
                    email="test.recipient@example.com",
                    reports_to="Test Manager",
                    start_date="2024-01-01",
                    phone="123-456-7890",
                    linkedin_profile_url="https://linkedin.com/in/testuser"
                )
            ]
        )
    )
    
    # Generate email content
    logger.info("Generating email content")
    result = await send_email(test_data)
    
    if result["results"] and result["results"][0]["status"] == "success":
        try:
            # Get SMTP settings from environment
            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            
            if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
                raise ValueError("Missing SMTP configuration")
            
            logger.info(f"Using SMTP server: {smtp_host}:{smtp_port}")
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Urgent: Security Update Required"
            msg['From'] = f"IT Security <{smtp_username}>"
            msg['To'] = test_data.data.employees[0].email
            
            # Add HTML content
            html_content = result["results"][0]["email_content"]
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            logger.info("Connecting to SMTP server...")
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                logger.info("Logging into SMTP server...")
                server.login(smtp_username, smtp_password)
                logger.info("Sending email...")
                server.send_message(msg)
                
            logger.info("Email sent successfully")
            result["email_sent"] = True
            result["smtp_status"] = "Email sent successfully"
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            result["email_sent"] = False
            result["smtp_status"] = f"Failed to send email: {str(e)}"
    else:
        logger.error("Content generation failed, email not sent")
        result["email_sent"] = False
        result["smtp_status"] = "Content generation failed"
    
    logger.info("Test endpoint completed")
    return result


