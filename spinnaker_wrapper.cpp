// spinnaker_wrapper.cpp
#include <Spinnaker.h>
#include <iostream>

extern "C" {
    Spinnaker::SystemPtr systemInstance = nullptr;

    void initSystem() {
        try {
            // Initialize the Spinnaker system
            systemInstance = Spinnaker::System::GetInstance();
            std::cout << "Spinnaker System Initialized" << std::endl;
        } catch (const Spinnaker::Exception& e) {
            std::cerr << "Error initializing Spinnaker System: " << e.what() << std::endl;
        }
    }

    void releaseSystem() {
        if (systemInstance) {
            try {
                systemInstance->ReleaseInstance();
                systemInstance = nullptr;
                std::cout << "Spinnaker System Released" << std::endl;
            } catch (const Spinnaker::Exception& e) {
                std::cerr << "Error releasing Spinnaker System: " << e.what() << std::endl;
            }
        }
    }

    void* getCameraList() {
        if (systemInstance) {
            try {
                Spinnaker::CameraList* cameraList = new Spinnaker::CameraList(systemInstance->GetCameras());
                return static_cast<void*>(cameraList);
            } catch (const Spinnaker::Exception& e) {
                std::cerr << "Error getting CameraList: " << e.what() << std::endl;
                return nullptr;
            }
        } else {
            std::cerr << "Spinnaker System not initialized" << std::endl;
            return nullptr;
        }
    }

    void releaseCameraList(void* cameraListPtr) {
        Spinnaker::CameraList* cameraList = static_cast<Spinnaker::CameraList*>(cameraListPtr);
        if (cameraList) {
            delete cameraList;
            std::cout << "CameraList Released" << std::endl;
        } else {
            std::cerr << "Invalid CameraList pointer" << std::endl;
        }
    }

    // Add more wrapper functions as needed
}
