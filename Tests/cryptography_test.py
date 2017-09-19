import cryptography as cr

privkey = '18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725'
u_pubkey = '0450863ad64a87ae8a2fe83c1af1a8403cb53f53e486d8511dad8a04887e5b23522cd470243453a299fa9e77237716103abc11a1df38855ed6f2ee187e9c582ba6'
hash_160 = '010966776006953d5567439e5e39f86a0d273bee'
address = '16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM'

print ("=== TESTING CRYPTOGRAPHY ===")

print ("public key: ", end='')
t_u_pubkey = cr.privkey_to_pubkey(privkey, compressed=False)
print ('OK') if t_u_pubkey == u_pubkey else print ('FAIL')

print ("hash160: ", end='')
t_hash160 = cr.pubkey_to_hash160(t_u_pubkey)
print ('OK') if t_hash160 == hash_160 else print ('FAIL')

print ("address: ", end='')
t_address_1 = cr.pubkey_to_address(t_u_pubkey)
t_address_2 = cr.hash160_to_address(t_hash160)
print ('OK') if t_address_1 == t_address_2 == address else print ('FAIL')