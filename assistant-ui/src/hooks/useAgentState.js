import { useState, useCallback } from 'react';

export const PANEL_STATES = {
  IDLE: 'idle',
  TEXT_RESPONSE: 'text',
  SCREEN_AGENT: 'screen_agent',
  DATA_OUTPUT: 'data_output',
};

export function useAgentState() {
  const [messages, setMessages] = useState([]);
  const [agentSteps, setAgentSteps] = useState([]);
  const [subtasks, setSubtasks] = useState([]);
  const [panelState, setPanelState] = useState(PANEL_STATES.IDLE);
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState('Idle');

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isRunning) return;
    
    const userMsg = { role: 'user', text: text.trim(), actions: [] };
    setMessages(prev => [...prev, userMsg]);
    setIsRunning(true);
    setStatus('Processing...');
    
    setAgentSteps([]);
    setSubtasks([]);

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
      let currentActions = [];
      let currentTaskType = 'text';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;

            if (dataStr.startsWith('[METADATA]')) {
              try {
                const meta = JSON.parse(dataStr.replace('[METADATA]', '').trim());
                currentTaskType = meta.task_type;
                if (meta.subtasks) setSubtasks(meta.subtasks);
                
                if (meta.task_type === 'screen_automation') {
                  setPanelState(PANEL_STATES.SCREEN_AGENT);
                } else if (meta.task_type === 'data_output') {
                  setPanelState(PANEL_STATES.DATA_OUTPUT);
                } else {
                  setPanelState(PANEL_STATES.TEXT_RESPONSE);
                }
              } catch (e) {}
              continue;
            }

            const m = dataStr.match(/^\[AGENT(?::([^\]]+))?\]\s*(.*)/i);
            if (m) {
               const tag = m[1] || 'STEP';
               const body = m[2];
               
               // Create step log entry
               setAgentSteps(prev => [...prev, { id: prev.length, tag, topTag: tag.split(':')[0], body, raw: dataStr }]);
               
               // Also convert into ActionPill data for inline chat
               let tool = 'default';
               let label = body;
               if (body.toLowerCase().includes('hotkey')) tool = 'hotkey';
               else if (body.toLowerCase().includes('typed')) tool = 'type';
               else if (body.toLowerCase().includes('wait')) tool = 'wait';
               else if (body.toLowerCase().includes('click')) tool = 'click';
               else if (body.toLowerCase().includes('navigate')) tool = 'navigate';
               else if (body.toLowerCase().includes('screen')) tool = 'vision';

               const newAction = { tool, label, status: 'success' };
               currentActions = [...currentActions, newAction];

               setMessages(prev => {
                 const newMsgs = [...prev];
                 // Find the last kira message or create one
                 if (newMsgs[newMsgs.length - 1]?.role !== 'kira') {
                   newMsgs.push({ role: 'kira', text: '', actions: currentActions });
                 } else {
                   newMsgs[newMsgs.length - 1].actions = currentActions;
                 }
                 return newMsgs;
               });
            } else {
               botText += dataStr + "\n";
               setMessages(prev => {
                 const newMsgs = [...prev];
                 if (newMsgs[newMsgs.length - 1]?.role === 'kira') {
                   newMsgs[newMsgs.length - 1].text = botText.trim();
                 } else {
                   newMsgs.push({ role: 'kira', text: botText.trim(), actions: currentActions });
                 }
                 return newMsgs;
               });
            }
          }
        }
      }
      
      setStatus('Ready');
      if (currentTaskType === 'text') {
        // Return to idle after text response is fully generated
        setTimeout(() => setPanelState(PANEL_STATES.IDLE), 5000);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'kira', text: "Connection error.", actions: [] }]);
      setStatus('Error');
    } finally {
      setIsRunning(false);
    }
  }, [isRunning]);

  return { messages, agentSteps, subtasks, panelState, isRunning, status, sendMessage, setPanelState };
}
