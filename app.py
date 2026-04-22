import React, { useState, useRef, useEffect } from 'react';
import { GoogleGenAI } from '@google/genai';
import { Send, ChevronRight, RefreshCw, Upload, Database, GraduationCap, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cn } from './lib/utils';

// Default built-in CSV mock data
const defaultCsvData = `Motor Type,Test ID,Torque (Nm),Dyno Speed (RPM),Voltage (V),Current (A),Input Power (W)
Three-Phase,3P-01 (No Load),0.0,1498,400,1.2,150
Three-Phase,3P-02,5.0,1460,400,2.5,1200
Three-Phase,3P-03,10.0,1410,400,4.2,2100
Three-Phase,3P-04,15.0,1350,400,6.5,3300
Single-Phase,1P-01 (No Load),0.0,2995,230,2.0,110
Single-Phase,1P-02,1.5,2920,230,3.5,600
Single-Phase,1P-03,3.0,2830,230,5.8,1150`;

const systemInstruction = `You are an Electrical Engineering exam writer. 
I have provided raw dynamometer lab data for Single-Phase and Three-Phase AC Induction Motors.

Your task is to generate exam-style calculation questions using ONLY the variables provided in these datasets.

The Rules:
1. You may only ask questions regarding Synchronous Speed, Slip, Mechanical Output Power, Efficiency, and Power Factor.
2. You must assume the UK standard supply frequency of 50 Hz.
3. Do not explicitly state the number of poles; force the student to deduce it by looking at the highest recorded no-load Dyno Speed in the dataset (e.g., chasing 1500 RPM means 4 poles).
4. When I ask for a question, select a random row from the data, provide me the necessary inputs from that row, and wait for my answer. 
5. If my answer is wrong, do not just give me the correct number. Show me the exact formula I should have used.
6. Format mathematical formulas clearly using standard markdown (e.g., \`P_out = T * w\`). Do not use LaTeX brackets like \\( or \\[ . Keep explanations encouraging but strictly academic.
7. Do not reveal the answer until the user attempts it. Keep your intro brief and go straight into the first question.
8. Data Plotting Command: When I provide a CSV file and ask to see a graph, you must use Python Code Execution (matplotlib or seaborn) to plot the requested variables. Always label the X and Y axes clearly with their units. Always include a title. If plotting a Speed-Torque curve, put Speed on the X-axis and Torque on the Y-axis. If the data is noisy, plot a line of best fit or a scatter plot to make the trend clear.
9. The Auto-Graph Command: If I type the command /visual_exam, you must autonomously select a relevant engineering relationship from the uploaded CSV data (e.g., Speed vs. Torque, or Efficiency vs. Mechanical Power), use Python Code Execution to generate and display a clear, well-labeled graph of that relationship. Immediately below the graph, ask a mock exam question that forces me to extract a value from that specific image and use it in a calculation. Stop and wait for my answer.`;

type Message = { role: 'user' | 'model'; parts: any[] };

export default function App() {
  const [csvData, setCsvData] = useState(defaultCsvData);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize the Gemini AI client
  const ai = new GoogleGenAI({ 
    // Injected by Vite define
    apiKey: process.env.GEMINI_API_KEY || '' 
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleStartSession = async () => {
    setMessages([]);
    setIsLoading(true);
    try {
      const initialMsgs: Message[] = [
        { role: 'user', parts: [{ text: 'Hello! I am ready to practice. Please give me my first question.' }] }
      ];
      
      const response = await ai.models.generateContent({
        model: 'gemini-3.1-pro-preview',
        contents: initialMsgs.map(m => ({ role: m.role, parts: m.parts })),
        config: {
          systemInstruction: `${systemInstruction}\n\nHere is the current raw dataset:\n${csvData}`,
          tools: [{ codeExecution: {} }]
        }
      });

      if (response.candidates && response.candidates[0] && response.candidates[0].content.parts) {
        setMessages([
          ...initialMsgs,
          { role: 'model', parts: response.candidates[0].content.parts }
        ]);
      } else if (response.text) {
        setMessages([
          ...initialMsgs,
          { role: 'model', parts: [{ text: response.text }] }
        ]);
      }
    } catch (err) {
      console.error(err);
      setMessages([{ role: 'model', content: 'Connection failed. Please check your config.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const newMessages: Message[] = [...messages, { role: 'user', parts: [{ text: inputValue }] }];
    setMessages(newMessages);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await ai.models.generateContent({
        model: 'gemini-3.1-pro-preview',
        contents: newMessages.map(m => ({ role: m.role, parts: m.parts })),
        config: {
          systemInstruction: `${systemInstruction}\n\nHere is the current raw dataset:\n${csvData}`,
          tools: [{ codeExecution: {} }]
        }
      });

      if (response.candidates && response.candidates[0] && response.candidates[0].content.parts) {
        setMessages([...newMessages, { role: 'model', parts: response.candidates[0].content.parts }]);
      } else if (response.text) {
        setMessages([...newMessages, { role: 'model', parts: [{ text: response.text }] }]);
      }
    } catch (err) {
      console.error(err);
      setMessages([...newMessages, { role: 'model', parts: [{ text: 'Error communicating with AI.' }] }]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderTable = () => {
    const lines = csvData.trim().split('\n');
    if (lines.length === 0) return <p className="p-4 text-[13px] opacity-50 font-mono">No data to display.</p>;
    
    const headers = lines[0].split(',');
    const rows = lines.slice(1).filter(l => l.trim().length > 0).map(l => l.split(','));

    return (
      <table className="w-full text-left border-collapse">
        <thead className="bg-accent-soft text-[10px] uppercase tracking-widest text-accent">
          <tr>
            {headers.map((h, i) => (
              <th key={i} className="p-4 border-b border-subtle font-semibold whitespace-nowrap">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="font-mono text-[13px] opacity-80">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-white/5">
              {row.map((cell, j) => (
                <td key={j} className="p-4 border-b border-subtle whitespace-nowrap">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[#0A0A0B] text-[#E0E0E0] overflow-hidden">
      
      {/* Left Panel: Data Viewer & Editor */}
      <div className="w-full md:w-1/2 p-8 flex flex-col border-r border-subtle bg-[#0A0A0B] z-10 flex-shrink-0">
        <header className="pb-8 mb-6 border-b border-subtle flex justify-between items-baseline">
          <div className="flex flex-col">
            <h1 className="font-serif text-4xl font-light tracking-tight text-accent">DynoGraph AI</h1>
            <p className="text-[10px] uppercase tracking-[0.2em] opacity-50 mt-1">Electrical Engineering Exam Architect // v4.2</p>
          </div>
        </header>

        <div className="flex-1 flex flex-col gap-6 overflow-hidden">
          <div className="flex flex-col h-1/2 min-h-[250px]">
             <div className="flex items-center justify-between mb-2">
                <label className="text-[10px] uppercase tracking-widest opacity-50 flex items-center gap-2">
                  Raw Laboratory Dataset (CSV)
                </label>
             </div>
             <textarea 
               value={csvData}
               onChange={(e) => setCsvData(e.target.value)}
               className="w-full h-full flex-1 p-4 text-[13px] font-mono text-white bg-black/40 border border-subtle focus:outline-none focus:border-[#C4A47C] transition-colors resize-none rounded-lg"
               spellCheck="false"
             />
          </div>

          <div className="flex flex-col h-1/2 flex-1 min-h-[300px] overflow-hidden">
             <div className="flex justify-between items-end mb-2">
                <label className="text-[10px] uppercase tracking-widest opacity-50 mb-1 flex items-center gap-2">
                  Parsed Table View
                </label>
             </div>
             <div className="flex-1 overflow-auto bg-black/40 border border-subtle rounded-lg">
                {renderTable()}
             </div>
          </div>
        </div>
      </div>

      {/* Right Panel: Chat Interface */}
      <div className="w-full md:w-1/2 flex flex-col h-screen max-h-screen bg-[#0E0E10]">
        
        {/* Chat Header */}
        <div className="p-8 border-b border-subtle flex justify-between items-baseline flex-shrink-0">
           <h2 className="font-serif text-2xl font-light text-[#E0E0E0]">Exam Session</h2>
           <button 
             onClick={handleStartSession}
             className="px-4 py-2 uppercase tracking-[0.2em] text-[10px] font-semibold gold-button rounded"
           >
             <span className="flex items-center gap-2">
               <RefreshCw className={cn("w-3 h-3", isLoading && messages.length === 0 ? "animate-spin" : "")} />
               Start Session
             </span>
           </button>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-10 space-y-8">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
              <h3 className="font-serif text-3xl font-light leading-tight mb-4">Ready to practice?</h3>
              <p className="text-sm font-light leading-relaxed opacity-70 mb-8">
                I'll generate exam-style questions based on your active dynamometer lab data. Press Start Session to begin your test.
              </p>
              <div className="mt-8 p-4 bg-accent-soft border border-subtle rounded flex items-start text-left gap-4">
                <div className="p-2 bg-[#C4A47C]/20 rounded mt-1">
                  <GraduationCap className="w-4 h-4 text-accent" />
                </div>
                <p className="text-xs font-light leading-relaxed opacity-70">
                  Note: The bot uses the data from your lab dataset. Calculate synchronous speed by isolating the highest recorded no-load speed to deduce poles.
                </p>
              </div>
            </div>
          ) : (
             messages.map((msg, index) => (
              <div key={index} className={cn("flex w-full", msg.role === 'user' ? "justify-end" : "justify-start")}>
                <div className={cn(
                  "max-w-[85%] p-6 rounded-lg",
                  msg.role === 'user' 
                    ? "bg-[#C4A47C]/10 border border-[#C4A47C]/30 text-white" 
                    : "bg-black/40 border border-subtle text-[#E0E0E0]"
                )}>
                  {msg.role === 'model' && (
                    <div className="flex items-center gap-3 mb-4">
                      <span className="px-2 py-1 bg-accent/10 border border-[#C4A47C]/20 rounded text-[9px] uppercase tracking-widest text-[#C4A47C]">Calculations</span>
                      <span className="text-[11px] opacity-40 font-mono">ID: EXAM-442-{(index+1).toString().padStart(2, '0')}</span>
                    </div>
                  )}
                  {msg.parts.map((p, pIdx) => {
                    if (p.text) {
                      return (
                        <div key={pIdx} className={cn(
                           "prose prose-invert max-w-none leading-relaxed",
                           msg.role === 'user' 
                             ? "font-serif text-xl prose-p:text-white" 
                             : "font-serif text-2xl font-light prose-p:mb-4 prose-code:font-mono prose-code:text-[#C4A47C] prose-code:text-lg"
                        )}>
                          <ReactMarkdown>{p.text}</ReactMarkdown>
                        </div>
                      );
                    } else if (p.executableCode) {
                      return (
                        <div key={pIdx} className="bg-black/60 border border-subtle rounded p-4 mt-4 mb-4">
                          <p className="text-[10px] uppercase tracking-widest text-[#C4A47C] mb-2 font-mono">Python Code Executed</p>
                          <pre className="font-mono text-[11px] opacity-70 overflow-x-auto text-[#E0E0E0]">
                            <code>{p.executableCode.code}</code>
                          </pre>
                        </div>
                      );
                    } else if (p.codeExecutionResult) {
                      return (
                        <div key={pIdx} className="bg-black/60 border border-[rgba(0,255,0,0.15)] rounded p-4 mt-4 mb-4">
                          <p className="text-[10px] uppercase tracking-widest text-green-400 mb-2 font-mono">Outcome: {p.codeExecutionResult.outcome}</p>
                          <pre className="font-mono text-[11px] opacity-70 overflow-x-auto text-[#E0E0E0]">
                            <code>{p.codeExecutionResult.output}</code>
                          </pre>
                        </div>
                      );
                    } else if (p.inlineData) {
                      return (
                        <div key={pIdx} className="mt-6 mb-6 rounded-lg overflow-hidden border border-subtle bg-black/40 p-3 flex justify-center">
                           <img src={`data:${p.inlineData.mimeType};base64,${p.inlineData.data}`} className="max-w-full rounded mx-auto block" alt="Generated Plot" />
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            ))
          )}
          {isLoading && messages.length > 0 && (
             <div className="flex justify-start">
               <div className="bg-black/40 border border-subtle p-6 rounded-lg flex items-center gap-2">
                 <div className="w-2 h-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: '0ms' }} />
                 <div className="w-2 h-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: '150ms' }} />
                 <div className="w-2 h-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: '300ms' }} />
               </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="p-8 border-t border-subtle flex-shrink-0 bg-[#0E0E10]">
          <div className="group">
            <label className="block text-[10px] uppercase tracking-widest opacity-50 mb-3">Your Answer / Calculation</label>
            <div className="flex gap-4">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !isLoading) handleSendMessage();
                }}
                placeholder="e.g. 3.86"
                className="flex-1 bg-black border border-subtle p-4 font-serif text-xl focus:outline-none focus:border-[#C4A47C] transition-colors rounded-none"
                disabled={isLoading || messages.length === 0}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading || messages.length === 0}
                className="px-8 py-4 uppercase tracking-[0.3em] text-[11px] font-semibold gold-button rounded-none whitespace-nowrap"
              >
                Submit
              </button>
            </div>
            <div className="mt-4 flex justify-between">
               <span className="text-[11px] uppercase tracking-widest opacity-40">Status: <span className="text-[#C4A47C]">{(isLoading || messages.length === 0) ? 'Idle' : 'Active'}</span></span>
               <span className="text-[11px] uppercase tracking-widest opacity-40">Verification via Gemini</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Quick helper missing from lucide import above
function TablePropertiesIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M15 3v18" />
      <rect width="18" height="18" x="3" y="3" rx="2" />
      <path d="M21 9H3" />
      <path d="M21 15H3" />
    </svg>
  );
}

