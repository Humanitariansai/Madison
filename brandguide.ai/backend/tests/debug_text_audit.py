import cv2
import numpy as np


def debug_text_logic():
    # 1. Create a Synthetic "Text on Dark Background" Image
    # Dark Slate Green: #2F4F4F (R=47, G=79, B=79)
    # Text: White #FFFFFF

    # Create background
    w, h = 100, 50
    bg_color = (47, 79, 79)  # RGB
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = bg_color

    # Draw Text "T"
    cv2.putText(
        img, "Thin Text", (5, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1
    )

    # Simulate Anti-Aliasing via Gaussian Blur
    img_blurred = cv2.GaussianBlur(img, (3, 3), 0)

    # Save for visual check
    cv2.imwrite("debug_text_sample.png", cv2.cvtColor(img_blurred, cv2.COLOR_RGB2BGR))

    print("Simulating Audit on 'debug_text_sample.png'...")

    # --- LOGIC FROM BRAND_AUDITOR.PY ---
    roi = img_blurred
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    num_zeros = np.count_nonzero(mask == 0)
    num_ones = np.count_nonzero(mask == 255)

    # In this case (Dark BG, Light Text):
    # Otsu usually makes Dark = 0, Light = 255.
    # Text is the minority.

    print(f"Zeros (Dark): {num_zeros}, Ones (Light): {num_ones}")

    if num_zeros > num_ones:
        # Background is Dark (0), Text is Light (255)
        print("Detected: Dark Background (Majority)")
        fg_mask = mask == 255
        # bg_mask = mask == 0
    else:
        # Background is Light (255), Text is Dark (0)
        print("Detected: Light Background (Majority)")
        fg_mask = mask == 0
        # bg_mask = mask == 255

    fg_pixels = roi[fg_mask]

    if len(fg_pixels) == 0:
        print("No FG pixels found!")
        return

    # pyrefly: ignore [no-matching-overload]
    text_color = np.mean(fg_pixels, axis=0)  # R,G,B
    print(f"Calculated Text Color (Average): {text_color}")

    is_text_white = all(c > 200 for c in text_color)
    print(f"Is White (>200)? {is_text_white}")

    # --- BETTER LOGIC: MEAN vs MEDIAN vs MAX? ---
    # pyrefly: ignore [no-matching-overload]
    median_color = np.median(fg_pixels, axis=0)
    print(f"Median Text Color: {median_color}")

    max_color = np.max(fg_pixels, axis=0)
    print(f"Max Text Color: {max_color}")

    # Percentile 95?
    # pyrefly: ignore [no-matching-overload]
    p95 = np.percentile(fg_pixels, 95, axis=0)
    print(f"95th Percentile Color: {p95}")

    # --- ROBUST LOGIC ---
    def get_lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    text_lum = get_lum(p95)
    bg_lum = get_lum(bg_color)

    print(f"Text Lum: {text_lum:.1f}, BG Lum: {bg_lum:.1f}")

    # Saturation (Max - Min) / Max
    t_max, t_min = np.max(p95), np.min(p95)
    sat = (t_max - t_min) / t_max if t_max > 0 else 0
    print(f"Saturation: {sat:.2f}")

    # Criteria:
    # 1. High Brightness (Lum > 150)
    # 2. High Contrast vs BG (Diff > 70)
    # 3. Low Saturation (< 0.15) for White

    is_robust_white = (text_lum > 140) and (text_lum - bg_lum > 60) and (sat < 0.20)
    print(f"Is Robust White? {is_robust_white}")


if __name__ == "__main__":
    debug_text_logic()
