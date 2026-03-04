import barcode
from barcode.writer import ImageWriter

def generate_barcode(roll_number):
    # Use Code128 (supports letters + numbers)
    code = barcode.get('code128', roll_number, writer=ImageWriter())

    filename = code.save(f"barcodes/{roll_number}")

    print(f"✅ Barcode generated for {roll_number}")
    print(f"Saved as: {filename}.png")


if __name__ == "__main__":
    import os

    # Create folder if not exists
    if not os.path.exists("barcodes"):
        os.makedirs("barcodes")

    # Example roll numbers
    roll_numbers = [
        "22A91A61B0",
        "22A91A61B1",
        "22A91A61B2"
    ]

    for roll in roll_numbers:
        generate_barcode(roll)