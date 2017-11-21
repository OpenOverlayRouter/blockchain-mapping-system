import math

a = float(input("Dame la 1a constante: "))
b = float(input("Dame la 2a constante: "))
c = float(input("Dame la 3a constante: "))

d = b**2 - 4*a*c

if d < 0:
    print("No existe una solucion real")
if d > 0:
    x1 = (-b + math.sqrt(d)) / (2 * a)
    if d == 0:
        print "La solucion es", x1
    else:
        x2 = (-b - math.sqrt(d)) / (2 * a)
        print "Las soluciones son", x1, "y", x2
