"""
共享工具函数
"""
import asyncio
import threading
from typing import Coroutine, TypeVar

T = TypeVar('T')


def run_async(coro: Coroutine[None, None, T]) -> T:
    """
    安全地在同步上下文中运行异步函数
    
    Google ADK 的工具函数必须是同步的，但数据库操作是异步的。
    这个函数处理了在已有事件循环中运行异步代码的情况。
    
    Args:
        coro: 要运行的协程
        
    Returns:
        协程的返回值
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 如果已有事件循环在运行，使用新线程
        result = [None]
        exception = [None]
        
        def run():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result[0] = new_loop.run_until_complete(coro)
            except Exception as e:
                exception[0] = e
            finally:
                new_loop.close()
        
        thread = threading.Thread(target=run)
        thread.start()
        thread.join()
        
        if exception[0]:
            raise exception[0]
        return result[0]
    else:
        # 没有事件循环，直接创建新的
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

