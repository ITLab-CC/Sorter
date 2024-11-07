import matplotlib.pyplot as plt

# Imshow durch Matplotlib ersetzen
if image is not None:
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.axis('off')  # Achsen entfernen
    plt.show()
