import re
import json
from openai import OpenAI
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

class ValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"

@dataclass
class MerchantProfile:
    organization: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    phone_number: Optional[str] = None
    merchant_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "organization": self.organization,
            "name": self.name,
            "address": self.address,
            "contact_email": self.contact_email,
            "phone_number": self.phone_number,
            "merchant_id": self.merchant_id
        }

class ValidationEngine:
    FIELD_HINTS = {
        "organization": {
            "missing": "Please provide your organization or company name.",
            "invalid": "Organization name should be between 2 and 100 characters.",
            "example": "e.g., 'TechCorp Inc.', 'Acme Solutions LLC'"
        },
        "merchant_id": {
            "missing": "Please provide your Merchant ID (MID).",
            "invalid": "Merchant ID should be 8-15 alphanumeric characters (letters and numbers only).",
            "example": "e.g., 'TC12345678', 'MERCH98765'"
        },
        "address": {
            "missing": "Please provide your complete business address.",
            "invalid": "Address should include street, city, and be between 10-200 characters.",
            "example": "e.g., '123 Main Street, San Francisco, CA 94105'"
        },
        "phone_number": {
            "missing": "Please provide a contact phone number.",
            "invalid": "Phone number should be 10-15 digits, optionally starting with '+'.",
            "example": "e.g., '+1-555-123-4567', '5551234567'"
        },
        "contact_email": {
            "missing": "If you'd like, you can provide a contact email address.",
            "invalid": "Please provide a valid email address format.",
            "example": "e.g., 'contact@company.com', 'john.doe@example.com'"
        },
        "name": {
            "missing": "Contact name is optional.",
            "invalid": "Contact name should be a valid name.",
            "example": "e.g., 'John Doe', 'Jane Smith'"
        }
    }
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        if not email:
            return False, "Email is missing"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "The email format doesn't appear to be valid"
        return True, "Valid email"
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        if not phone:
            return False, "Phone number is missing"
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
        pattern = r'^\+?[1-9]\d{9,14}$'
        if not re.match(pattern, cleaned):
            return False, "Phone number should be 10-15 digits (with optional country code)"
        return True, "Valid phone number"
    
    @staticmethod
    def validate_mid(mid: str) -> Tuple[bool, str]:
        if not mid:
            return False, "Merchant ID is missing"
        pattern = r'^[A-Z0-9]{8,15}$'
        if not re.match(pattern, mid.upper()):
            return False, "MID should be 8-15 alphanumeric characters (A-Z, 0-9)"
        return True, "Valid MID"
    
    @staticmethod
    def validate_organization(org: str) -> Tuple[bool, str]:
        if not org:
            return False, "Organization name is missing"
        if len(org.strip()) < 2:
            return False, "Organization name should be at least 2 characters"
        if len(org) > 100:
            return False, "Organization name should be less than 100 characters"
        return True, "Valid organization name"
    
    @staticmethod
    def validate_address(address: str) -> Tuple[bool, str]:
        if not address:
            return False, "Address is missing"
        if len(address.strip()) < 10:
            return False, "Address should be more detailed (at least 10 characters)"
        if len(address) > 200:
            return False, "Address should be less than 200 characters"
        return True, "Valid address"
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, str]:
        if not name:
            return False, "Name is missing"
        if len(name.strip()) < 2:
            return False, "Name should be at least 2 characters"
        if len(name) > 100:
            return False, "Name should be less than 100 characters"
        return True, "Valid name"
    
    def get_field_status(self, profile: MerchantProfile, field_name: str) -> Dict[str, str]:
        value = getattr(profile, field_name, None)
        
        if value is None:
            return {
                "status": ValidationStatus.MISSING.value,
                "message": f"{field_name} is not provided",
                "hint": self.FIELD_HINTS.get(field_name, {}).get("missing", ""),
                "example": self.FIELD_HINTS.get(field_name, {}).get("example", "")
            }
        
        validators = {
            "organization": self.validate_organization,
            "merchant_id": self.validate_mid,
            "address": self.validate_address,
            "phone_number": self.validate_phone,
            "contact_email": self.validate_email,
            "name": self.validate_name
        }
        
        validator = validators.get(field_name)
        if validator:
            valid, msg = validator(value)
            return {
                "status": ValidationStatus.VALID.value if valid else ValidationStatus.INVALID.value,
                "message": msg,
                "hint": self.FIELD_HINTS.get(field_name, {}).get("invalid", "") if not valid else "",
                "example": self.FIELD_HINTS.get(field_name, {}).get("example", "") if not valid else ""
            }
        
        return {
            "status": ValidationStatus.VALID.value,
            "message": "Valid",
            "hint": "",
            "example": ""
        }
    
    def get_field_display_name(self, field_name: str) -> str:
        display_names = {
            "organization": "Organization Name",
            "merchant_id": "Merchant ID (MID)",
            "address": "Business Address",
            "phone_number": "Phone Number",
            "contact_email": "Contact Email",
            "name": "Contact Name"
        }
        return display_names.get(field_name, field_name.replace('_', ' ').title())


class AIOnboardingAssistant:
    """AI-powered onboarding assistant using Groq"""
    
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model
    
    def process_with_ai(self, user_input: str, profile: MerchantProfile, conversation_history: List[Dict]) -> Dict:
        """Use AI to process user input and extract merchant data intelligently"""
        
        profile_context = f"""
        Current merchant profile state:
        - Organization: {profile.organization or 'NOT PROVIDED'}
        - Merchant ID: {profile.merchant_id or 'NOT PROVIDED'}
        - Address: {profile.address or 'NOT PROVIDED'}
        - Phone: {profile.phone_number or 'NOT PROVIDED'}
        - Email: {profile.contact_email or 'NOT PROVIDED'}
        - Contact Name: {profile.name or 'NOT PROVIDED'}

        Required fields: Organization, Merchant ID (8-15 alphanumeric), Address, Phone Number
        Optional fields: Email, Contact Name
        """
        
        system_prompt = f"""You are a friendly AI merchant onboarding assistant. 

        IMPORTANT: You MUST respond in two parts separated by "|||DATA|||":

        Part 1: Your conversational message to the user (be friendly and helpful)
        Part 2: A JSON object with the extracted data

        {profile_context}

        Format your response EXACTLY like this:
        Your friendly message here|||DATA|||{{"organization": "extracted or null", "name": "extracted or null", "address": "extracted or null", "contact_email": "extracted or null", "phone_number": "extracted or null", "merchant_id": "extracted or null", "all_complete": true/false, "missing_fields": ["list"], "invalid_fields": ["list"]}}

        Example response:
        Hello! Thanks for sharing that. Let me make sure I got everything right.|||DATA|||{{"organization": "TechCorp", "name": "John", "address": "123 Main St", "contact_email": null, "phone_number": "555-1234", "merchant_id": "TC123", "all_complete": false, "missing_fields": ["contact_email"], "invalid_fields": []}}

        DO NOT include the JSON in your message. Keep your message natural and conversational."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 5 messages for context)
        for msg in conversation_history[-5:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            print(f"🤖 Calling AI model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content.strip()
            print(f"📝 AI Raw Response: {ai_response[:300]}...")
            
            # Split response into message and data
            if "|||DATA|||" in ai_response:
                parts = ai_response.split("|||DATA|||")
                message = parts[0].strip()
                data_json = parts[1].strip() if len(parts) > 1 else "{}"
                
                # Clean the JSON part
                data_json = re.sub(r'```json\s*|\s*```', '', data_json)
                
                try:
                    data = json.loads(data_json)
                    print(f"✅ Parsed data: {data}")
                    return {
                        "message": message,
                        "extracted_data": {
                            "organization": data.get("organization"),
                            "name": data.get("name"),
                            "address": data.get("address"),
                            "contact_email": data.get("contact_email"),
                            "phone_number": data.get("phone_number"),
                            "merchant_id": data.get("merchant_id")
                        },
                        "all_complete": data.get("all_complete", False),
                        "missing_fields": data.get("missing_fields", []),
                        "invalid_fields": data.get("invalid_fields", [])
                    }
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parse error: {e}")
                    print(f"Raw data: {data_json}")
            else:
                print("⚠️ No DATA separator found, treating entire response as message")
            
            # Fallback: treat entire response as message with regex extraction
            return {
                "message": ai_response,
                "extracted_data": self.extract_with_regex(user_input, profile),
                "all_complete": False,
                "missing_fields": [],
                "invalid_fields": []
            }
                
        except Exception as e:
            print(f"❌ AI processing failed: {e}")
            raise e
    
    def extract_with_regex(self, user_input: str, profile: MerchantProfile) -> Dict:
        """Fallback regex extraction"""
        extracted = {
            "organization": None,
            "name": None,
            "address": None,
            "contact_email": None,
            "phone_number": None,
            "merchant_id": None
        }
        
        # Extract MID
        mid_match = re.search(r'(?:MID|merchant\s*id)\s*(?:is\s*)?[:#]?\s*([A-Z0-9]{8,15})', user_input, re.IGNORECASE)
        if mid_match:
            extracted["merchant_id"] = mid_match.group(1).upper()
        
        # Extract email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', user_input)
        if email_match:
            extracted["contact_email"] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(r'\+?[\d\s\-\(\)]{10,15}', user_input)
        if phone_match:
            extracted["phone_number"] = phone_match.group(0).strip()
        
        # Extract address
        address_match = re.search(r'(?:at|located\s+at|address\s*(?:is)?[:#]?)\s*([^,.]+(?:,\s*[^,.]+){2,})', user_input, re.IGNORECASE)
        if address_match:
            extracted["address"] = address_match.group(1).strip()
        
        # Extract organization (if not already set)
        if not profile.organization:
            words = user_input.split()
            if len(words) <= 5:
                extracted["organization"] = user_input.strip()
        
        return extracted


class MerchantOnboardingSystem:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.use_ai = False
        self.ai_assistant = None
        self.model = None
        
        # Try to initialize AI
        try:
            print("🔧 Initializing AI connection...")
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            
            # Try different models
            models_to_try = [
                "llama-3.3-70b-versatile",
                "llama3-70b-8192",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
                "llama-3.1-70b-versatile"
            ]
            
            for model in models_to_try:
                try:
                    print(f"  Testing model: {model}...")
                    test_response = self.client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=10
                    )
                    self.model = model
                    print(f"✅ Connected to Groq AI using model: {model}")
                    self.use_ai = True
                    self.ai_assistant = AIOnboardingAssistant(self.client, model)
                    break
                except Exception as e:
                    print(f"  ❌ Model {model} failed: {e}")
                    continue
            
            if not self.use_ai:
                print("⚠️ Could not connect to any AI model. Falling back to regex.")
                
        except Exception as e:
            print(f"❌ AI initialization failed: {e}")
            print("⚠️ Running in regex-only mode")
            self.client = None
            self.use_ai = False
        
        self.validator = ValidationEngine()
        self.profile = MerchantProfile()
        self.onboarding_attempts = 0
        self.onboarding_complete = False
        self.conversation_history = []
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process user input - AI-powered if available"""
        print(f"\n{'='*60}")
        print(f"📥 Input: {user_input[:100]}...")
        print(f"🤖 AI Mode: {self.use_ai}")
        
        if user_input.lower() == 'exit':
            return {
                "message": "👋 Onboarding cancelled. Feel free to return when you're ready!",
                "type": "system",
                "onboarding_complete": False,
                "extracted_data": None
            }
        
        extracted_data = {}
        ai_message = None
        
        if self.use_ai and self.ai_assistant:
            try:
                # Use AI for processing
                print("🤖 Processing with AI...")
                ai_result = self.ai_assistant.process_with_ai(
                    user_input,
                    self.profile,
                    self.conversation_history
                )
                
                ai_message = ai_result.get("message", "")
                extracted_data = ai_result.get("extracted_data", {})
                all_complete = ai_result.get("all_complete", False)
                
                print(f"📊 AI extracted: {extracted_data}")
                print(f"✅ All complete: {all_complete}")
                
            except Exception as e:
                print(f"❌ AI processing failed: {e}")
                # Fallback to regex
                extracted_data = self.extract_with_regex(user_input)
        else:
            # Regex-only mode
            print("🔄 Using regex extraction")
            extracted_data = self.extract_with_regex(user_input)
        
        # Update profile with extracted data
        self.update_profile_from_extraction(extracted_data)
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Get current state
        missing = self.get_missing_required_fields()
        invalid = self.get_invalid_fields()
        
        self.onboarding_attempts += 1
        
        # Generate appropriate response
        if not missing and not invalid:
            message = self.format_success_message()
            if ai_message:
                message = ai_message + "\n\n" + message
            response_type = "success"
        else:
            if ai_message:
                message = ai_message
            else:
                message = self.generate_polite_reprompt(missing, invalid)
            response_type = "prompt"
        
        # Add assistant response to history
        self.conversation_history.append({"role": "assistant", "content": message})
        
        result = {
            "message": message,
            "type": response_type,
            "onboarding_complete": False,
            "extracted_data": self.profile.to_dict(),
            "profile": self.profile.to_dict(),
            "missing_fields": missing,
            "invalid_fields": invalid
        }
        
        print(f"📤 Response type: {response_type}")
        print(f"{'='*60}\n")
        
        return result
    
    def extract_with_regex(self, user_input: str) -> Dict:
        """Fallback regex extraction"""
        extracted = {
            "organization": None,
            "name": None,
            "address": None,
            "contact_email": None,
            "phone_number": None,
            "merchant_id": None
        }
        
        # MID
        mid_match = re.search(r'(?:MID|merchant\s*id)\s*(?:is\s*)?[:#]?\s*([A-Z0-9]{8,15})', user_input, re.IGNORECASE)
        if mid_match:
            extracted["merchant_id"] = mid_match.group(1).upper()
        
        # Email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', user_input)
        if email_match:
            extracted["contact_email"] = email_match.group(0)
        
        # Phone
        phone_match = re.search(r'\+?[\d\s\-\(\)]{10,15}', user_input)
        if phone_match:
            extracted["phone_number"] = phone_match.group(0).strip()
        
        # Address
        address_match = re.search(r'(?:at|located\s+at|address\s*(?:is)?[:#]?)\s*([^,.]+(?:,\s*[^,.]+){2,})', user_input, re.IGNORECASE)
        if address_match:
            extracted["address"] = address_match.group(1).strip()
        
        # Organization
        if not self.profile.organization:
            words = user_input.split()
            if len(words) <= 5:
                extracted["organization"] = user_input.strip()
        
        return extracted
    
    def update_profile_from_extraction(self, extracted_data: Dict):
        if "organization" in extracted_data and extracted_data["organization"]:
            self.profile.organization = extracted_data["organization"]
        if "name" in extracted_data and extracted_data["name"]:
            self.profile.name = extracted_data["name"]
        if "address" in extracted_data and extracted_data["address"]:
            self.profile.address = extracted_data["address"]
        if "contact_email" in extracted_data and extracted_data["contact_email"]:
            self.profile.contact_email = extracted_data["contact_email"]
        if "phone_number" in extracted_data and extracted_data["phone_number"]:
            self.profile.phone_number = extracted_data["phone_number"]
        if "merchant_id" in extracted_data and extracted_data["merchant_id"]:
            self.profile.merchant_id = extracted_data["merchant_id"]
    
    def get_missing_required_fields(self) -> List[Dict]:
        required_fields = ["organization", "merchant_id", "address", "phone_number"]
        missing = []
        for field in required_fields:
            status = self.validator.get_field_status(self.profile, field)
            if status["status"] == ValidationStatus.MISSING.value:
                missing.append({
                    "field": field,
                    "display_name": self.validator.get_field_display_name(field),
                    "hint": status["hint"],
                    "example": status["example"]
                })
        return missing
    
    def get_invalid_fields(self) -> List[Dict]:
        all_fields = ["organization", "merchant_id", "address", "phone_number", "contact_email", "name"]
        invalid = []
        for field in all_fields:
            status = self.validator.get_field_status(self.profile, field)
            if status["status"] == ValidationStatus.INVALID.value:
                invalid.append({
                    "field": field,
                    "display_name": self.validator.get_field_display_name(field),
                    "current_value": getattr(self.profile, field),
                    "error_message": status["message"],
                    "hint": status["hint"],
                    "example": status["example"]
                })
        return invalid
    
    def generate_polite_reprompt(self, missing: List[Dict], invalid: List[Dict]) -> str:
        prompt_parts = []
        if self.onboarding_attempts == 1:
            prompt_parts.append("🙏 Thank you for that information!")
        else:
            prompt_parts.append("🙏 Thank you for your patience!")
        
        if missing:
            prompt_parts.append("\n📋 **Still Needed:**")
            for item in missing:
                prompt_parts.append(f"  • {item['display_name']}: {item['example']}")
        
        if invalid:
            prompt_parts.append("\n🔧 **Needs Correction:**")
            for item in invalid:
                prompt_parts.append(f"  • {item['display_name']}: {item['error_message']}")
        
        prompt_parts.append("\n💡 You can provide multiple pieces of information at once.")
        
        return "\n".join(prompt_parts)
    
    def format_success_message(self) -> str:
        profile = self.profile
        message = "✅ Great! All required information has been provided successfully!\n\n"
        message += "📊 **Merchant Profile:**\n"
        if profile.organization:
            message += f"  🏢 Organization: {profile.organization}\n"
        if profile.merchant_id:
            message += f"  🆔 MID: {profile.merchant_id}\n"
        if profile.address:
            message += f"  📍 Address: {profile.address}\n"
        if profile.phone_number:
            message += f"  📞 Phone: {profile.phone_number}\n"
        if profile.contact_email:
            message += f"  📧 Email: {profile.contact_email}\n"
        if profile.name:
            message += f"  👤 Contact: {profile.name}\n"
        message += "\nDoes this look correct? (yes/no/edit)"
        return message
    
    def get_backend_payload(self) -> Dict:
        return {
            "Organization": self.profile.organization,
            "MID": self.profile.merchant_id,
            "Address": self.profile.address,
            "Contact": {
                "phone": self.profile.phone_number,
                "email": self.profile.contact_email,
                "name": self.profile.name
            }
        }
    
    def confirm_onboarding(self, confirmation: str) -> Dict[str, Any]:
        if confirmation.lower() in ['yes', 'y']:
            return {
                "message": "🎊 Onboarding completed successfully! Your merchant profile has been created.",
                "type": "success",
                "onboarding_complete": True,
                "backend_payload": self.get_backend_payload(),
                "profile": self.profile.to_dict()
            }
        elif confirmation.lower() in ['edit', 'e']:
            self.onboarding_complete = False
            return {
                "message": "📝 No problem! Please specify which information you'd like to correct.",
                "type": "prompt",
                "onboarding_complete": False
            }
        else:
            return {
                "message": "I didn't understand. Please type 'yes' to confirm, 'edit' to modify, or 'no' to cancel.",
                "type": "prompt",
                "onboarding_complete": False
            }
    
    def reset(self):
        self.profile = MerchantProfile()
        self.onboarding_attempts = 0
        self.onboarding_complete = False
        self.conversation_history = []