from consensus import Consensus

cons = Consensus()
print cons.get_next_signer()
cons.calculate_next_signer()
print cons.get_next_signer()