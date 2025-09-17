import random
import datetime

# Template emails for when AI generation fails - with more variety
template_emails = [
    {
        "sender": "security@company-portal.net",
        "subject": "Password Reset Required",
        "content": """
            <p>Dear User,</p>
            <p>Our systems have detected that your password will expire in 24 hours.</p>
            <p>To reset your password, please click the link below:</p>
            <p><a href="https://company-portal.net/reset">Reset Password</a></p>
            <p>IT Department</p>
        """,
        "is_spam": True
    },

    {
        "sender": "newsletter@legitimate-news.com",
        "subject": "Weekly Technology Update",
        "content": """
            <p>Hello subscriber,</p>
            <p>This week's top tech stories:</p>
            <ul>
                <li>New advances in AI development</li>
                <li>Tech company quarterly results</li>
                <li>Upcoming product releases</li>
            </ul>
            <p>Read more on our <a href="https://legitimate-news.com">website</a>.</p>
        """,
        "is_spam": False
    },
    {
        "sender": "support@cloud-storage.com",
        "subject": "Action Required: Account Verification",
        "content": """
            <p>Dear Customer,</p>
            <p>We've noticed unusual login attempts on your account.</p>
            <p>To secure your account, please verify your identity by clicking the link below:</p>
            <p><a href="https://verification.cloud-storage.com/verify">Verify Account</a></p>
            <p>If you ignore this message, your account may be temporarily restricted.</p>
            <p>Cloud Storage Security Team</p>
        """,
        "is_spam": True
    },
    {
        "sender": "updates@spotify.com",
        "subject": "Your Weekly Music Recommendations",
        "content": """
            <p>Hey music lover!</p>
            <p>Based on your listening history, we think you might enjoy these tracks:</p>
            <ul>
                <li>"Summer Nights" by The Melodics</li>
                <li>"Distant Dreams" by Skywave</li>
                <li>"Rhythm & Soul" by Urban Collective</li>
            </ul>
            <p>Check out your personalized playlist on the Spotify app or <a href="https://spotify.com/recommendations">website</a>.</p>
            <p>The Spotify Team</p>
        """,
        "is_spam": False
    },
    {
        "sender": "alert@bank-secure.com",
        "subject": "Unusual Activity Detected on Your Account",
        "content": """
            <p>Dear Valued Customer,</p>
            <p>We have detected unusual activity on your bank account.</p>
            <p>Please verify your identity by clicking the link below and entering your account details:</p>
            <p><a href="https://bank-secure.com/verify">Verify Account</a></p>
            <p>If you don't recognize this activity, please contact us immediately.</p>
            <p>Bank Security Team</p>
        """,
        "is_spam": True
    },
    {
        "sender": "no-reply@github.com",
        "subject": "Security Alert: New Sign-in to GitHub",
        "content": """
            <p>Hello,</p>
            <p>We noticed a new sign-in to your GitHub account from a new device:</p>
            <p><strong>Time</strong>: August 14, 2025, 3:15 PM UTC<br>
            <strong>Device</strong>: Chrome on Windows<br>
            <strong>Location</strong>: San Francisco, CA, USA</p>
            <p>If this was you, you can ignore this email. If you didn't sign in recently, please <a href="https://github.com/settings/security">review your account security</a> and change your password.</p>
            <p>The GitHub Team</p>
        """,
        "is_spam": False
    },
    {
        "sender": "customer-service@amaz0n-support.net",
        "subject": "Your Amazon Order #7829345 has been Canceled",
        "content": """
            <p>Dear Amazon Customer,</p>
            <p>Unfortunately, your recent Amazon order (#7829345) has been canceled due to a problem with your payment method.</p>
            <p>To update your payment information and reprocess your order, please click the link below:</p>
            <p><a href="http://amaz0n-support.net/update-payment">Update Payment Information</a></p>
            <p>We apologize for any inconvenience.</p>
            <p>Amazon Customer Service</p>
        """,
        "is_spam": True
    },
    {
        "sender": "newsletter@medium.com",
        "subject": "Top 5 Stories This Week - Medium Digest",
        "content": """
            <p>Your Weekly Medium Digest</p>
            <h3>Top 5 Stories You Might Have Missed:</h3>
            <ul>
                <li>How I Built a Successful Tech Startup in 12 Months</li>
                <li>The Future of AI: Opportunities and Risks</li>
                <li>10 Productivity Hacks That Actually Work</li>
                <li>Understanding Web3: A Beginner's Guide</li>
                <li>Why Remote Work Is Here to Stay</li>
            </ul>
            <p>Read these stories and more on <a href="https://medium.com">Medium</a>.</p>
            <p>You're receiving this email because you're subscribed to Medium's weekly digest.</p>
        """,
        "is_spam": False
    }
]

def get_template_email():
    """
    Return a random template email with enhanced randomization
    to ensure uniqueness across different simulation sessions
    """
    # Generate a unique template for each position
    template = random.choice(template_emails)
    
    # Add significantly more randomness to ensure uniqueness
    random_phrases = [
        "Important update", "Please review", "Action required",
        "Notification", "Alert", "Update", "Information",
        "Confirmation", "Reminder", "News", "Your account",
        "Security notice", "Customer service", "Membership update",
        "Service announcement", "Weekly digest", "New message"
    ]
    
    random_phrase = random.choice(random_phrases)
    random_id = random.randint(10000, 99999)
    current_date = datetime.datetime.now()
    formatted_date = current_date.strftime("%B %d, %Y")
    
    # Modify content to ensure uniqueness by adding a timestamp and reference ID
    timestamp = current_date.strftime("%H:%M:%S")
    content_with_uniqueness = template["content"].replace(
        "</p>", f" (Ref: {random_id}-{timestamp})</p>", 1
    )
    
    # Add a random sender domain variation for more uniqueness
    sender_parts = template["sender"].split("@")
    if len(sender_parts) == 2:
        domain_parts = sender_parts[1].split(".")
        if len(domain_parts) >= 2:
            # Add small random variation to domain name sometimes
            if random.random() < 0.3:
                domain_parts[0] = f"{domain_parts[0]}{random.choice(['', '-', '.'])}{random.randint(1, 99)}"
            sender = f"{sender_parts[0]}@{'.'.join(domain_parts)}"
        else:
            sender = template["sender"]
    else:
        sender = template["sender"]
    
    return {
        "sender": sender,
        "subject": f"{random_phrase}: {template['subject']} #{random_id}",
        "date": formatted_date,
        "content": content_with_uniqueness,
        "is_spam": template["is_spam"]
    }