import ctypes

# Load the shared library
lib = ctypes.CDLL('./spinnaker_wrapper.so')

# Define function prototypes
lib.initSystem.argtypes = []
lib.initSystem.restype = None

lib.releaseSystem.argtypes = []
lib.releaseSystem.restype = None

lib.getCameraList.argtypes = []
lib.getCameraList.restype = ctypes.c_void_p

# Use the functions
lib.initSystem()

camera_list = lib.getCameraList()
print("Camera List:", camera_list)

lib.releaseSystem()
