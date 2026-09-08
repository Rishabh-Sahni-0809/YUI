import { useState, useEffect, useRef } from 'react';

export function useScreenPoll(isRunning) {
  const [screenshotBase64, setScreenshotBase64] = useState(null);
  const [lastUpdated, setLastUpdated] = useState('');
  const pollRef = useRef(null);

  useEffect(() => {
    if (!isRunning) {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }

    const fetchScreen = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/screenshot');
        if (res.ok) {
          const data = await res.json();
          if (data.image) {
            setScreenshotBase64(data.image);
            setLastUpdated(new Date().toLocaleTimeString());
          }
        }
      } catch (e) {}
    };

    fetchScreen();
    pollRef.current = setInterval(fetchScreen, 800);

    return () => clearInterval(pollRef.current);
  }, [isRunning]);

  return { screenshotBase64, lastUpdated };
}
