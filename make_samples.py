"""Builds the two messy sample files. All data is invented."""

import csv
import os
import random

random.seed(7)

os.makedirs("data", exist_ok=True)

FIRST = ["Lucía", "Martín", "Sofía", "Joaquín", "Valentina", "Tomás", "Camila",
         "Nicolás", "Agustina", "Facundo", "Micaela", "Santiago", "Julieta",
         "Ezequiel", "Rocío", "Gonzalo", "Florencia", "Matías", "Brenda", "Iván"]
LAST = ["Gómez", "Fernández", "Rodríguez", "López", "Martínez", "Pereyra",
        "De la Fuente", "Sosa", "Ramírez", "Quiroga", "Del Valle", "Acosta",
        "Ibarra", "Molina", "Suárez", "Vega", "Castro", "Ortiz", "Benítez", "Ruiz"]
CITIES = ["Quilmes", "Berazategui", "Avellaneda", "La Plata", "Lanús",
          "Florencio Varela", "Bernal", "Wilde", "Ezpeleta", "Temperley"]
STATUS = ["Activo", "activo", "ACTIVO", "Inactivo", "inactivo", "Pendiente"]


def messy_name(first, last):
    full = f"{first} {last}"
    roll = random.random()
    if roll < 0.18:
        return full.upper()
    if roll < 0.34:
        return full.lower()
    if roll < 0.46:
        return f"  {full}  "
    if roll < 0.56:
        return full.replace(" ", "  ")
    return full


def messy_dni(number):
    roll = random.random()
    if roll < 0.3:
        return f"{str(number)[:2]}.{str(number)[2:5]}.{str(number)[5:]}"
    if roll < 0.4:
        return f" {number} "
    if roll < 0.45:
        return str(number)[:6]  # too short on purpose -> goes to review
    return str(number)


def cuit_check_digit(first_ten):
    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(d) * w for d, w in zip(first_ten, weights))
    rest = 11 - (total % 11)
    return 0 if rest == 11 else (9 if rest == 10 else rest)


def make_cuit(dni, prefix="20"):
    base = f"{prefix}{str(dni).zfill(8)}"
    return base + str(cuit_check_digit(base))


def messy_cuit(cuit, allow_bad=True):
    roll = random.random()
    if roll < 0.3:
        return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"
    if roll < 0.4:
        return f"{cuit[:2]} {cuit[2:10]} {cuit[10]}"
    if allow_bad and roll < 0.46:
        wrong = str((int(cuit[10]) + 3) % 10)
        return cuit[:10] + wrong  # broken check digit -> goes to review
    return cuit


def messy_phone(area, number):
    roll = random.random()
    if roll < 0.2:
        return f"+54 9 {area} {number}"
    if roll < 0.35:
        return f"0{area} 15 {number}"
    if roll < 0.5:
        return f"{area}{number}"
    if roll < 0.62:
        return f"({area}) {number[:4]}-{number[4:]}"
    if roll < 0.72:
        return f"0054 9 {area}{number}"
    return f"{area} {number}"


def messy_email(first, last, domain_pool):
    local = f"{first.lower()}.{last.lower().replace(' ', '')}"
    local = (local.replace("á", "a").replace("é", "e").replace("í", "i")
                  .replace("ó", "o").replace("ú", "u").replace("ñ", "n"))
    domain = random.choice(domain_pool)
    roll = random.random()
    if roll < 0.15:
        return f" {local}@{domain} "
    if roll < 0.3:
        return f"{local.upper()}@{domain}"
    if roll < 0.38:
        return f"{local}@gmail.con"          # typo -> fixed automatically
    if roll < 0.44:
        return f"{local}gmail.com"           # missing @ -> goes to review
    return f"{local}@{domain}"


def messy_date(year, month, day):
    roll = random.random()
    if roll < 0.28:
        return f"{day:02d}/{month:02d}/{year}"
    if roll < 0.45:
        return f"{day}/{month}/{str(year)[2:]}"
    if roll < 0.58:
        return f"{year}-{month:02d}-{day:02d}"
    if roll < 0.7:
        return f"{day:02d}-{month:02d}-{year}"
    if roll < 0.8:
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                  "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        return f"{day} de {months[month - 1]} de {year}"
    if roll < 0.86:
        return "31/02/2026"                  # impossible date -> goes to review
    return f"{day:02d}/{month:02d}/{year}"


def messy_amount(value, currency="ARS"):
    roll = random.random()
    if currency == "USD":
        if roll < 0.5:
            return f"U$S {value:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
        return f"USD {value:,.2f}"
    if roll < 0.3:
        return f"$ {value:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    if roll < 0.5:
        return f"{value:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    if roll < 0.65:
        return f"$ {value:,.2f}"
    if roll < 0.75:
        return f"{value:.2f}"
    return f"$ {value:,.0f}".replace(",", ".")


# ---------------------------------------------------------------- clients ---

clients = []
used = []
for i in range(42):
    first = random.choice(FIRST)
    last = random.choice(LAST)
    dni = random.randint(20_000_000, 45_999_999)
    area = random.choice(["11", "221", "351", "341", "223"])
    phone_number = "".join(str(random.randint(0, 9)) for _ in range(10 - len(area)))
    row = {
        "Nombre y Apellido": messy_name(first, last),
        "DNI": messy_dni(dni),
        "Email": messy_email(first, last, ["gmail.com", "hotmail.com", "yahoo.com.ar", "outlook.com"]),
        "Telefono": messy_phone(area, phone_number),
        "Localidad": random.choice(CITIES) + ("  " if random.random() < 0.2 else ""),
        "Fecha de alta": messy_date(random.choice([2024, 2025, 2026]), random.randint(1, 12), random.randint(13, 28)),
        "Estado": random.choice(STATUS),
    }
    clients.append(row)
    used.append((first, last, dni, area, phone_number))

# Three deliberate duplicates, written slightly differently each time.
for first, last, dni, area, phone_number in random.sample(used, 3):
    clients.append({
        "Nombre y Apellido": f"{first.upper()} {last.upper()}",
        "DNI": f"{str(dni)[:2]}.{str(dni)[2:5]}.{str(dni)[5:]}",
        "Email": f"{first.lower()}.{last.lower().replace(' ', '')}@gmail.com",
        "Telefono": f"{area} {phone_number}",
        "Localidad": random.choice(CITIES),
        "Fecha de alta": messy_date(2026, random.randint(1, 9), random.randint(13, 28)),
        "Estado": "activo",
    })

random.shuffle(clients)
with open("data/clientes_sucio.csv", "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(clients[0].keys()))
    writer.writeheader()
    writer.writerows(clients)

# --------------------------------------------------------------- payments ---

CONCEPTS = ["Honorarios", "honorarios ", "Consulta inicial", "CONSULTA INICIAL",
            "Gastos de gestión", "Anticipo", "anticipo", "Servicio mensual"]

payments = []
used_p = []
for i in range(38):
    first = random.choice(FIRST)
    last = random.choice(LAST)
    dni = random.randint(20_000_000, 45_999_999)
    cuit = make_cuit(dni)
    currency = "USD" if random.random() < 0.2 else "ARS"
    value = round(random.uniform(15_000, 480_000), 2) if currency == "ARS" else round(random.uniform(80, 1500), 2)
    row = {
        "Razon Social": messy_name(first, last),
        "CUIT": messy_cuit(cuit),
        "Concepto": random.choice(CONCEPTS),
        "Importe": messy_amount(value, currency),
        "Fecha de pago": messy_date(random.choice([2025, 2026]), random.randint(1, 12), random.randint(13, 28)),
        "Fecha de vencimiento": messy_date(2026, random.randint(1, 12), random.randint(13, 28)),
        "Comprobante": f"{random.choice(['A', 'B', 'C'])}-{random.randint(1, 9):04d}-{random.randint(1, 99999):08d}",
    }
    payments.append(row)
    used_p.append((first, last, cuit, currency, value))

for first, last, cuit, currency, value in random.sample(used_p, 2):
    payments.append({
        "Razon Social": f"  {first} {last}  ",
        "CUIT": f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}",
        "Concepto": "Honorarios",
        "Importe": messy_amount(value, currency),
        "Fecha de pago": messy_date(2026, random.randint(1, 9), random.randint(13, 28)),
        "Fecha de vencimiento": messy_date(2026, random.randint(1, 12), random.randint(13, 28)),
        "Comprobante": f"A-0001-{random.randint(1, 99999):08d}",
    })

random.shuffle(payments)
with open("data/pagos_sucio.csv", "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(payments[0].keys()))
    writer.writeheader()
    writer.writerows(payments)

print(f"clientes_sucio.csv: {len(clients)} rows")
print(f"pagos_sucio.csv: {len(payments)} rows")
