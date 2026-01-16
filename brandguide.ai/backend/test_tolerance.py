def calculate_distance(hex1, hex2):
    h1 = hex1.lstrip('#')
    h2 = hex2.lstrip('#')
    rgb1 = tuple(int(h1[i:i+2], 16) for i in (0, 2, 4))
    rgb2 = tuple(int(h2[i:i+2], 16) for i in (0, 2, 4))
    
    dist = sum([(a - b) ** 2 for a, b in zip(rgb1, rgb2)]) ** 0.5
    print(f"Color 1: {hex1} {rgb1}")
    print(f"Color 2: {hex2} {rgb2}")
    print(f"Distance: {dist:.2f}")

# Test Case: Jolly Lush
# Official: Dark Slate Green
official = "#193C40"
# Detected: The second one flagged as off-brand (Lighter Green/Grey)
detected = "#879e9d"

print("--- Checking Jolly Lush Lighter Green ---")
calculate_distance(official, detected)
