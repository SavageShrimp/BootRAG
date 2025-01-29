import hashlib

def generate_sha256_hash(input_string):
    """
    Generate the SHA256 hash of a given string.

    Args:
        input_string (str): The string to be hashed.

    Returns:
        str: The hexadecimal representation of the SHA256 hash.
    """
    # Create a SHA256 hash object
    sha256 = hashlib.sha256()

    # Update the hash object with the input string (encoded to bytes)
    sha256.update(input_string.encode('utf-8'))

    # Return the hexadecimal digest of the hash
    return sha256.hexdigest()

# Example usage
if __name__ == "__main__":
    test_string = "Hello, World!"
    hash_result = generate_sha256_hash(test_string)
    print(f"SHA256 Hash: {hash_result}")
