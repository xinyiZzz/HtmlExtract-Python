#!/usr/bin/python
#-*-coding:utf-8-*-
'''
Name: 线程池
    支持传函数、传参、传回调函数、立即终止所有线程，支持线程的循环利用，节省时间和资源
    
Author：XinYi 609610350@qq.com
Time：2016.5.15
'''
import threading
import Queue
import contextlib
import time

StopEvent = object()


class ThreadPoolSpark(object):


    def __init__(self, max_num):
        self.q = Queue.Queue()
        self.max_num = max_num  # 线程池最大线程数量

        self.terminal = False
        self.generate_list = []
        self.free_list = []

    def run(self, func, args, callback=None):
        """
        线程池执行一个任务
        :param func: 任务函数
        :param args: 任务函数所需参数
        :param callback: 任务执行失败或成功后执行的回调函数，回调函数有两个参数1、任务函数执行状态；2、任务函数返回值（默认为None，即：不执行回调函数）
        :return: 如果线程池已经终止，则返回True否则None
        """
        if len(self.free_list) == 0 and len(self.generate_list) < self.max_num:
            self.generate_thread()
        w = (func, args, callback,)
        self.q.put(w)

    def generate_thread(self):
        """
        创建一个线程
        """
        t = threading.Thread(target=self.call)
        t.start()

    def call(self):
        """
        循环去获取任务函数并执行任务函数
        """
        current_thread = threading.currentThread
        self.generate_list.append(current_thread)
        event = self.q.get()
        while event != StopEvent:
            func, arguments, callback = event
            try:
                result = func(*arguments)
                status = True
            except Exception as e:
                status = False
                result = e
            if callback is not None:
                try:
                    callback(status, result)
                except Exception as e:
                    pass
            self.q.task_done()
            if self.terminal:  # False
                event = StopEvent
            else:
                with self.worker_state(self.free_list, current_thread):
                    event = self.q.get()
        else:
            self.generate_list.remove(current_thread)

    @contextlib.contextmanager
    def worker_state(self, x, v):
        x.append(v)
        try:
            yield
        finally:
            x.remove(v)

    def close(self):
        num = len(self.generate_list)
        while num:
            self.q.put(StopEvent)
            num -= 1

    def terminate(self):
        '''
        终止线程（清空队列）
        '''
        self.terminal = True
        while self.generate_list:
            self.q.put(StopEvent)
        self.q.empty()

    def wait(self):
        '''
        等待所有线程执行完毕后返回
        '''
        self.q.join()
        self.terminate()
        while self.generate_list != []:
            time.sleep(0.1)
        return


if __name__ == '__main__':
    pass
