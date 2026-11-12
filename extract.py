import cv2
video=cv2.VideoCapture("v1.mp4")  # Open the default camera (0)
fps=video.get(cv2.CAP_PROP_FPS)  # Get the frames per second of the video
print("Frames per second:", fps)  # Print the frames per second
video.release()  # Release the video capture object