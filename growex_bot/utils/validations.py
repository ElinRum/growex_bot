def is_valid_email(email):
    return "@" in email and "." in email.split("@")[-1]

def is_valid_phone(phone):
    return phone.startswith("+") and phone[1:].isdigit() and len(phone) >= 11