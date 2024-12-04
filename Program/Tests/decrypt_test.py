import numpy as np
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


def selective_encrypt(region, key):
    """
    Chiffrement sélectif des 6 bits LSB d'une région.
    """
    iv = get_random_bytes(16) 
    cipher = AES.new(key, AES.MODE_CBC, iv)

    flat_region = region.flatten()

    # Extract the 6 LSBs
    lsb_bits = flat_region & 0x3F  # Mask

    # Pad the LSBs
    padding_length = (16 - len(lsb_bits) % 16) % 16
    padded_lsb_bits = np.pad(lsb_bits, (0, padding_length), mode='constant', constant_values=0)

    # Encrypt the padded LSBs
    encrypted_lsb_bytes = cipher.encrypt(padded_lsb_bits.tobytes())
    

    encrypted_lsb = np.frombuffer(encrypted_lsb_bytes, dtype=np.uint8)[:len(lsb_bits)]
    encrypted_msb = encrypted_msb = encrypted_lsb & 0xC0  # Extract the 2 MSBs

    # Replace the 6 LSBs with the encrypted LSBs
    flat_region &= 0xC0
    flat_region |= encrypted_lsb & 0x3F  # Set the new 6 LSBs

    encrypted_region = flat_region.reshape(region.shape)

    return encrypted_region, iv, encrypted_msb


def selective_decrypt(encrypted_region, key, iv, original_shape, encrypted_msb):
    """
    Déchiffrement sélectif des 6 bits LSB d'une région.
    """
    cipher = AES.new(key, AES.MODE_CBC, iv)

    flat_region = encrypted_region.flatten()

    # Extract the 6 LSBs
    encrypted_lsb = flat_region & 0x3F  # Mask
    encrypted_lsb |= encrypted_msb  # Set the 2 MSBs

    # Pad the LSBs
    padding_length = (16 - len(encrypted_lsb) % 16) % 16
    padded_encrypted_lsb = np.pad(encrypted_lsb, (0, padding_length), mode='constant', constant_values=0)

    # Decrypt the padded LSBs
    decrypted_lsb_bytes = cipher.decrypt(padded_encrypted_lsb.tobytes())

    decrypted_lsb = np.frombuffer(decrypted_lsb_bytes, dtype=np.uint8)[:len(encrypted_lsb)]

    # Replace the 6 LSBs with the decrypted LSBs
    flat_region &= 0xC0
    flat_region |= decrypted_lsb & 0x3F  # Set the new 6 LSBs

    decrypted_region = flat_region.reshape(original_shape)

    return decrypted_region


# random data
region = np.random.randint(0, 256, (16, 16), dtype=np.uint8)
key = get_random_bytes(16)

# Encryption & Decryption
encrypted_region, new_iv, encrypted_msb = selective_encrypt(region, key)

decrypted_region = selective_decrypt(encrypted_region, key, new_iv, region.shape, encrypted_msb)

print("LSB :", region.flatten() & 0x3F)
print("LSB crypted :", encrypted_region.flatten() & 0x3F)
print("LSB decrypted :", decrypted_region.flatten() & 0x3F)

# Test
assert np.array_equal(region, decrypted_region), "Decryption failed!"
print("Test passed!")
