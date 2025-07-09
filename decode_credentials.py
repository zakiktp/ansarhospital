import base64

# Read the Base64-encoded credentials from the 'credentials.b64.txt' file
with open("credentials.b64.txt", "r") as file:
    encoded_credentials = file.read().strip()  # Remove leading/trailing whitespaces

# Remove any unwanted newlines or extra spaces from the Base64 string
encoded_credentials = "".join(encoded_credentials.split())

# Decode the credentials
decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')

# Save the decoded credentials into a .json file
with open('decoded_credentials.json', 'w') as f:
    f.write(decoded_credentials)

print("Decoded credentials saved to 'decoded_credentials.json'.")
