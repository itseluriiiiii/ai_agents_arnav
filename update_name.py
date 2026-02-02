#!/usr/bin/env python3
"""
Quick script to update user name in AI Email Agent profile.
"""

import json
import os
import sys

def update_profile_name(user_email, new_name):
    """Update the user's profile with their preferred name."""
    profile_path = f"profiles/{user_email}.json"
    
    try:
        # Load existing profile
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = json.load(f)
        else:
            print(f"No profile found for {user_email}")
            return False
        
        # Update name patterns
        if 'style_metrics' not in profile:
            profile['style_metrics'] = {}
        
        profile['style_metrics']['greeting_patterns'] = [
            f"Hi {new_name}", 
            f"Dear {new_name}", 
            f"Hello {new_name}"
        ]
        
        profile['style_metrics']['signature_patterns'] = [
            f"Best regards, {new_name}", 
            f"Thanks, {new_name}", 
            f"Sincerely, {new_name}"
        ]
        
        profile['style_metrics']['common_phrases'] = [
            f"Best, {new_name}", 
            f"Regards, {new_name}"
        ]
        
        # Save updated profile
        os.makedirs('profiles', exist_ok=True)
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2, default=str)
        
        print(f"+ Profile updated for {user_email}")
        print(f"+ Name set to: {new_name}")
        print(f"+ Greetings: {', '.join(profile['style_metrics']['greeting_patterns'])}")
        print(f"+ Signatures: {', '.join(profile['style_metrics']['signature_patterns'])}")
        return True
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python update_name.py <email> <name>")
        print("Example: python update_name.py user@example.com Alice")
        return
    
    email = sys.argv[1]
    name = sys.argv[2]
    
    print(f"Updating profile for {email} with name '{name}'...")
    
    if update_profile_name(email, name):
        print("\n+ Profile successfully updated!")
        print("\nTest with:")
        print(f"email-agent draft --topic 'Test' --recipient 'test@example.com' --user {email}")
    else:
        print("\n- Failed to update profile")

if __name__ == "__main__":
    main()