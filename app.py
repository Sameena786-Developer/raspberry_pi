import cv2
cap=cv2.VideoCapture("http://192.0.0.4:8080/video")
while True:
    ret, frame=cap.read()
    if not ret:
        break
    # resized=cv2.resize(frame,(400,300))
    # cv2.rectangle(frame,(100,100),(700,200),(255,255,255),2)

    crop=frame[100:300,200:400]
    cv2.putText(
        frame,"Device ON",(50,50),cv2.FONT_HERSHEY_SIMPLEX,2,(255,0,255),2
    )
    cv2.imshow("camera",frame)
    cv2.imshow("crop",crop)
    if cv2.waitKey(1) & 0xFF ==ord('q'):
        break
cap.release()
cv2.destroyAllWindows()