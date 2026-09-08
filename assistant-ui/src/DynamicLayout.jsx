import React, { useEffect, useRef, useState } from 'react';
import TitleBar from './components/layout/TitleBar';
import ScreenViewport from './components/vision/ScreenViewport';
import StepCard from './components/agent/StepCard';
import MessageBubble from './components/chat/MessageBubble';
import InputBar from './components/chat/InputBar';
import SubtaskBar from './components/chat/SubtaskBar';
import RightDrawer from './components/layout/RightDrawer';
import BenchmarkDashboard from './components/benchmark/BenchmarkDashboard';
import { useAgentState, PANEL_STATES } from './hooks/useAgentState';
import { useScreenPoll } from './hooks/useScreenPoll';
import { useMetrics } from './hooks/useMetrics';

import './styles/tokens.css';
import './styles/animations.css';

export default function DynamicLayout() {
  const { 
    messages, agentSteps, subtasks, panelState, 
    isRunning, status, sendMessage, setPanelState 
  } = useAgentState();
  
  // Only poll screenshot if we are in screen_agent mode
  const shouldPoll = isRunning && panelState === PANEL_STATES.SCREEN_AGENT;
  const { screenshotBase64, lastUpdated } = useScreenPoll(shouldPoll);
  const metrics = useMetrics();

  // View toggle: 'chat' or 'benchmark'
  const [activeView, setActiveView] = useState('chat');

  const chatRef = useRef(null);
  const stepsRef = useRef(null);

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    stepsRef.current?.scrollTo({ top: stepsRef.current.scrollHeight, behavior: 'smooth' });
  }, [agentSteps]);

  const activeTask = messages.length > 0 && isRunning ? messages[messages.length - 1].text : '';

  // Calculate panel widths based on state
  let leftWidth = '100%';
  let centerWidth = '0%';
  let rightWidth = '0%';

  if (panelState === PANEL_STATES.SCREEN_AGENT) {
    leftWidth = '45%';
    centerWidth = '35%';
    rightWidth = '20%';
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-base)' }}>
      <TitleBar 
        activeTask={activeTask} 
        status={isRunning ? 'running' : 'idle'} 
        routingStatus={metrics.routingStatus}
        cpuPercent={metrics.current.cpu}
        cpuState={metrics.current.state}
        activeView={activeView}
        onViewChange={setActiveView}
      />
      
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', position: 'relative' }}>
        
        {/* ── Benchmark Dashboard View ────────── */}
        {activeView === 'benchmark' && (
          <div style={{ width: '100%', overflow: 'hidden' }}>
            <BenchmarkDashboard metrics={metrics} />
          </div>
        )}

        {/* ── Chat View ──────────────────────── */}
        {activeView === 'chat' && (
          <>
            {/* Left Panel: Chat */}
            <div style={{ 
              width: leftWidth, 
              transition: 'width 300ms ease',
              display: 'flex', 
              flexDirection: 'column', 
              borderRight: panelState !== PANEL_STATES.IDLE ? '1px solid var(--border-default)' : 'none',
              background: 'var(--bg-surface)'
            }}>
              <div ref={chatRef} style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
                {messages.length === 0 && (
                  <div style={{ textAlign: 'center', marginTop: '40px', color: 'var(--text-muted)' }}>
                    Start a task to see Kira in action.
                  </div>
                )}
                {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
              </div>
              
              <div style={{ padding: '0 16px' }}>
                <SubtaskBar subtasks={subtasks} isRunning={isRunning} />
              </div>
              <InputBar onSend={sendMessage} isRunning={isRunning} />
            </div>

            {/* Center Panel: Screen Grounding */}
            <div style={{ 
              width: centerWidth, 
              transition: 'width 300ms ease',
              opacity: panelState === PANEL_STATES.SCREEN_AGENT ? 1 : 0,
              display: 'flex', 
              flexDirection: 'column',
              borderRight: '1px solid var(--border-default)'
            }}>
              {panelState === PANEL_STATES.SCREEN_AGENT && (
                <ScreenViewport 
                  screenshotBase64={screenshotBase64} 
                  lastUpdated={lastUpdated} 
                />
              )}
            </div>

            {/* Right Panel: Step Log */}
            <div style={{ 
              width: rightWidth, 
              transition: 'width 300ms ease',
              opacity: panelState === PANEL_STATES.SCREEN_AGENT ? 1 : 0,
              display: 'flex', 
              flexDirection: 'column', 
              background: 'var(--bg-elevated)' 
            }}>
              {panelState === PANEL_STATES.SCREEN_AGENT && (
                <>
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-default)', fontSize: '12px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>
                    AGENT REASONING
                  </div>
                  <div ref={stepsRef} style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
                    {agentSteps.length === 0 && (
                      <div style={{ textAlign: 'center', marginTop: '40px', color: 'var(--text-muted)', fontSize: '13px' }}>
                        Agent step log appears here.
                      </div>
                    )}
                    {agentSteps.map(step => {
                      const isAction = step.topTag === 'STEP';
                      const isResult = step.topTag === 'VERIFY' || step.topTag === 'DONE';
                      const isFail = step.tag && step.tag.includes('FAIL');
                      
                      let type = 'thought';
                      if (isAction) type = 'action';
                      if (isResult) type = 'result';
                      if (step.body.toLowerCase().includes('click')) type = 'vision';
                      
                      return (
                        <StepCard 
                          key={step.id}
                          type={type}
                          status={isFail ? 'failed' : 'success'}
                          content={step.body}
                          command={step.raw}
                        />
                      );
                    })}
                  </div>
                </>
              )}
            </div>

            {/* Right Drawer: For Data Output */}
            <RightDrawer 
              isOpen={panelState === PANEL_STATES.DATA_OUTPUT} 
              onClose={() => setPanelState(PANEL_STATES.IDLE)} 
            />
          </>
        )}

      </div>
    </div>
  );
}
