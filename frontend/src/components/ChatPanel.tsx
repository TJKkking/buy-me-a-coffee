import { useState, useRef, useEffect } from 'react';
import {
  Send,
  Loader2,
  Sparkles,
  Coffee,
  Truck,
  Clock,
  Sun,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { ENDPOINT } from '../utils/config';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolCalls?: Array<{ name: string; args: Record<string, unknown> }>;
}

interface ChatPanelProps {
  onOrderCreated?: () => void;
  storeId?: string;
}

export default function ChatPanel({ onOrderCreated, storeId = 'store_001' }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `你好！👋 欢迎来到 **希希咖啡**！

我是你的智能助手，可以帮你：

- ☕ **点咖啡** - 查看菜单、下单
- 📋 **查订单** - 查询订单状态
- 🛵 **叫配送** - 安排外卖配送
- 🌤️ **查天气** - 了解今日天气
- ⏰ **管时间** - 设置提醒和日程

有什么我可以帮你的吗？`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${ENDPOINT}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Store-Id': storeId,
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      let assistantContent = '';
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        toolCalls: [],
      };

      setMessages((prev) => [...prev, assistantMessage]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('event:')) {
            continue;
          }
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5).trim());

              if (data.session_id) {
                setSessionId(data.session_id);
              }

              if (data.content) {
                assistantContent += data.content;
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage.role === 'assistant') {
                    lastMessage.content = assistantContent;
                  }
                  return newMessages;
                });
              }

              if (data.name && data.args) {
                // Tool call
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage.role === 'assistant') {
                    lastMessage.toolCalls = [
                      ...(lastMessage.toolCalls || []),
                      { name: data.name, args: data.args },
                    ];
                  }
                  return newMessages;
                });
              }
            } catch {
              // 忽略解析错误
            }
          }
        }
      }

      // 检查是否创建了订单
      if (
        assistantContent.includes('订单创建成功') ||
        assistantContent.includes('订单号')
      ) {
        onOrderCreated?.();
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '抱歉，出现了一些问题。请稍后重试。',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const quickActions = [
    { icon: Coffee, label: '看菜单', message: '我想看看菜单' },
    { icon: Truck, label: '查配送', message: '帮我查一下配送状态' },
    { icon: Sun, label: '查天气', message: '今天天气怎么样' },
    { icon: Clock, label: '设提醒', message: '帮我设置一个提醒' },
  ];

  return (
    <div className='flex flex-col h-full bg-gradient-to-b from-cream-50 to-cream-100'>
      {/* 消息区域 */}
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message-bubble flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-coffee-600 to-coffee-700 text-white rounded-br-md'
                  : 'bg-white shadow-md border border-coffee-100 rounded-bl-md'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className='markdown-content prose prose-sm max-w-none'>
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <p className='whitespace-pre-wrap'>{message.content}</p>
              )}

              {/* 工具调用显示 */}
              {message.toolCalls && message.toolCalls.length > 0 && (
                <div className='mt-2 pt-2 border-t border-coffee-100'>
                  <div className='flex flex-wrap gap-1'>
                    {message.toolCalls.map((tool, idx) => (
                      <span
                        key={idx}
                        className='inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-coffee-100 text-coffee-700'
                      >
                        <Sparkles className='w-3 h-3 mr-1' />
                        {tool.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div
                className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-cream-200' : 'text-coffee-400'
                }`}
              >
                {message.timestamp.toLocaleTimeString('zh-CN', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className='flex justify-start'>
            <div className='bg-white shadow-md border border-coffee-100 rounded-2xl rounded-bl-md px-4 py-3'>
              <div className='flex items-center space-x-2 text-coffee-500'>
                <Loader2 className='w-4 h-4 animate-spin' />
                <span className='text-sm'>正在思考...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 快捷操作 */}
      <div className='px-4 py-2 border-t border-coffee-100 bg-white/50'>
        <div className='flex space-x-2 overflow-x-auto pb-2'>
          {quickActions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => setInput(action.message)}
              className='flex-shrink-0 flex items-center space-x-1 px-3 py-1.5 rounded-full bg-white border border-coffee-200 text-coffee-600 text-sm hover:bg-coffee-50 hover:border-coffee-300 transition-colors'
            >
              <action.icon className='w-4 h-4' />
              <span>{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 输入区域 */}
      <form
        onSubmit={handleSubmit}
        className='p-4 bg-white border-t border-coffee-200'
      >
        <div className='flex items-end space-x-3'>
          <div className='flex-1 relative'>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder='输入消息... (Enter 发送, Shift+Enter 换行)'
              rows={1}
              className='w-full resize-none rounded-xl border border-coffee-200 px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-coffee-500 focus:border-transparent bg-cream-50 placeholder-coffee-400'
              style={{ minHeight: '48px', maxHeight: '120px' }}
            />
          </div>
          <button
            type='submit'
            disabled={!input.trim() || isLoading}
            className='flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-r from-coffee-500 to-coffee-600 text-white flex items-center justify-center hover:from-coffee-600 hover:to-coffee-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl btn-ripple'
          >
            {isLoading ? (
              <Loader2 className='w-5 h-5 animate-spin' />
            ) : (
              <Send className='w-5 h-5' />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
