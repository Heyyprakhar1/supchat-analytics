'use client';

import { useState, useRef, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Send, Database, Activity, MessageSquare } from 'lucide-react';

interface QueryResult {
  sql: string;
  data: any[];
  chart_type: 'line' | 'bar' | 'table';
  explanation: string;
}

export default function Home() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [result]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    setLoading(true);
    setHistory(prev => [...prev, input]);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  const renderChart = () => {
    if (!result?.data || result.data.length === 0) return null;

    if (result.chart_type === 'line') {
      return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={result.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={Object.keys(result.data[0])[0]} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={Object.keys(result.data[0])[1]} stroke="#8884d8" />
          </LineChart>
        </ResponsiveContainer>
      );
    } else if (result.chart_type === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={result.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={Object.keys(result.data[0])[0]} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={Object.keys(result.data[0])[1]} fill="#82ca9d" />
          </BarChart>
        </ResponsiveContainer>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-3">
        <Database className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">SupaChat</h1>
          <p className="text-sm text-gray-500">Conversational Analytics</p>
        </div>
        <div className="ml-auto flex items-center gap-2 text-sm text-gray-600">
          <Activity className="w-4 h-4 text-green-500" />
          <span>System Operational</span>
        </div>
      </header>

      <div className="flex-1 flex max-w-7xl mx-auto w-full p-6 gap-6">
        {/* Sidebar - History */}
        <div className="w-64 bg-white rounded-lg shadow-sm border border-gray-200 p-4 hidden md:block">
          <h3 className="font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Query History
          </h3>
          <div className="space-y-2">
            {history.map((q, i) => (
              <div key={i} className="text-sm p-2 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer truncate">
                {q}
              </div>
            ))}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200">
          {/* Results Area */}
          <div className="flex-1 p-6 overflow-y-auto">
            {result ? (
              <div className="space-y-6">
                {/* Explanation */}
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                  <p className="text-blue-800">{result.explanation}</p>
                </div>

                {/* Chart */}
                {result.chart_type !== 'table' && (
                  <div className="bg-white p-4 rounded-lg border border-gray-200">
                    <h3 className="font-semibold mb-4">Visualization</h3>
                    {renderChart()}
                  </div>
                )}

                {/* Data Table */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {result.data.length > 0 && Object.keys(result.data[0]).map((key) => (
                          <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {result.data.map((row, i) => (
                        <tr key={i}>
                          {Object.values(row).map((val: any, j) => (
                            <td key={j} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {val}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* SQL Query */}
                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                  <code className="text-sm font-mono">{result.sql}</code>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Ask me about your blog analytics...</p>
                  <div className="mt-4 space-y-2 text-sm">
                    <button 
                      onClick={() => setInput("Show top trending topics in last 30 days")}
                      className="block w-full text-left px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 transition"
                    >
                      "Show top trending topics in last 30 days"
                    </button>
                    <button 
                      onClick={() => setInput("Compare article engagement by topic")}
                      className="block w-full text-left px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 transition"
                    >
                      "Compare article engagement by topic"
                    </button>
                    <button 
                      onClick={() => setInput("Plot daily views trend for AI articles")}
                      className="block w-full text-left px-4 py-2 bg-gray-100 rounded hover:bg-gray-200 transition"
                    >
                      "Plot daily views trend for AI articles"
                    </button>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your analytics..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? 'Thinking...' : <><Send className="w-4 h-4" /> Send</>}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

