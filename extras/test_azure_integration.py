import os
import sys
import datetime
from dotenv import load_dotenv

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a mock Flask app
class MockApp:
    def __init__(self):
        self.config = {}

def setup_environment():
    # Load environment variables
    load_dotenv()
    print("Loading environment variables...")
    
    # Create mock Flask app
    app = MockApp()
    
    # Set up Azure OpenAI configuration
    app.config['AZURE_OPENAI_KEY'] = os.getenv('AZURE_OPENAI_KEY')
    app.config['AZURE_OPENAI_ENDPOINT'] = os.getenv('AZURE_OPENAI_ENDPOINT')
    app.config['AZURE_OPENAI_DEPLOYMENT'] = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4-turbo')
    
    # Check if required environment variables are present
    if app.config['AZURE_OPENAI_KEY'] and app.config['AZURE_OPENAI_ENDPOINT']:
        print("Azure OpenAI configuration found")
    else:
        print("Azure OpenAI configuration missing")
    
    # Set up Gemini configuration
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if gemini_api_key:
        print("Gemini API key found")
    else:
        print("Gemini API key missing")
    
    return app, gemini_api_key

def test_azure_helper():
    print("\n=== Testing Azure OpenAI Helper ===")
    from pyFunctions.azure_openai_helper import azure_openai_completion
    
    app, _ = setup_environment()
    
    # Simple test prompt
    system_prompt = "You are a helpful assistant."
    user_prompt = "Provide a one-sentence definition of cybersecurity."
    
    print("Calling Azure OpenAI API...")
    start_time = datetime.datetime.now()
    
    text, status = azure_openai_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=100,
        temperature=0.7,
        app=app
    )
    
    end_time = datetime.datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    print(f"Status: {status}")
    print(f"Time taken: {elapsed:.2f} seconds")
    
    if status == "SUCCESS":
        print("\nResponse:")
        print("-" * 50)
        print(text)
        print("-" * 50)
        return True
    else:
        print(f"Error: {text}")
        return False

def test_phishing_assignment():
    print("\n=== Testing Phishing Assignment Generation ===")
    
    app, gemini_api_key = setup_environment()
    
    try:
        # Import required modules
        import google.generativeai as genai
        from pyFunctions.phishing_assignment import assign_phishing_creation, assign_phishing_creation_azure
        
        # Test Azure implementation first
        if app.config['AZURE_OPENAI_KEY'] and app.config['AZURE_OPENAI_ENDPOINT']:
            print("Testing Azure OpenAI implementation...")
            start_time = datetime.datetime.now()
            
            result = assign_phishing_creation_azure(app)
            
            end_time = datetime.datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            if result and result.get("success"):
                print(f"Azure test succeeded in {elapsed:.2f} seconds")
                print("\nAssignment excerpt:")
                print("-" * 50)
                # Print only the first 200 characters to keep output manageable
                print(result["assignment"][:200] + "...")
                print("-" * 50)
            else:
                print("Azure test failed")
        
        # Test combined implementation
        if gemini_api_key:
            # Configure Gemini
            genai.configure(api_key=gemini_api_key)
            
            print("\nTesting combined implementation...")
            start_time = datetime.datetime.now()
            
            result = assign_phishing_creation(gemini_api_key, genai, app)
            
            end_time = datetime.datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            if result and result.get("success"):
                print(f"Combined test succeeded in {elapsed:.2f} seconds")
                print("\nAssignment excerpt:")
                print("-" * 50)
                # Print only the first 200 characters to keep output manageable
                print(result["assignment"][:200] + "...")
                print("-" * 50)
                return True
            else:
                print("Combined test failed")
                return False
        else:
            print("Skipping Gemini test (API key not available)")
            return True
        
    except Exception as e:
        print(f"Error in phishing assignment test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_phishing_evaluation():
    print("\n=== Testing Phishing Evaluation ===")
    
    app, gemini_api_key = setup_environment()
    
    # Sample phishing email for testing
    test_email = """
    From: support@netflixpayment.com
    Subject: Your Netflix subscription payment failed
    
    Dear Valued Customer,
    
    We were unable to process your payment for your Netflix subscription. 
    To continue enjoying uninterrupted service, please update your payment information 
    by clicking the link below:
    
    [Update Payment Information](https://netflix-account-verify.com/payment)
    
    If you do not update your payment information within 24 hours, your account will be suspended.
    
    Thank you,
    The Netflix Team
    """
    
    try:
        # Import required modules
        import google.generativeai as genai
        from pyFunctions.phishing_assignment import evaluate_phishing_creation, evaluate_phishing_creation_azure
        
        # Test Azure implementation first
        if app.config['AZURE_OPENAI_KEY'] and app.config['AZURE_OPENAI_ENDPOINT']:
            print("Testing Azure OpenAI implementation...")
            start_time = datetime.datetime.now()
            
            result = evaluate_phishing_creation_azure(test_email, app)
            
            end_time = datetime.datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            if result and "feedback" in result:
                print(f"Azure test succeeded in {elapsed:.2f} seconds")
                print(f"Score: {result['score']}")
                print(f"Effectiveness: {result['effectiveness_rating']}")
                print("\nFeedback excerpt:")
                print("-" * 50)
                # Print only the first 200 characters to keep output manageable
                print(result["feedback"][:200] + "...")
                print("-" * 50)
            else:
                print("Azure test failed")
        
        # Test combined implementation
        if gemini_api_key:
            # Configure Gemini
            genai.configure(api_key=gemini_api_key)
            
            print("\nTesting combined implementation...")
            start_time = datetime.datetime.now()
            
            result = evaluate_phishing_creation(test_email, gemini_api_key, genai, app)
            
            end_time = datetime.datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            if result and "feedback" in result:
                print(f"Combined test succeeded in {elapsed:.2f} seconds")
                print(f"Score: {result['score']}")
                print(f"Effectiveness: {result['effectiveness_rating']}")
                print("\nFeedback excerpt:")
                print("-" * 50)
                # Print only the first 200 characters to keep output manageable
                print(result["feedback"][:200] + "...")
                print("-" * 50)
                return True
            else:
                print("Combined test failed")
                return False
        else:
            print("Skipping Gemini test (API key not available)")
            return True
        
    except Exception as e:
        print(f"Error in phishing evaluation test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_simulation_analysis():
    print("\n=== Testing Simulation Analysis ===")
    
    app, gemini_api_key = setup_environment()
    
    # Create mock user responses
    class MockResponse:
        def __init__(self, is_spam, user_response):
            self.is_spam_actual = is_spam
            self.user_response = user_response
    
    user_responses = [
        MockResponse(True, True),   # Correct - identified phishing
        MockResponse(True, True),   # Correct - identified phishing
        MockResponse(True, False),  # Missed phishing
        MockResponse(False, False), # Correct - identified legitimate
        MockResponse(False, True),  # False positive
    ]
    
    try:
        # Import required modules
        import google.generativeai as genai
        from pyFunctions.simulation import generate_simulation_analysis, generate_simulation_analysis_azure
        
        # Test Azure implementation first
        if app.config['AZURE_OPENAI_KEY'] and app.config['AZURE_OPENAI_ENDPOINT']:
            print("Testing Azure OpenAI implementation...")
            start_time = datetime.datetime.now()
            
            result = generate_simulation_analysis_azure(user_responses, app)
            
            end_time = datetime.datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            if result and result.get("success"):
                print(f"Azure test succeeded in {elapsed:.2f} seconds")
                print(f"Accuracy: {result['accuracy']:.1f}%")
                print("\nAnalysis excerpt:")
                print("-" * 50)
                # Print only the first 200 characters to keep output manageable
                print(result["analysis_html"][:200] + "...")
                print("-" * 50)
            else:
                print("Azure test failed")
        
        # Test combined implementation
        if gemini_api_key:
            # Configure Gemini
            genai.configure(api_key=gemini_api_key)
            
            print("\nTesting combined implementation...")
            start_time = datetime.datetime.now()
            
            result = generate_simulation_analysis(user_responses, gemini_api_key, genai, app)
            
            end_time = datetime.datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            if result and result.get("success"):
                print(f"Combined test succeeded in {elapsed:.2f} seconds")
                print(f"Accuracy: {result['accuracy']:.1f}%")
                print("\nAnalysis excerpt:")
                print("-" * 50)
                # Print only the first 200 characters to keep output manageable
                print(result["analysis_html"][:200] + "...")
                print("-" * 50)
                return True
            else:
                print("Combined test failed")
                return False
        else:
            print("Skipping Gemini test (API key not available)")
            return True
        
    except Exception as e:
        print(f"Error in simulation analysis test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    print("=== CyberVantage Azure OpenAI Integration Tests ===")
    print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    test_results = {
        "Azure Helper": test_azure_helper(),
        "Phishing Assignment": test_phishing_assignment(),
        "Phishing Evaluation": test_phishing_evaluation(),
        "Simulation Analysis": test_simulation_analysis()
    }
    
    print("\n=== Test Results Summary ===")
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed. Please check the output above for details.")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)