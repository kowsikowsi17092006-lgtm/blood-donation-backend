import csv
import random

names = [
    "Arun Kumar", "Priya", "Karthik", "Divya", "Suresh",
    "Kavya", "Vignesh", "Swetha", "Dinesh", "Keerthana",
    "Rahul", "Harini", "Surya", "Nandhini", "Manoj",
    "Anitha", "Praveen", "Deepa", "Santhosh", "Pooja",
    "Gokul", "Aishwarya", "Mohan", "Pavithra", "Aravind",
    "Ramya", "Vijay", "Shalini", "Bala", "Meena"
]

locations = [
    "Chennai", "Coimbatore", "Erode", "Tiruppur",
    "Salem", "Madurai", "Trichy", "Tanjore",
    "Kumbakonam", "Tirunelveli", "Bengaluru",
    "Hyderabad", "Kochi", "Bangalore", "Vellore"
]

blood_groups = [
    "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"
]

with open("donors.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "name",
        "age",
        "blood_group",
        "phone",
        "location"
    ])

    for i in range(500):
        name = random.choice(names)
        age = random.randint(18, 60)
        blood_group = random.choice(blood_groups)

        # Synthetic/demo phone number
        phone = f"90000{i:05d}"

        location = random.choice(locations)

        writer.writerow([
            name,
            age,
            blood_group,
            phone,
            location
        ])

print("500 Indian synthetic donor records created successfully!")
print("File: donors.csv")