import cv2
import os
import shutil

def contains_marble(frame_bgr, crop_size=300, min_area=2000, max_area=100000, thresh_val=100):
    """
    Detects if a marble is present in the center of the given image.
    
    Args:
        image_path (str): Path to the image file.
        crop_size (int): Size of the center square crop.
        min_area (int): Minimum contour area to be considered a marble.
        max_area (int): Maximum contour area to be considered a marble.
        thresh_val (int): Threshold value for binarization.
        
    Returns:
        bool: True if a marble is detected, False otherwise.
    """
    # 1. Load Image
    if frame_bgr is None:
        print(f"Warning: Could not load image at {image_path}")
        return False

    height, width = frame_bgr.shape[:2]

    # 2. Fast Cropping
    start_x = max(0, width // 2 - crop_size // 2)
    start_y = max(0, height // 2 - crop_size // 2)
    
    # Slice the numpy array
    center_crop = frame_bgr[start_y:start_y+crop_size, start_x:start_x+crop_size]

    # 3. Optimized Processing (Grayscale -> Blur -> Threshold -> Invert)
    frame_gray = cv2.cvtColor(center_crop, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(frame_gray, (5, 5), 0)
    
    _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
    inv_thresh = cv2.bitwise_not(thresh)

    # 4. Contour Detection
    contours, _ = cv2.findContours(inv_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. Validation
    # If any contour matches the area criteria, a marble is present
    for c in contours:
        area = cv2.contourArea(c)
        if min_area <= area <= max_area:
            return True

    return False

if __name__ == "__main__":
    # Example usage for filtering a folder of images
    source_folder = "out/"
    dataset_folder = "dataset_images/"

    os.makedirs(dataset_folder, exist_ok=True)

    for filename in os.listdir(source_folder):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            file_path = os.path.join(source_folder, filename)
            img = cv2.imread(file_path)
            
            # Check if the image contains a marble
            if contains_marble(img):
                # Save/move it to your final dataset folder
                destination_path = os.path.join(dataset_folder, filename)
                shutil.copy(file_path, destination_path)
                print(f"Saved: {filename}")