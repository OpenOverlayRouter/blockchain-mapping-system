from patricia_state import PatriciaState

patricia = PatriciaState()
for i in range(0, 100):
    patricia.set_value('192.168.0.' + str(i), "hola")

patricia.to_db()

patricia2 = PatriciaState()
patricia2.from_db()
print(len(patricia2.patricia))