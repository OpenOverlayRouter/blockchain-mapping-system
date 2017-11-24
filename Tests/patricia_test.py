from patricia_state import Patricia_state

patricia = Patricia_state()
for i in range(0, 100):
    patricia.set_value('192.168.0.' + str(i), "hola")

patricia.to_db()

patricia2 = Patricia_state()
patricia2.from_db()
print(len(patricia2.patricia))
