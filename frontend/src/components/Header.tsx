import { Coffee } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function Header() {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const formatDate = (date: Date) => {
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    return `${date.getMonth() + 1}月${date.getDate()}日 ${
      weekdays[date.getDay()]
    }`;
  };

  const getGreeting = () => {
    const hour = currentTime.getHours();
    if (hour < 6) return '夜深了 🌙';
    if (hour < 9) return '早上好 🌅';
    if (hour < 12) return '上午好 ☀️';
    if (hour < 14) return '中午好 🍱';
    if (hour < 18) return '下午好 ☕';
    if (hour < 22) return '晚上好 🌆';
    return '夜深了 🌙';
  };

  return (
    <header className='bg-gradient-to-r from-coffee-800 via-coffee-700 to-coffee-800 text-white shadow-lg'>
      <div className='max-w-full mx-auto px-6 py-4'>
        <div className='flex items-center justify-between'>
          {/* Logo 和标题 */}
          <div className='flex items-center space-x-4'>
            <div className='relative'>
              <div className='w-12 h-12 bg-gradient-to-br from-cream-300 to-cream-500 rounded-full flex items-center justify-center shadow-lg'>
                <Coffee className='w-7 h-7 text-coffee-800' />
              </div>
              {/* 蒸汽效果 */}
              <div className='absolute -top-2 left-1/2 transform -translate-x-1/2'>
                <div className='flex space-x-1'>
                  <div
                    className='w-1 h-3 bg-white/40 rounded-full steam'
                    style={{ animationDelay: '0s' }}
                  ></div>
                  <div
                    className='w-1 h-4 bg-white/30 rounded-full steam'
                    style={{ animationDelay: '0.3s' }}
                  ></div>
                  <div
                    className='w-1 h-3 bg-white/40 rounded-full steam'
                    style={{ animationDelay: '0.6s' }}
                  ></div>
                </div>
              </div>
            </div>
            <div>
              <h1 className='text-2xl font-display font-bold tracking-wide'>
                Buy A Coffee
              </h1>
              <p className='text-cream-300 text-sm'>希希咖啡 · 智能点单助手</p>
            </div>
          </div>

          {/* 中间状态指示 */}
          <div className='hidden md:flex items-center space-x-6'>
            <div className='flex items-center space-x-2 bg-white/10 rounded-full px-4 py-2'>
              <div className='w-2 h-2 bg-green-400 rounded-full animate-pulse'></div>
              <span className='text-sm'>AI 助手在线</span>
            </div>
            <div className='flex items-center space-x-2 bg-white/10 rounded-full px-4 py-2'>
              <span className='text-sm'>☕ 咖啡店营业中</span>
            </div>
            <div className='flex items-center space-x-2 bg-white/10 rounded-full px-4 py-2'>
              <span className='text-sm'>🛵 配送服务可用</span>
            </div>
          </div>

          {/* 右侧时间和问候 */}
          <div className='text-right'>
            <div className='text-lg font-medium'>{formatTime(currentTime)}</div>
            <div className='text-cream-300 text-sm flex items-center justify-end space-x-2'>
              <span>{formatDate(currentTime)}</span>
              <span>·</span>
              <span>{getGreeting()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 装饰性底部边框 */}
      <div className='h-1 bg-gradient-to-r from-transparent via-cream-400 to-transparent opacity-30'></div>
    </header>
  );
}
