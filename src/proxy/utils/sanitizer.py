def sanitize_email_address(address):
    to_sanitize = address
    keepcharacters = ('-','.','_','@')
    return("".join(c for c in to_sanitize if c.isalnum() or c in keepcharacters).rstrip())