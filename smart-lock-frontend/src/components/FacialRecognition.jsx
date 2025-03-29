import React, { useEffect, useState } from 'react';
import { useBiometrics } from '../hooks/useBiometrics';
import LiveVideo from './LiveVideo';
import Button from './Button';

const FacialRecognition = () => {
  const { recognitionData, startRecognition, stopRecognition } = useBiometrics();
  const [isRecognizing, setIsRecognizing] = useState(false);

  useEffect(() => {
    if (isRecognizing) {
      startRecognition('facial'); // Specify the recognition type
    } else {
      stopRecognition('facial');
    }

    // Cleanup on unmount
    return () => {
      stopRecognition('facial');
    };
  }, [isRecognizing, startRecognition, stopRecognition]);

  const handleRecognitionToggle = () => {
    setIsRecognizing(!isRecognizing);
  };

  return (
    <div className="status-container">
      <h2>Facial Recognition</h2>
      <div className="video-wrapper">
        <LiveVideo />
        {isRecognizing && (
          <div className="recognition-overlay">
            <p>Scanning...</p>
          </div>
        )}
      </div>
      <Button
        onClick={handleRecognitionToggle}
        text={isRecognizing ? 'Stop Recognition' : 'Start Recognition'}
        variant={isRecognizing ? 'secondary' : 'primary'}
      />
      {recognitionData && (
        <div className={`status-${recognitionData.success ? 'success' : 'error'}`}>
          <h3>Recognition Results:</h3>
          <p>{recognitionData.message}</p>
          {recognitionData.matchPercentage && (
            <p className="match-percentage">Match: {recognitionData.matchPercentage}%</p>
          )}
        </div>
      )}
    </div>
  );
};

export default FacialRecognition;