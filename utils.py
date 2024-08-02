def get_secret_key():
    import os
    if os.path.exists('.key'):
        with open('.key', 'rb') as key_file:
            return key_file.read()
    secret_key = os.urandom(24)
    with open('.key', 'wb') as key_file:
        key_file.write(secret_key)
    return secret_key
