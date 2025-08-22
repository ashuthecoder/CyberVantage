import os
import datetime
import hashlib
import json

# Global variables for tracking
api_request_log = []
MAX_LOG_SIZE = 100  # Keep last 100 requests in memory
LOG_FILE_PATH = 'logs/gemini_api_requests.log'  # Path to save log file
API_REQUESTS_PER_MINUTE = 0
LAST_REQUEST_RESET = datetime.datetime.now()
MAX_REQUESTS_PER_MINUTE = 10  # Adjust based on your Gemini API limits
request_cache = {}  # For caching responses

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

def log_api_request(function_name, prompt_length, success, response_length=0, error=None):
    """
    Log API request to file for debugging and optimization
    
    Args:
        function_name (str): Name of the function making the API call
        prompt_length (int): Length of the prompt in characters
        success (bool): Whether the API call succeeded
        response_length (int, optional): Length of the response if successful
        error (Exception, optional): Error object if the call failed
    """
    global api_request_log
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add to in-memory log for the monitoring endpoint
    api_request_log.append({
        "timestamp": datetime.datetime.now(),
        "function": function_name,
        "prompt_length": prompt_length,
        "success": success,
        "response_length": response_length,
        "error": str(error) if error else None
    })
    
    # Keep in-memory log size manageable
    if len(api_request_log) > MAX_LOG_SIZE:
        api_request_log = api_request_log[-MAX_LOG_SIZE:]
    
    # Format log entry for file
    status = "SUCCESS" if success else "FAILED"
    log_entry = f"[{timestamp}] {function_name} - {status} - Prompt: {prompt_length} chars"
    
    if success:
        log_entry += f", Response: {response_length} chars"
    if error:
        log_entry += f"\n  ERROR: {error}"
    
    # Write to log file
    try:
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
            log_file.write(log_entry + "\n")
    except Exception as e:
        # Fall back to console if file writing fails
        print(f"[LOG_ERROR] Failed to write to log file: {e}")
        print(log_entry)
        
    # Rotate log file if too large (> 5MB)
    try:
        if os.path.exists(LOG_FILE_PATH) and os.path.getsize(LOG_FILE_PATH) > 5 * 1024 * 1024:
            # Rename current log file with timestamp
            backup_timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            backup_file = f"{LOG_FILE_PATH}.{backup_timestamp}"
            os.rename(LOG_FILE_PATH, backup_file)
            
            # Create fresh log file with rotation notice
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as log_file:
                log_file.write(f"[{timestamp}] Log file rotated. Previous log: {backup_file}\n")
    except Exception as e:
        print(f"[LOG_ERROR] Failed to rotate log file: {e}")

def check_rate_limit():
    """
    Check if we should allow another API request based on rate limits
    
    Returns:
        bool: True if the request is allowed, False if it should be blocked
    """
    global API_REQUESTS_PER_MINUTE, LAST_REQUEST_RESET
    
    current_time = datetime.datetime.now()
    
    # Reset counter every minute
    if (current_time - LAST_REQUEST_RESET).total_seconds() >= 60:
        API_REQUESTS_PER_MINUTE = 0
        LAST_REQUEST_RESET = current_time
    
    # Check if we're over limit
    if API_REQUESTS_PER_MINUTE >= MAX_REQUESTS_PER_MINUTE:
        # Log this rate limiting event
        log_api_request("check_rate_limit", 0, False, 
                        error=f"Rate limit reached: {API_REQUESTS_PER_MINUTE} requests this minute")
        return False
    
    # Increment counter and allow request
    API_REQUESTS_PER_MINUTE += 1
    return True

def get_cached_or_generate(cache_key, generator_func, *args, **kwargs):
    """
    Get from cache or generate with the provided function
    
    Args:
        cache_key (str): Unique key for caching
        generator_func (callable): Function to call if cache miss
        *args, **kwargs: Arguments to pass to generator_func
        
    Returns:
        Any: The cached or newly generated result
    """
    global request_cache
    
    # Use existing cache entry if available and not too old (10 minutes)
    if cache_key in request_cache:
        entry = request_cache[cache_key]
        cache_time = entry.get("timestamp")
        current_time = datetime.datetime.now()
        
        # Cache for 10 minutes
        if cache_time and (current_time - cache_time).total_seconds() < 600:
            log_api_request("cache_hit", len(cache_key), True)
            return entry.get("result")
    
    # Generate new result
    result = generator_func(*args, **kwargs)
    
    # Store in cache
    request_cache[cache_key] = {
        "timestamp": datetime.datetime.now(),
        "result": result
    }
    
    # Keep cache size manageable
    if len(request_cache) > 100:
        # Remove oldest entries
        oldest = sorted(request_cache.items(), key=lambda x: x[1]["timestamp"])
        request_cache = dict(oldest[-100:])
    
    return result

def create_cache_key(prefix, content):
    """
    Create a deterministic cache key for any content
    
    Args:
        prefix (str): Prefix to identify the type of content
        content (str): Content to hash for the key
        
    Returns:
        str: A cache key combining the prefix and a hash of the content
    """
    if not content:
        return f"{prefix}_empty"
        
    # Create a hash of the content
    content_hash = hashlib.md5(content.encode()).hexdigest()
    return f"{prefix}_{content_hash[:16]}"

def get_api_stats():
    """
    Get statistics about API usage
    
    Returns:
        dict: Various statistics about API usage
    """
    if not api_request_log:
        return {
            "total_requests": 0,
            "message": "No API requests logged yet"
        }
    
    # Get time-based stats
    now = datetime.datetime.now()
    one_minute_ago = now - datetime.timedelta(minutes=1)
    five_minutes_ago = now - datetime.timedelta(minutes=5)
    one_hour_ago = now - datetime.timedelta(hours=1)
    
    requests_last_minute = sum(1 for r in api_request_log if r["timestamp"] >= one_minute_ago)
    requests_last_5min = sum(1 for r in api_request_log if r["timestamp"] >= five_minutes_ago)
    requests_last_hour = sum(1 for r in api_request_log if r["timestamp"] >= one_hour_ago)
    
    # Get function-based stats
    function_counts = {}
    for r in api_request_log:
        function_counts[r["function"]] = function_counts.get(r["function"], 0) + 1
    
    # Get error stats
    error_count = sum(1 for r in api_request_log if not r["success"])
    error_messages = [r["error"] for r in api_request_log if r["error"]]
    
    # Get rate limit errors specifically
    rate_limit_errors = sum(1 for r in api_request_log 
                          if r["error"] and any(term in str(r["error"]).lower() 
                                              for term in ["429", "quota", "rate limit"]))
    
    return {
        "total_requests": len(api_request_log),
        "requests_last_minute": requests_last_minute,
        "requests_last_5min": requests_last_5min,
        "requests_last_hour": requests_last_hour,
        "by_function": function_counts,
        "error_count": error_count,
        "rate_limit_errors": rate_limit_errors,
        "recent_errors": error_messages[-5:] if error_messages else [],
        "recent_requests": [
            {
                "time": r["timestamp"].strftime("%H:%M:%S"),
                "function": r["function"],
                "prompt_length": r["prompt_length"],
                "success": r["success"],
                "error": r["error"]
            } for r in sorted(api_request_log, key=lambda x: x["timestamp"], reverse=True)[:10]
        ]
    }

def parse_log_file():
    """
    Parse the log file to extract useful information
    
    Returns:
        dict: Analysis of the log file contents
    """
    if not os.path.exists(LOG_FILE_PATH):
        return {"error": "Log file not found"}
        
    try:
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as log_file:
            log_content = log_file.read()
        
        # Parse logs
        log_entries = log_content.strip().split('\n')
        
        # Analyze by function
        function_stats = {}
        error_count = 0
        success_count = 0
        
        for entry in log_entries:
            if not entry.startswith('['):
                continue
                
            try:
                # Extract function name and status
                parts = entry.split(' - ')
                if len(parts) < 3:
                    continue
                    
                timestamp_part = parts[0]
                function_part = parts[1]
                status_part = parts[2]
                
                function_name = function_part.strip()
                is_success = 'SUCCESS' in status_part
                
                # Update stats
                if function_name not in function_stats:
                    function_stats[function_name] = {'success': 0, 'failure': 0}
                
                if is_success:
                    function_stats[function_name]['success'] += 1
                    success_count += 1
                else:
                    function_stats[function_name]['failure'] += 1
                    error_count += 1
            except:
                continue
        
        # Find recent errors
        error_lines = []
        for i, entry in enumerate(log_entries):
            if 'ERROR' in entry:
                # Include the log entry and the error message
                error_lines.append(entry)
                # Add the next line too if it's an error detail
                if i < len(log_entries) - 1 and not log_entries[i+1].startswith('['):
                    error_lines.append(log_entries[i+1])
        
        # Get last 10 errors
        recent_errors = error_lines[-10:] if len(error_lines) > 10 else error_lines
        
        return {
            "total_entries": len(log_entries),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count/(success_count + error_count)*100) if (success_count + error_count) > 0 else 0,
            "function_stats": function_stats,
            "recent_errors": recent_errors
        }
    except Exception as e:
        return {"error": f"Error parsing log file: {str(e)}"}