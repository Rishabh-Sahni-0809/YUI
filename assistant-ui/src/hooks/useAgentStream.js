import { useState, useCallback } from 'react';

export function useAgentStream() {
  const [messages, setMessages] = useState([]);
  const [agentSteps, setAgentSteps] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState('Idle');
  
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isRunning) return;
    
    const userMsg = { role: 'user', text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setIsRunning(true);
    setStatus('Processing...');
    
    // Check if task
    const isAgentTask = text.trim().toLowerCase().startsWith("do ") || 
                        text.trim().toLowerCase().startsWith("agent:");
                        
    if (isAgentTask) {
      setAgentSteps([]);
    }

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      if (!response.body) throw new Error("No body in response");

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let botText = "";
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        // parse SSE format "data: <message>\n\n"
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;
            
            // Check if agent tag
            const m = dataStr.match(/^\[AGENT:([^\]]+)\]\s*(.*)/);
            if (m) {
               const tag = m[1];
               const body = m[2];
               setAgentSteps(prev => [...prev, { id: prev.length, tag, topTag: tag.split(':')[0], body, raw: dataStr }]);
            } else {
               botText += dataStr + "\n";
               // Update latest bot message
               setMessages(prev => {
                 const newMsgs = [...prev];
                 if (newMsgs[newMsgs.length - 1]?.role === 'yui') {
                   newMsgs[newMsgs.length - 1].text = botText;
                 } else {
                   newMsgs.push({ role: 'yui', text: botText });
                 }
                 return newMsgs;
               });
            }
          }
        }
      }
      
      if (isAgentTask && !botText) {
         setMessages(prev => [...prev, { role: 'yui', text: "Agent task complete. See step log." }]);
      }
      
      setStatus('Ready');
    } catch (err) {
      setMessages(prev => [...prev, { role: 'yui', text: "Connection error." }]);
      setStatus('Error');
    } finally {
      setIsRunning(false);
    }
  }, [isRunning]);

  return { messages, agentSteps, isRunning, status, sendMessage };
}
